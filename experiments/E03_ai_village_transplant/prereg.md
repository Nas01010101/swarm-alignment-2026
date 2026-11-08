# E03 — Real communication graphs: AI Village transcripts with planted tampering

Owner: benhoangquan (with coding agent) · Registered: <UTC timestamp of the commit that adds this file, before run.py is executed>

## Question
On the communication graphs of real LLM-agent villages, does witness-free attribution behave as E01
predicts from graph structure, or are real graphs star-like enough to make it uninformative?

## What this experiment is and is not
- **Is:** real *who-talked-to-whom-when* structure and real message content (hashed) from AI Village,
  turned into two-sided per-agent `Logs` (sender `send` + each recipient `recv`), then tampered with
  `swarm.tamper()` exactly as in E01.
- **Is not:** real agents tampering, and not a check that AI Village's own storage is per-agent. Both
  records are built by us from one shared chat log. The report must say so.

## Data
`aidigestorg/ai-village` (Hugging Face, gated). Folders: main-village, game-jam-village, open-chat-village,
saboteur-rpg-village, swarm-village. Tables used: `chat_messages`, `chat_rooms`, `agents`, `villages`.
Human (non-agent) senders are dropped. Schema notes go in the notebook at Step 0, before any statistic is computed.

## Units
One **instance** = one village x one room x one UTC day (agents who are senders that day are the swarm).
Keep instances with >= 4 agents and >= 20 agent messages. At most 40 instances per folder, chosen as the
first 40 qualifying instances in (village_id, room, day) order. No other selection.

## Graph constructions (both run; fixed now)
- **room**: a message from s goes to every other agent who sent at least one message in that room that day.
- **addressed**: a message goes only to agents whose name appears in it (case-insensitive whole-word match
  on the agent's display name). Messages that address no one are dropped. The adapter reads text to build
  the graph; the detector does not (digests only), as in E01/E02.
Each (message, recipient) pair becomes one `send`/`recv` record pair with msg_id `<message_id>><recipient>`.

## Design
Per instance x mode: k in {0, 1, 2, 3} (k <= n // 3), collude in {False, True}, seeds 0-9, tamper rate 0.2,
all three ops (same as E01). Liars: `random.Random(seed).sample(sorted(agents), k)`.
Detectors: `diagnose(max_liars=k+2)` (min-cover) and `diagnose_bounded(t=k)`. Baseline: `naive_count`.
Reference: for each instance, `synthetic_swarm(n, "complete", rounds=8, seed)` with the same k/seeds/rate
(the E01 generator at the instance's n).
Model/LLM: none. $0.

## Hypotheses, metrics and thresholds (fixed now)
Primary unit for intervals = instance (runs inside an instance are not independent): compute the per-instance
mean, then report the mean over instances with a 95% bootstrap CI over instances (2000 resamples, seed 0).
- **H1 (guarantee transfers):** `diagnose_bounded(t=k)` accuses an honest agent in 0 runs, both modes, all k.
  Falsifier: any run > 0. That would be a bug or a broken assumption: stop, debug, report.
- **H2 (room graphs are diagnosable):** room mode, k=1, collusion pooled: min-cover exact rate >= 0.80.
  Falsifier: < 0.60. Between 0.60 and 0.80: "partially supported".
- **H3 (addressing makes graphs sparse and hub-shaped):** addressed-mode k=1 exact rate is lower than
  room-mode by >= 0.15 (on instances present in both modes). Falsifier: difference < 0.05.
- **H4 (structure predicts attribution):** across instances (room + addressed pooled, k=1, min-cover),
  Spearman rho between `min_degree` and per-instance exact rate > 0 with bootstrap CI excluding 0.
  Tested only if >= 15 instances; otherwise reported as "not testable".
- **H5 (framing transfers):** in star-like instances (definition below) at k >= 2, min-cover accuses an
  honest agent in >= 0.5 of runs (E01 star: 0.70-0.75). Tested only if >= 5 star-like instances.

**star-like**: one agent is an endpoint of >= 90% of the distinct agent pairs that exchanged a message.
**Go/no-go falsifier (from the original draft):** if >= 50% of room-mode instances are star-like, write
"the method is uninformative on these real swarms" as the headline E03 result. Still report everything.

## Controls
- Negative: k=0 -> status `clean` in 100% of runs (any other value is a bug).
- Positive: one extra cell, k=1, rate 1.0, 3 seeds per instance -> >= 1 discrepancy in 100% of runs.
- Reference: E01 generator at the same n (see Design), so differences are attributable to real structure.

## Rival explanations to check in the notebook
- Instances are small (n 4-8), so "complete-like" may just be "small". Compare against the same-n reference.
- The room construction assumes every active agent read every message; addressed is the conservative variant.

## Budget
$0 (no LLM). Wall-clock < 30 min. Download: tables only (never the image tars).
