"""In-memory operation journal and bounded SSE replay."""
import asyncio
import json
import threading
from datetime import datetime, timezone
from tools.operation_events import MAX_BYTES, MAX_EVENTS, normalize

class Journal:
    def __init__(self, operation_id, mode="autopilot"):
        self.operation_id = operation_id
        self.mode = mode
        self.guard = threading.Lock()
        self.rows = []
        self.closed = False
        self.offset = 0
        self.degraded = False

    def append(self, kind, **fields):
        with self.guard:
            if self.closed or len(self.rows) >= MAX_EVENTS + 4:
                return
            self.rows.append(dict(schema_version=1, operation_id=self.operation_id,
                mode=self.mode, sequence=len(self.rows)+1,
                observed_at=datetime.now(timezone.utc).isoformat(), kind=kind, **fields))
            if kind == "completed":
                self.closed = True

    def ingest(self, path):
        if self.degraded:
            return
        try:
            with path.open("rb") as f:
                data = f.read(MAX_BYTES+1)
            if len(data)>MAX_BYTES or len(data)<self.offset:
                raise ValueError("Event limit")
            tail = data[self.offset:]
            for line in tail.splitlines(keepends=True):
                if not line.endswith(b"\n"):
                    break
                self.offset += len(line)
                if len(line)>1024:
                    raise ValueError("Event line limit")
                row = normalize(json.loads(line))
                if row is None:
                    raise ValueError("Invalid event")
                self.append(**row)
        except (OSError, ValueError, TypeError, RecursionError):
            self.degraded = True
            self.append("observation_gap")

    def finish(self, status, recovery_required):
        self.append("completed", outcome=status, recovery_required=recovery_required)

    def read(self, cursor):
        with self.guard:
            return list(self.rows[cursor:]), self.closed, len(self.rows)

    async def stream(self, cursor, request):
        idle = 0
        while not await request.is_disconnected():
            rows, closed, count = self.read(cursor)
            for row in rows:
                cursor = row["sequence"]
                yield f"id: {cursor}\ndata: {json.dumps(row,separators=(',',':'))}\n\n"
            if closed and cursor >= count:
                return
            idle += 1
            if idle % 20 == 0:
                yield ": heartbeat\n\n"
            await asyncio.sleep(.5)
