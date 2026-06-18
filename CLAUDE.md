# CLAUDE.md — Trial Voices / CT-Patient-Scraper (`trial-voices`)

> Repo root `CLAUDE.md`. Reconstructed from recovered memory note + replayed source (~2026-06).
> **Read the two-repo split before pushing anything.**

## Purpose
Mine **publicly posted patient clinical-trial experiences** (duration on investigational drug, tolerability, sentiment, AEs) from Reddit/forums and structure them with Claude → SQLite `trial_voices.db`. Location: `~/projects/trial-voices`.

## ⚠️ Two-repo split (deliberate — do not cross the streams)
- 🌐 **PUBLIC** [`trial-voices`](https://github.com/AsthikaG/trial-voices) — clean generic tool, **official-API-only, NO drug/competitor lists**. This is the URL given to **Reddit Data API reviewers**.
- 🔒 **PRIVATE** [`CT-Patient-Scraper`](https://github.com/AsthikaG/CT-Patient-Scraper) — full version incl. PullPush + the drug/competitor taxonomy.
- Local `main` tracks `private`. **Never push targeting logic (PullPush, drug taxonomy) to `origin` (public).** When in doubt, push to the private remote.

## Stack
Python + SQLite. Claude **Haiku Batch API** for extraction. `ANTHROPIC_API_KEY` loaded via `.env` / python-dotenv (real env vars win; key was persisted with `setx` on the old machine — **re-set it on the new machine**). Set `PYTHONUTF8=1`.

## Pipeline (script-based, not a single CLI)
`scrape_pullpush.py` (no-auth historical archive; site-wide full-text search) **and/or** `scrape_reddit.py` (live official Reddit API)
→ `documents` table
→ `tag_all.py` (deterministic alias tagging)
→ `purge_noise.py` (drops finance/news/off-label-HRT/non-onc/junk subs)
→ `extract.py submit` / `extract.py collect` (Haiku Batch, second-order fields)
→ `ctgov.py` + `load_ct.py` (CT.gov cross-ref, ~34 trials)
→ `build_report.py` (8-section analysis → `reports/patient_voices.csv` + `trial_voices_report.md`).
Manual fallback path: `dump_batch.py` → agent extraction → `load_extractions.py`. Prototype non-Reddit sources: `forum_pull.py`, `manual_capture.py`.

## Drug taxonomy
Now lives in shared **`ag-drug-universe`** (`~/projects/shared/ag-drug-universe`, private) — 28 pipeline assets + 44 competitors. `config.py` still keeps a local copy (DRUGS + COMPETITORS). **Tagger prefers pipeline over competitor on co-mention.** Curate short/ambiguous code names carefully — dropped aliases that false-match (`auto1`→gaming/cannabis; `amg 509` space-variant).

## Data-quality ground truth (don't relitigate these)
- Deterministic `matched_*` columns are ground truth; LLM free-text fields drift.
- Caregiver report of a specific patient's real treatment = **valid** patient voice (old prompt wrongly excluded these → +67 on re-run).
- Dexamethasone IS an MM regimen partner (VRd/D-VRd/KRd), not a premed.
- `nct_id` must be NCT-format only (acronyms like GRIFFIN/PERSEUS don't belong there); `line_of_therapy` is a single-value enum.
- QA notes: `docs/qa_findings.md`.

## Empirical reality (corrects a priori assumptions)
- Collection is **site-wide keyword search**, so voices span 25+ subreddits — not subreddit-restricted (`scrape_reddit.py` never actually ran; all data is PullPush so far).
- **r/multiplemyeloma dominates (~70%, 289/413 voices)** — MM has the richest investigational pipeline + most engaged community; it is NOT "smaller/niche." r/leukemia (40, mostly blinatumomab/ALL), r/lymphoma + r/Lymphoma_MD_Answers (20) are next. r/coloncancer ≈ empty (CRC barely on Reddit); r/breastcancer high-volume but few drug-matched. *(A 6-subreddit "utility" table from ChatGPT was a-priori and directionally wrong — trust our data.)*

## Status (2026-06)
- Reddit live-API request submitted via support form (account Wild-Camp5583), **pending**; Reddit app creation blocked by Devvit/Responsible-Builder gate. Until approved, collection = PullPush only (times out heavily; ~3,210 docs captured).
- Dataset: 601 extractions / **413 first-hand patient/caregiver voices** (QA'd twice). AG assets 292 voices (~49% positive) vs competitors 121 (~26%). Durations up to ~7.4y (daratumumab). Top combos dex/dara/lenalidomide/bortezomib; top AE fatigue (38), CRS (12).

## Resume here
1. Re-set `ANTHROPIC_API_KEY` (`setx`) and the `.env` on the new machine.
2. Confirm remotes: `origin` = public trial-voices, private remote = CT-Patient-Scraper; local `main` tracks private. Re-verify before any push.
3. Chase the pending Reddit Data API approval; if granted, wire `scrape_reddit.py` into the pipeline (currently unused).
4. The `trial_voices.db` and pulled docs live only on the dead SSD or must be re-pulled via PullPush.
