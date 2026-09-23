"""Review one stored report using .env, then explicitly apply the reviewed revision.

Dry run performs real model checks and records a before/after diff. Applying an
existing review does not call the LLM again and refuses a changed report snapshot.
"""
import argparse
from collections import Counter
import copy
import datetime
import hashlib
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core import db
from app.core.claim_verifier import verify_claims, supported_claims
from app.core.confidence_policy import CONFIDENCE_POLICY_VERSION
from app.core.config import get_settings
from app.core.evidence_context import EvidenceContext
from app.core.final_audit import finalize_report
from app.core.llm import TOKEN_USAGE


def fingerprint(report):
    return hashlib.sha256(json.dumps(report, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def summary(claims):
    return {'levels': dict(Counter(c.get('confidence') for c in claims)),
            'supported': len(supported_claims(claims)),
            'cross_validated': sum(bool(c.get('cross_validated')) for c in claims),
            'single_authority': sum(c.get('independent_verification', {}).get('status') == 'single_authority' for c in claims)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report-id', required=True)
    parser.add_argument('--review-file', required=True)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    report = db.get_report(args.report_id)
    if not report:
        raise SystemExit('Report not found')
    target = Path(args.review_file)
    if args.apply:
        result = json.loads(target.read_text(encoding='utf-8'))
        if result['report_id'] != args.report_id or result['original_hash'] != fingerprint(report):
            raise SystemExit('Report changed since review; repeat the review before applying')
        replacement = result['reviewed_report']
        task = db._connect().execute('SELECT task_id FROM reports WHERE report_id=?', (args.report_id,)).fetchone()
        db.save_report(replacement, task_id=task['task_id'] or '')
        # Keep the exported copy in sync with the on-screen result.
        from frontend_acceptance import export_report
        export_report(replacement)
        acceptance = Path(__file__).resolve().parents[2] / 'doc/新能源车案例-验收结果.json'
        if acceptance.exists():
            check = json.loads(acceptance.read_text(encoding='utf-8'))
            if check.get('report_id') == args.report_id:
                check.update(verified_claims=result['after']['supported'], confidence_review=replacement['confidence_review'])
                acceptance.write_text(json.dumps(check, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'applied': True, 'report_id': args.report_id, **result['after']}, ensure_ascii=False))
        return
    if not args.live:
        parser.error('--live is required to use model credentials')
    passages = copy.deepcopy(report.get('evidence_selection', []))
    if not passages:
        raise SystemExit('No persisted selection; do not invent original model context')
    for p in passages:
        p['report_snapshot_at'] = report.get('created_at', '')
    before = summary(report['claims'])
    start, tokens = time.monotonic(), TOKEN_USAGE['total']
    print(json.dumps({'before': before, 'report_id': args.report_id}), flush=True)
    reviewed = verify_claims(report['claims'], EvidenceContext(passages, ''), model=get_settings().provider_config.aux_model)
    after = summary(reviewed)
    original_hash = fingerprint(report)
    original = copy.deepcopy(report)
    old_supported = {c['claim_id'] for c in supported_claims(report['claims'])}
    new_supported = {c['claim_id'] for c in supported_claims(reviewed)}
    report['claims'] = reviewed
    by_id = {c['claim_id']: c for c in reviewed}
    for section in report['sections']:
        section['claims'] = [by_id[c['claim_id']] for c in section.get('claims', []) if c['claim_id'] in by_id]
    # A changed support set invalidates the old publication audit, not just badges.
    if old_supported != new_supported:
        report = finalize_report(report, model=get_settings().provider_config.aux_model)
        report['quality_status'] = 'needs_review'
    total = len(reviewed) or 1
    biz = report.setdefault('metrics', {}).setdefault('business', {})
    biz['high_confidence_ratio'] = round(sum(c['confidence'] == 'high' for c in reviewed)/total, 3)
    biz['accuracy'] = biz['high_confidence_ratio']  # legacy alias only
    biz['cross_validated_ratio'] = round(sum(bool(c['cross_validated']) for c in reviewed)/total, 3)
    biz['formula'] = '高可信占比与独立交叉验证占比分开统计；均不是事实准确率'
    report['confidence_review'] = {
        'policy_version': CONFIDENCE_POLICY_VERSION,
        'reviewed_at': datetime.datetime.now().isoformat(timespec='seconds'),
        'before': before, 'after': after, 'support_set_changed': old_supported != new_supported,
        'tokens': TOKEN_USAGE['total'] - tokens, 'elapsed_seconds': round(time.monotonic() - start, 2),
        'note': '重新核验的是已保存的原文快照，没有重新抓取实时价格；历史研究质检状态未自动提升',
    }
    result = {'report_id': args.report_id, 'original_hash': original_hash, 'before': before, 'after': after,
              'reviewed_report': report, 'original_report': original}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report['confidence_review'], ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
