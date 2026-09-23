"""Run the fixed 36-case semantic benchmark with .env keys (explicit --live)."""
import argparse
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.evidence_context import EvidenceContext
from app.core.claim_verifier import verify_claims
from app.core.config import get_settings
from app.core.llm import TOKEN_USAGE

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if not args.live:
        parser.error('Use --live to allow paid model calls')
    cases = json.loads((Path(__file__).parent / 'fixtures/claim_quality_36.json').read_text(encoding='utf-8'))['cases']
    claims, passages = [], []
    for case in cases:
        eid = 'e_' + case['id']
        # Two mirror URLs per claim deliberately test fake cross-validation.
        refs = [eid, eid + '_mirror']
        claims.append({'claim_id': case['id'], 'text': case['claim'], 'field': case['field'], 'evidence_ids': refs})
        for index, ref in enumerate(refs):
            passages.append({'evidence_id': ref, 'brand': 'Fixture', 'source_url': f'https://fixture{index}.example/' + case['id'],
                             'title': 'Synthetic source fixture', 'text': case['evidence'], 'start': 0, 'end': len(case['evidence']),
                             'source_tier': 'official', 'fetch_kind': 'body', 'source_group': 'same_fixture_original'})
    context = EvidenceContext(passages, '')
    start, tokens = time.monotonic(), TOKEN_USAGE['total']
    results = []
    for i in range(0, len(claims), 4):
        results += verify_claims(claims[i:i+4], context, model=get_settings().provider_config.aux_model)
        print(f'checked {len(results)}/{len(cases)}', flush=True)
    bad = [(c, r) for c, r in zip(cases, results) if c['expected'] != 'supported']
    good = [(c, r) for c, r in zip(cases, results) if c['expected'] == 'supported']
    unsupported = [(c, r) for c, r in zip(cases, results) if c['expected'] == 'insufficient']
    metrics = {'cases': len(cases), 'false_claim_release_rate': sum(r['verification']['verdict'] == 'supported' for c,r in bad)/len(bad),
               'supported_recall': sum(r['verification']['verdict'] == 'supported' for c,r in good)/len(good),
               'unsupported_rejection_rate': sum(r['verification']['verdict'] != 'supported' for c,r in unsupported)/len(unsupported),
               'false_cross_validation_rate': sum(r['cross_validated'] for r in results)/len(results),
               'elapsed_seconds': round(time.monotonic()-start, 2), 'tokens': TOKEN_USAGE['total']-tokens,
               'model': get_settings().provider_config.aux_model,
               'note': 'Synthetic held-fixed claims, not an estimate of real-web accuracy. Primary source rate is measured on the acceptance report, not these fixtures.'}
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({'metrics': metrics, 'results': [{'id':c['id'],'expected':c['expected'],**r['verification']} for c,r in zip(cases,results)]},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(metrics, ensure_ascii=False), flush=True)
    return 0 if metrics['false_claim_release_rate'] == 0 and metrics['supported_recall'] >= 0.8 else 1

if __name__ == '__main__':
    raise SystemExit(main())
