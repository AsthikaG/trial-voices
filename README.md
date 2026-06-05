# trial-voices

Identify and analyze **publicly posted** patient clinical-trial experiences and
structure them for aggregate research — drug name, trial phase, **duration on
investigational drug**, sentiment, and adverse events.

> **Scope & ethics.** Read-only. Uses the official Reddit Data API (OAuth, `script`
> type, well under 100 queries/min). Does not post, comment, vote, message users,
> or moderate. Output is aggregate and de-identified — usernames are not retained in
> analysis. Built for non-commercial biomedical research; raw Reddit content is not
> republished.

## Pipeline

```
scrape_reddit.py  →  documents table (resume-safe, keyword pre-filtered)
extract.py submit →  Claude Batch API (Haiku, tool-forced extraction)
extract.py collect→  extractions table
report.py         →  stats / duration distribution
```

## Setup

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set env vars (Reddit app: https://www.reddit.com/prefs/apps → "script" type):

```powershell
$env:REDDIT_CLIENT_ID     = "..."
$env:REDDIT_CLIENT_SECRET = "..."
$env:REDDIT_USER_AGENT    = "trial-voices/0.1 by u/yourname"
$env:ANTHROPIC_API_KEY    = "sk-ant-..."
```

## Run

```powershell
python scrape_reddit.py            # all subreddits in config.py
python extract.py submit           # send pending docs to Batch API
python extract.py collect          # ~minutes later: pull results
python report.py                   # summary
python report.py duration          # duration-on-drug distribution
```

## Extending beyond Reddit

`documents` is source-agnostic (keyed by a string id). Add an `scrape_inspire.py`
(Playwright) or another public-data puller that upserts rows the same way, and
`extract.py` will pick them up unchanged. Always respect each source's terms of
service and robots policy.

## Notes
- Pre-filter (`RELEVANCE_KEYWORDS`) gates docs before spending tokens.
- `is_patient_voice` flag separates real first-hand accounts from news/caregivers —
  filter on it for analysis.
- Re-running any step is safe; work is keyed by document id.
