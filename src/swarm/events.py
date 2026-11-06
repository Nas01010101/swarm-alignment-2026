"""Per-agent event logs.

Every inter-agent message leaves two records: a `send` in the sender's log and a
`recv` in the receiver's log, both carrying the same msg_id and content digest.
That redundancy is the whole point: an agent can rewrite its own log, but not
its peers', so a tampered record disagrees with its counterpart.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

Logs = dict[str, list["Event"]]


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


@dataclass(frozen=True)
class Event:
    agent: str  # whose log this record lives in
    t: int  # round index
    kind: str  # "send" | "recv"
    peer: str  # the other endpoint
    msg_id: str
    digest: str
    text: str = ""  # optional; detectors must not depend on it

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)


def dump_logs(logs: Logs, path: str) -> None:
    with open(path, "w") as f:
        for agent in sorted(logs):
            for ev in logs[agent]:
                f.write(ev.to_json() + "\n")


def load_logs(path: str) -> Logs:
    logs: Logs = {}
    with open(path) as f:
        for line in f:
            ev = Event(**json.loads(line))
            logs.setdefault(ev.agent, []).append(ev)
    return logs
