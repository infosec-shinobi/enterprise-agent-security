import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from dashboard.backend.main import app
from dashboard.backend.runs import Manager
from dashboard.backend.events import Journal
from tools.operation_events import Emitter, MAX_BYTES, MAX_EVENTS, normalize

class EventTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"events.jsonl"
        self.path.touch()
        self.j=Journal("test")

    def test_order_and_replay(self):
        self.j.append("accepted")
        Emitter(self.path).emit("provisioning")
        self.j.ingest(self.path)
        self.j.ingest(self.path)
        self.j.finish("error",True)
        rows,closed,count=self.j.read(1)
        self.assertEqual([r["sequence"] for r in rows],[2,3])
        self.assertTrue(closed)
        self.assertEqual(count,3)

    def test_partial_line(self):
        self.path.write_bytes(b'{"kind":"provision')
        self.j.ingest(self.path)
        self.assertEqual(self.j.read(0)[2],0)
        with self.path.open("ab") as f:
            f.write(b'ing"}\n')
        self.j.ingest(self.path)
        self.assertEqual(self.j.read(0)[2],1)

    def test_reject_secret_fields(self):
        self.path.write_text('{"kind":"provisioning","token":"secret-marker"}\n')
        self.j.ingest(self.path)
        self.assertEqual(self.j.read(0)[0][0]["kind"],"observation_gap")
        self.assertNotIn("secret-marker",str(self.j.read(0)))

    def test_oversize(self):
        self.path.write_bytes(b"x"*(MAX_BYTES+1))
        self.j.ingest(self.path)
        self.assertTrue(self.j.degraded)

    def test_emitter_bound(self):
        e=Emitter(self.path)
        for _ in range(MAX_EVENTS+10):
            e.emit("provisioning")
        self.assertEqual(len(self.path.read_bytes().splitlines()),MAX_EVENTS)

    def test_assertion_validation(self):
        row=dict(kind="assertion",scenario="active-read",outcome="pass",expected=200,actual=200)
        self.assertEqual(normalize(row),row)
        self.assertIsNone(normalize(dict(row,actual=True)))
        self.assertIsNone(normalize(dict(row,scenario="secret-marker")))

    def test_sse_replay_and_rejection(self):
        m=Manager(Path(self.tmp.name))
        m.journal=self.j
        self.j.append("accepted")
        self.j.finish("error",True)
        with patch("dashboard.backend.runs.manager",m), TestClient(app) as c:
            url="/api/v1/runs/test/events"
            response=c.get(url,headers={"Last-Event-ID":"1"})
            self.assertEqual(response.status_code,200)
            self.assertIn("id: 2",response.text)
            self.assertNotIn("id: 1",response.text)
            self.assertIn('"kind":"completed"',response.text)
            self.assertEqual(c.get(url,headers={"Last-Event-ID":"99"}).status_code,400)
            self.assertEqual(c.get(url,headers={"Origin":"https://example.invalid"}).status_code,403)
            self.assertEqual(c.get("/api/v1/runs/unknown/events").status_code,404)
            for _ in range(8):
                self.assertTrue(m.stream_slots.acquire(False))
            self.assertEqual(c.get(url).status_code,429)
            for _ in range(8):
                m.stream_slots.release()
