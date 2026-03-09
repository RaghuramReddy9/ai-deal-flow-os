# Daily Notes

## Date: 03/09/2026
- Designed the architecture
- Defined the deal record schema

---

## Deal Record Schema

The deal record is the core data structure flowing through scraping, AI enrichment, and Notion sync. This schema starts minimal but covers all three stages of the pipeline.

### Base Fields (From Scraper)
These fields are extracted directly by the scraper:
- **id** - Unique identifier for the deal
- **deal_name** - Title/name of the business for sale
- **location** - Geographic location
- **asking_price** - Listed asking price
- **revenue** - Annual revenue
- **ebitda** - Earnings before interest, taxes, depreciation, amortization
- **description** - Full deal description
- **source_url** - Direct link to the deal listing
- **source_name** - Which broker/platform (e.g., "BizBuySell", "Flippa")

### AI-Generated Fields (From Enrichment)
The AI layer processes raw data and generates these:
- **summary** - Concise 1-2 sentence business summary
- **industry** - Categorized industry classification
- **score** - Overall deal attractiveness score (0-100)
- **risks** - Key risk flags identified by AI
- **stage** - Business stage (early, growth, mature, declining)
- **recurring_revenue_signal** - Indicator if revenue is recurring/subscription-based
- **growth_potential** - Assessment of growth trajectory

### Notion Sync Fields
Fields aligned with existing Notion database schema:
- Deal Name → **deal_name**
- Industry → **industry**
- Location → **location**
- Revenue → **revenue**
- EBITDA → **ebitda**
- Asking Price → **asking_price**
- Summary → **summary**
- Score → **score**
- Risks → **risks**
- Stage → **stage**
- Source URL → **source_url**

### Internal Operations Fields
Not for display, but critical for data quality:
- **raw_price_text** - Original price text (for cleaning/parsing)
- **raw_revenue_text** - Original revenue text (handles variations)
- **raw_ebitda_text** - Original EBITDA text (handles variations)
- **dedupe_hash** - Hash for detecting duplicate deals
- **scraped_at** - When the deal was scraped
- **created_at** - When the record was created in our system
- **updated_at** - Last update timestamp

### Why These Fields
1. **Scraper stage** needs title, location, financials, and source URL to capture deal basics
2. **AI enrichment** generates summary, industry, score to make deals comparable
3. **Notion sync** matches these fields to the existing database structure
4. **Operations fields** prevent messy deduplication, cleaning, and data quality issues

---

## What Determines the Deal Score

**Core Principle**: Build a simple triage score, not a fake "investment genius" model. Combine structured LLM output with deterministic scoring logic.

### Scoring Components (Out of 10)

#### Financial Quality — 0 to 3 points
Based on whether revenue and EBITDA are present and whether the business appears profitable.
- **3 pts**: Revenue and EBITDA both present, profitable (EBITDA > 0)
- **2 pts**: Revenue and EBITDA present, margins unclear or weak
- **1 pt**: Only revenue present, or EBITDA missing
- **0 pts**: Revenue missing or unable to determine profitability

#### Price Attractiveness — 0 to 2 points
Better if asking price looks reasonable relative to EBITDA or revenue. Lower multiples are more attractive.
- **2 pts**: Price-to-EBITDA < 5x OR Price-to-Revenue < 2x (excellent value)
- **1 pt**: Price-to-EBITDA 5-10x OR Price-to-Revenue 2-5x (fair value)
- **0 pts**: Price-to-EBITDA > 10x OR Price-to-Revenue > 5x (expensive) or unable to calculate

#### Recurring Revenue Signal — 0 to 2 points
AI identifies if revenue is recurring/subscription-based (stable vs. transactional).
- **2 pts**: Confirmed recurring/subscription model
- **1 pt**: Mixed or unclear revenue model
- **0 pts**: Transactional or one-time revenue model

#### Risk Level — 0 to 2 points
Fewer risk flags identified by AI = higher score.
- **2 pts**: No significant risks identified
- **1 pt**: 1-2 moderate risks (e.g., customer concentration, market trends)
- **0 pts**: 3+ risks or 1+ critical risk (e.g., legal issues, key person dependency)

#### Growth Potential — 0 to 1 point
AI assessment of growth trajectory and upside.
- **1 pt**: Strong growth signals identified (expanding market, new channels, etc.)
- **0 pts**: Flat or declining growth potential

### Score Formula
```
score = financial_quality + price_attractiveness + recurring_revenue_signal + risk_adjustment + growth_potential
```
**Range**: 0-10

### Pipeline Stage Logic

Based on the triage score:

| Score Range | Stage | Action |
|---|---|---|
| **>= 7.5** | **Review** | Passed initial filters, ready for deeper analysis |
| **6.0 - 7.4** | **Watchlist** | Interesting but needs monitoring or better data |
| **< 6.0** | **Rejected** | Does not meet minimum attractiveness threshold |

This aligns with the full pipeline: **New** → **Scored** → **Review/Rejected/Watchlist** → **Notion Sync**