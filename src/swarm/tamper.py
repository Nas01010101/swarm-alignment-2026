"""Plant tampering in per-agent logs. Liars may only rewrite their OWN logs.

Ops (per tampered record):
  delete - drop a send/recv (hiding a message)
  edit   - change the digest (claiming different content)
  forge  - add a send that never happened (fabricated work / alibi)

collude=True: when both endpoints of a message are liars, they rewrite it
consistently on both sides. That case is invisible to pairwise checks by
construction; experiments must report it as a stated blind spot, not hide it.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace

from .events import Event, Logs, digest

OPS = ("delete", "edit", "forge")


@dataclass
class Truth:
    liars: set[str]
    tampered: list[tuple[str, str, str]]  # (agent, op, msg_id)


def tamper(logs: Logs, liars: set[str], rate: float, seed: int,
           ops: tuple[str, ...] = OPS, collude: bool = False) -> tuple[Logs, Truth]:
    rng = random.Random(seed)
    out: Logs = {a: list(evs) for a, evs in logs.items()}
    truth = Truth(set(liars), [])
    for liar in sorted(liars):
        new: list[Event] = []
        for ev in out[liar]:
            if rng.random() >= rate:
                new.append(ev)
                continue
            op = rng.choice(ops)
            truth.tampered.append((liar, op, ev.msg_id))
            if op == "delete":
                if collude and ev.peer in liars:
                    _mirror(out, ev, op, None)
                continue
            if op == "edit":
                new.append(replace(ev, digest=digest(f"edited {ev.msg_id} {seed}"), text="[edited]"))
            else:  # forge: keep the real record, add a fake send
                new.append(ev)
                fake = f"forged-{liar}-{len(truth.tampered)}"
                new.append(Event(liar, ev.t, "send", ev.peer, fake, digest(fake), "[forged]"))
            if collude and ev.peer in liars:
                _mirror(out, ev, op, new[-1])
        out[liar] = new
    return out, truth


def _mirror(out: Logs, ev: Event, op: str, changed: Event | None) -> None:
    """Accomplice rewrites its counterpart record to match."""
    peer_log = out[ev.peer]
    idx = [i for i, e in enumerate(peer_log) if e.msg_id == ev.msg_id]
    if op == "delete":
        for i in reversed(idx):
            peer_log.pop(i)
    elif op == "edit" and changed is not None:
        for i in idx:
            peer_log[i] = replace(peer_log[i], digest=changed.digest, text=changed.text)
    elif op == "forge" and changed is not None:
        flip = "recv" if changed.kind == "send" else "send"
        peer_log.append(replace(changed, agent=ev.peer, kind=flip, peer=ev.agent))
