"""Extract structured trial-experience data from scraped docs via Claude Batch API.

Two-phase, resume-safe:
  python extract.py submit    # send all pending docs as one batch, save batch id
  python extract.py collect   # poll batch, write extractions, mark docs done

Batch API = 50% cheaper, async, ideal for backfill volumes.
"""
import json
import os
import re
import sys
import time

import anthropic

import config
import db

BATCH_FILE = os.path.join(os.path.dirname(__file__), ".batch_id")

TOOL = {
    "name": "record_trial_experience",
    "description": "Record structured data about a patient's clinical-trial experience.",
    "input_schema": {
        "type": "object",
        "properties": {
            "is_patient_voice": {"type": "boolean",
                "description": "True only if the author describes their OWN first-hand trial experience (not news, not a caregiver speculating)."},
            "drug_name": {"type": "string"},
            "condition": {"type": "string"},
            "trial_phase": {"type": "string", "description": "e.g. 'Phase 1', 'Phase 2', or '' if unknown"},
            "duration_on_drug": {"type": "string", "description": "Time on the investigational drug, as stated, e.g. '8 months'. '' if not mentioned."},
            "duration_days": {"type": ["integer", "null"], "description": "Normalized duration in days, or null if unknown."},
            "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative", "mixed", "unknown"]},
            "adverse_events": {"type": "array", "items": {"type": "string"}},
            "summary": {"type": "string", "description": "One-sentence summary of their experience."},
        },
        "required": ["is_patient_voice", "sentiment", "summary"],
    },
}

SYSTEM = (
    "You analyze online forum posts from patients about clinical trials. "
    "Extract only what is explicitly stated. Do not infer a drug name or duration "
    "that isn't there. Use the record_trial_experience tool."
)


def pending_docs(conn, limit=None):
    q = "SELECT id, title, body FROM documents WHERE extracted=0"
    if limit:
        q += f" LIMIT {int(limit)}"
    return conn.execute(q).fetchall()


def submit():
    conn = db.connect()
    docs = pending_docs(conn)
    if not docs:
        print("No pending docs.")
        return
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    requests = []
    for d in docs:
        text = f"{d['title'] or ''}\n\n{d['body']}".strip()[:6000]
        requests.append({
            "custom_id": d["id"].replace("_", "-"),  # batch ids: alnum/_/- ; reddit uses _
            "params": {
                "model": config.EXTRACT_MODEL,
                "max_tokens": 1024,
                "system": SYSTEM,
                "tools": [TOOL],
                "tool_choice": {"type": "tool", "name": "record_trial_experience"},
                "messages": [{"role": "user", "content": text}],
            },
        })
    batch = client.messages.batches.create(requests=requests)
    with open(BATCH_FILE, "w") as f:
        f.write(batch.id)
    print(f"Submitted batch {batch.id} with {len(requests)} requests.")
    print("Run `python extract.py collect` in a few minutes.")


def collect():
    if not os.path.exists(BATCH_FILE):
        sys.exit("No .batch_id — run `submit` first.")
    batch_id = open(BATCH_FILE).read().strip()
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    b = client.messages.batches.retrieve(batch_id)
    print(f"Batch {batch_id}: {b.processing_status}  counts={b.request_counts}")
    if b.processing_status != "ended":
        print("Not ready yet. Try again later.")
        return

    conn = db.connect()
    n = 0
    for res in client.messages.batches.results(batch_id):
        doc_id = res.custom_id.replace("-", "_", 2)  # restore t1_/t3_ prefix
        if res.result.type != "succeeded":
            conn.execute("UPDATE documents SET extracted=-1 WHERE id=?", (doc_id,))
            continue
        data = None
        for block in res.result.message.content:
            if block.type == "tool_use":
                data = block.input
        if not data:
            conn.execute("UPDATE documents SET extracted=-1 WHERE id=?", (doc_id,))
            continue
        conn.execute(
            """INSERT OR REPLACE INTO extractions
               (doc_id, is_patient_voice, drug_name, condition, trial_phase,
                duration_on_drug, duration_days, sentiment, adverse_events,
                summary, raw_json, extracted_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (doc_id, int(data.get("is_patient_voice", False)),
             data.get("drug_name", ""), data.get("condition", ""),
             data.get("trial_phase", ""), data.get("duration_on_drug", ""),
             data.get("duration_days"), data.get("sentiment", "unknown"),
             json.dumps(data.get("adverse_events", [])),
             data.get("summary", ""), json.dumps(data), time.time()),
        )
        conn.execute("UPDATE documents SET extracted=1 WHERE id=?", (doc_id,))
        n += 1
    conn.commit()
    conn.close()
    print(f"Collected {n} extractions.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "submit":
        submit()
    elif cmd == "collect":
        collect()
    else:
        print(__doc__)
