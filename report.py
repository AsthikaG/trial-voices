"""Quick analysis of extracted patient-voice data.

    python report.py            # summary stats
    python report.py duration   # duration-on-drug distribution
"""
import sys
import db


def summary():
    conn = db.connect()
    docs = conn.execute("SELECT COUNT(*) c FROM documents").fetchone()["c"]
    done = conn.execute("SELECT COUNT(*) c FROM documents WHERE extracted=1").fetchone()["c"]
    voices = conn.execute("SELECT COUNT(*) c FROM extractions WHERE is_patient_voice=1").fetchone()["c"]
    print(f"Docs scraped: {docs}  |  extracted: {done}  |  first-hand patient voices: {voices}")
    print("\nSentiment (patient voices):")
    for r in conn.execute("SELECT sentiment, COUNT(*) c FROM extractions WHERE is_patient_voice=1 GROUP BY sentiment ORDER BY c DESC"):
        print(f"  {r['sentiment']:>10}: {r['c']}")
    print("\nTop drugs mentioned:")
    for r in conn.execute("SELECT drug_name, COUNT(*) c FROM extractions WHERE is_patient_voice=1 AND drug_name!='' GROUP BY drug_name ORDER BY c DESC LIMIT 15"):
        print(f"  {r['c']:>3}  {r['drug_name']}")


def duration():
    conn = db.connect()
    rows = conn.execute("SELECT duration_days FROM extractions WHERE is_patient_voice=1 AND duration_days IS NOT NULL ORDER BY duration_days").fetchall()
    vals = [r["duration_days"] for r in rows]
    if not vals:
        print("No normalized durations yet.")
        return
    print(f"n={len(vals)}  min={min(vals)}d  median={vals[len(vals)//2]}d  max={max(vals)}d")
    print("\nWith stated text:")
    for r in conn.execute("SELECT duration_on_drug, drug_name, summary FROM extractions WHERE is_patient_voice=1 AND duration_on_drug!='' ORDER BY duration_days DESC NULLS LAST LIMIT 25"):
        print(f"  {r['duration_on_drug']:>14} | {r['drug_name'] or '?':<20} | {r['summary'][:70]}")


if __name__ == "__main__":
    (duration if sys.argv[1:2] == ["duration"] else summary)()
