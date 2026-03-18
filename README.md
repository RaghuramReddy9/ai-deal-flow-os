# AI Deal Flow OS

AI Deal Flow OS is a lightweight internal pipeline for sourcing, enriching, scoring, and triaging acquisition opportunities.

It scrapes broker listings, stores them in SQLite, enriches them with AI, scores and labels them, and syncs qualified deals into a Notion pipeline. The system is designed to be rerunnable and automation-friendly, with n8n as the next orchestration layer.

## What It Does

- Scrapes fresh business listings from Flippa across multiple search pages
- Deduplicates deals by `source_url`
- Stores raw and enriched deal records in SQLite
- Enriches only new or unprocessed deals with AI-generated summary, risks, and scoring
- Syncs only qualified unsynced deals into Notion by default
- Supports a separate refresh mode for updating already-synced Notion pages
- Runs end-to-end from a single command

## End-to-End Flow

```text
Flippa -> SQLite -> AI Enrichment -> Scoring -> Notion -> n8n
```

Default pipeline behavior:

1. Scrape fresh deals
2. Store only new records in SQLite
3. Enrich only unenriched or failed deals
4. Score and label them
5. Sync only newly eligible unsynced deals to Notion

Manual refresh mode:

1. Load already-synced qualified deals
2. Update their existing Notion pages when needed

## How To Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file from `.env.example` and add the required credentials:

```env
OPENROUTER_API_KEY=...
NOTION_API_KEY=...
NOTION_DATABASE_ID=...
```

### 3. Initialize the database

```bash
python -m app.db.init_db
```

### 4. Run the full pipeline

```bash
python -m app.run_pipeline
```

Optional CLI controls:

```bash
python -m app.run_pipeline --scrape-limit 15 --enrich-limit 15 --sync-limit 15
```

To refresh already-synced or previously processed records:

```bash
python -m app.run_pipeline --refresh-existing
```

## Design Decisions

### Why SQLite?

SQLite is enough for an MVP internal tool:

- simple setup
- easy local development
- good fit for idempotent batch workflows
- no deployment overhead during prototyping

### Why Notion?

Notion acts as the lightweight deal pipeline UI:

- easy for non-technical users
- fast to inspect qualified deals
- good enough for internal review workflows

### Why n8n?

n8n turns the project from a script into an operating workflow:

- manual, scheduled, and webhook-based runs
- easier orchestration and monitoring
- practical automation layer without heavy backend infrastructure

### Why AI enrichment instead of rules only?

Rules are good for deterministic filters, but deal writeups are messy and inconsistent. AI helps summarize noisy listings and surface risk signals faster, while deterministic filters still keep the process grounded.

## Reliability Characteristics

- Idempotent and rerunnable
- No duplicate deals from repeated runs
- Enrichment only processes new or unprocessed records
- Notion sync handles existing, missing, and archived pages
- Workflow can be triggered in the background through webhook

## Current Scope

This project intentionally focuses on one strong MVP:

- one broker source
- one structured deal pipeline
- one automation layer
- one clear internal workflow

It does not try to solve:

- full production auth
- multi-agent orchestration
- enterprise deployment
- large-scale infrastructure

## Project Structure

```text
ai-deal-flow-os/
├── README.md
├── requirements.txt
├── .env.example
├── app/
│   ├── ai/
│   ├── api/
│   ├── db/
│   ├── notion/
│   ├── scraper/
│   └── run_pipeline.py
├── docs/
└── tests/
```

## Future Improvements

- Multi-source scraping
- Better scoring calibration using partner feedback
- Alerting to Slack or email
- RAG / Deal Chat over historical deals
- Source-level conversion analytics
- Operator and deal matching

## Author

- Name: Raghuramreddy Thirumalareddy
- LinkedIn: https://www.linkedin.com/in/raghuram-genai/