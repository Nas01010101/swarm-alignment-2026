# E03 — Real logs: AI Village transcripts with planted tampering

Owner: _TBD_ · Registered: _not yet_

## Question
Does the redundancy assumption hold in real multi-agent logs, and how diagnosable are real communication graphs?

## Step 0 (go/no-go, Sat 12:00 ET)
`scripts/fetch_ai_village.py --inspect` → document the schema in the notebook. Needed: who sent each message
and which agents saw it. If each agent's view is not separable, use "two independent records of the same
message" any other way the data offers (e.g. a message quoted by several agents) and say so.

## Design (draft)
Build `Logs` from the transcripts; compute the empirical communication graph and its min degree;
plant tampering with `tamper()`; report exact / false accusations vs. the E01 curve for the same graph statistics.

## Falsifier
Real graphs are star-like (one hub sees everything): the method is uninformative on real swarms. Still report it.
