# Project Scope

## Overview
The AI Deal Flow Operating System automatically collects business listings from one source, structures them, scores them with AI, pushes qualified deals into a Notion pipeline, triggers n8n alerts, and makes past deals searchable through Deal Chat.

## problem Statement
Small investment firms waste time manually scanning broker websites, copying listings into spreadsheets, reviewing weak deals, and searching scattered historical notes. This MVP reduces that manual work by automatically sourcing listings, structuring them, generating AI summaries and scores, organizing them in a Notion pipeline, and making prior deal knowledge searchable.

## Pipeline Stages
- *New* — raw ingested deal, not yet enriched
- *Scored* — AI summary and score completed
- *Review* — score or criteria passed; worth human review
- *Watchlist* — not strong enough now, but worth keeping visible
- *Rejected* — clearly outside thesis or too weak

## Tech Stack
- Python for scraper + enrichment + DB scripts
- BeautifulSoup + requests first, Playwright only if site requires JS
- SQLite instead of Postgres for speed
- FastAPI for later API/chat endpoints
- OpenAI API for summary + scoring + embeddings
- Notion API for pipeline UI
- n8n for orchestration and alerts
- ChromaDB for Deal Chat retrieval
- Markdown + GitHub for documentatio

## Features
- Deal scraping
- Data processing
- AI enrichment and scoring
- Database storage
- Notion synchronization
- Chat interface
- API endpoints

---

## Deal Scoring Rubric

Deals are triaged using a deterministic 0-10 scoring system that combines structured data analysis with AI-generated signals. This is **not** an investment recommendation engine—it's a data-driven filter to separate obviously poor deals from candidates worth human review.

### Scoring Components

#### 1. Financial Quality (0-3 points)
Assesses data completeness and profitability signals.

- **3 points**: Revenue AND EBITDA both present with EBITDA > 0 (profitable, complete data)
- **2 points**: Revenue AND EBITDA present, but EBITDA ≤ 0 or margins unclear
- **1 point**: Only revenue present, or EBITDA missing entirely
- **0 points**: Revenue missing or unable to verify profitability

#### 2. Price Attractiveness (0-2 points)
Evaluates purchase multiple relative to cash generation capacity.

- **2 points**: Price-to-EBITDA < 5x OR Price-to-Revenue < 2x (excellent value)
- **1 point**: Price-to-EBITDA 5-10x OR Price-to-Revenue 2-5x (fair value range)
- **0 points**: Price-to-EBITDA > 10x OR Price-to-Revenue > 5x (expensive) OR unable to calculate

#### 3. Recurring Revenue Signal (0-2 points)
AI assessment of revenue stability and predictability.

- **2 points**: Confirmed recurring/subscription model (SaaS, membership, recurring fees)
- **1 point**: Mixed revenue model (some recurring, some transactional)
- **0 points**: Transactional or one-time revenue model (services, project work)

#### 4. Risk Level (0-2 points)
Fewer identified risks = higher points.

- **2 points**: No significant risks identified by AI analysis
- **1 point**: 1-2 moderate risks (e.g., customer concentration, regulatory changes, market trends)
- **0 points**: 3+ risks identified OR presence of critical risk (legal issues, key person risk, technical debt)

#### 5. Growth Potential (0-1 point)
AI assessment of upside trajectory.

- **1 point**: Strong growth signals (expanding addressable market, new growth channels, improving margins)
- **0 points**: Flat or declining trajectory

### Score Calculation

```
Deal Score = Financial Quality + Price Attractiveness + Recurring Revenue + Risk Level + Growth Potential
Range: 0-10
```

### Pipeline Stage Assignment

Based on triage score:

| Score | Pipeline Stage | Action | Next Step |
|-------|--------|--------|----------|
| ≥ 7.5 | **Review** | Passed initial filters | Schedule human review in Notion |
| 6.0 - 7.4 | **Watchlist** | Interesting but incomplete data | Monitor for updates; revisit if metrics improve |
| < 6.0 | **Rejected** | Below minimum threshold | Archive; revisit only if fundamentals change |

### Scoring Philosophy

- **Deterministic**: No black-box ML; every point is explainable
- **Conservative**: Favors data completeness over speculation
- **Multiple-aware**: Emphasizes valuation discipline (5-10x EBITDA sweet spot aligns with M&A norms)
- **Recurring-biased**: Subscription revenue signals lower operational risk
- **Risk-forward**: Penalizes deals with multiple unknowns

## Architecture v1
*Broker website → Python scraper → cleaning/normalization → SQLite deals DB → AI enrichment layer (summary, risks, score) → Notion pipeline sync → n8n workflow for scheduled runs/alerts → ChromaDB vector index → Deal Chat via FastAPI/CLI*

## Repo structure
ai-deal-flow-os/
├── README.md
├── .env.example
├── requirements.txt
├── app/
│   ├── scraper/
│   │   └── broker_scraper.py
│   ├── processing/
│   │   ├── clean_deals.py
│   │   └── dedupe.py
│   ├── ai/
│   │   ├── prompts.py
│   │   ├── enrich_deals.py
│   │   └── scoring.py
│   ├── db/
│   │   ├── models.py
│   │   ├── init_db.py
│   │   └── ingest.py
│   ├── notion/
│   │   └── sync_notion.py
│   ├── automation/
│   │   └── workflow_notes.md
│   ├── chat/
│   │   ├── build_index.py
│   │   └── query_chat.py
│   └── api/
│       └── main.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── ai_deals.db
├── docs/
│   ├── scope.md
│   ├── architecture.md
│   ├── daily-notes.md
│   └── demo-script.md
└── screenshots/

## Boundaries
- Define what is in and out of scope