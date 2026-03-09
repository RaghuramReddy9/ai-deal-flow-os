# Architecture

Documentation for the AI Deal Flow OS architecture.

---

## SQLite Database Schema

The core data layer uses a single `deals` table optimized for the scraping → enrichment → sync pipeline.

### Deals Table

| Column | Type | Constraints | Purpose |
|--------|------|-----------|----------|
| **id** | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique internal deal identifier |
| **deal_name** | TEXT | NOT NULL | Business name/deal title from scraper |
| **location** | TEXT | | Geographic location (city, state, country) |
| **asking_price** | REAL | | Listed asking price in dollars |
| **revenue** | REAL | | Annual revenue from most recent data |
| **ebitda** | REAL | | EBITDA (earnings before interest, taxes, depreciation, amortization) |
| **description** | TEXT | | Full deal description from broker listing |
| **summary** | TEXT | | AI-generated 1-2 sentence summary |
| **industry** | TEXT | | Categorized industry classification |
| **stage** | TEXT | | Business lifecycle stage (early, growth, mature, declining) |
| **score** | INTEGER | | Overall attractiveness score 0-10 |
| **risks** | TEXT | | AI-identified risk flags and concerns |
| **recurring_revenue_signal** | TEXT | | Revenue model assessment (recurring, transactional, mixed) |
| **growth_potential** | TEXT | | Growth trajectory assessment (strong, moderate, flat, declining) |
| **source_url** | TEXT | UNIQUE | Direct link to original listing |
| **source_name** | TEXT | | Broker/platform source (BizBuySell, Flippa, etc.) |
| **raw_price_text** | TEXT | | Original asking price text before parsing |
| **raw_revenue_text** | TEXT | | Original revenue text before normalization |
| **raw_ebitda_text** | TEXT | | Original EBITDA text before normalization |
| **dedupe_hash** | TEXT | UNIQUE | SHA256 hash of (deal_name, location, asking_price) for duplicate detection |
| **scraped_at** | DATETIME | DEFAULT CURRENT_TIMESTAMP | When the deal was scraped from broker |
| **created_at** | DATETIME | DEFAULT CURRENT_TIMESTAMP | When record entered our system |
| **updated_at** | DATETIME | DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |

### Design Rationale

- **Single table**: Simplicity for fast prototyping; no joins needed for core queries
- **Raw fields**: `raw_price_text`, `raw_revenue_text`, `raw_ebitda_text` retain original data for debugging parsing errors
- **Dedupe hash**: Deterministic duplicate detection without requiring broker-provided IDs
- **Timestamps**: Track data freshness and scraping frequency
- **Score field**: Enables sorting and filtering on triage score without recalculation
