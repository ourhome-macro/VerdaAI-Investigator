import asyncio
import sqlite3
import unittest
from unittest.mock import patch
from app.core import db, task_runtime as rt


class RuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.conn = sqlite3.connect(':memory:', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        db._init_schema(self.conn)
        self.patcher = patch.object(db, '_connect', return_value=self.conn)
        self.patcher.start()
        db.save_task('task', 'fixture', {})

    async def asyncTearDown(self):
        for worker in list(rt._workers.values()):
            worker.cancel()
            try:
                await worker
            except asyncio.CancelledError:
                pass
        self.patcher.stop()
        self.conn.close()

    async def test_disconnect_does_not_cancel_worker_and_events_replay(self):
        reached, finish = asyncio.Event(), asyncio.Event()
        calls = []
        async def pipeline(task_id, sub_id=''):
            calls.append(task_id)
            yield {'type': 'progress', 'data': {'percent': 10}}
            reached.set()
            await finish.wait()
            db.mark_task_done(task_id, 'r-fixture')
            yield {'type': 'done', 'data': {'reportId': 'r-fixture'}}
        await rt.start('task', None, None, pipeline)
        await reached.wait()
        class Request:
            async def is_disconnected(self):
                return True
        self.assertEqual([x async for x in rt.observe('task', Request())], [])
        self.assertEqual(rt.state('task')['status'], 'running')
        await rt.start('task', None, None, pipeline)
        self.assertEqual(calls, ['task'])
        finish.set()
        await rt._workers['task']
        self.assertEqual(rt.events('task', 1)[0]['type'], 'done')
        self.assertEqual(rt.state('task')['status'], 'done')
        saved = self.conn.execute("SELECT status,data FROM research_run_metrics WHERE task_id='task'").fetchone()
        self.assertEqual(saved["status"], "done")
        self.assertIn("stage_seconds", saved["data"])

    async def test_expired_lease_requires_explicit_retry_and_filters_old_attempt(self):
        rt.init()
        self.conn.execute("INSERT INTO research_runs VALUES('task',NULL,1,'running',0,0)")
        self.conn.commit()
        rt.append_event('task', 1, {'type':'error','data':{'message':'old'}})
        self.assertEqual(rt.state('task')['status'], 'interrupted')
        async def pipeline(task_id, sub_id=''):
            yield {'type':'done','data':{'reportId':'new'}}
        await rt.start('task', None, None, pipeline)
        self.assertEqual(rt.state('task')['attempt'], 1)
        await rt.start('task', None, None, pipeline, retry=True)
        await rt._workers['task']
        self.assertEqual(rt.state('task')['attempt'], 2)
        self.assertEqual([e['type'] for e in rt.events('task')], ['done'])

    async def test_retry_recovers_source_documents_but_does_not_reuse_old_claims(self):
        from app.core.models import Evidence
        rt.init()
        self.conn.execute("INSERT INTO research_runs VALUES('task',NULL,2,'running',9999999999,0)")
        self.conn.commit()
        ev = Evidence('e1', 'https://www.tesla.cn/model3', 'official', 'Model 3', 'price', '', 80, 'test',
                      brand='特斯拉', full_text='Model 3 official price details')
        rt.append_event('task', 1, {'type': 'evidence', 'data': ev.to_dict()})
        rt.append_event('task', 1, {'type': 'message', 'data': {'kind': 'claim', 'claim': {'text': 'old unchecked'}}})
        restored = rt.collection_checkpoint('task')
        self.assertEqual(len(restored), 1)
        self.assertEqual(restored[0].full_text, ev.full_text)
        ev.evidence_id = 'e2'
        ev.research_dimensions = ['architecture']
        rt.append_event('task', 1, {'type': 'evidence', 'data': ev.to_dict()})
        self.assertEqual(len(rt.collection_checkpoint('task')), 2)


if __name__ == '__main__':
    unittest.main()
