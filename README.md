# AI Deal Flow Operating System

## Problem
Small investment firms waste time manually scanning broker sites, copying listings into spreadsheets, reviewing weak opportunities, and searching old deal notes.

## Solution
This MVP automates deal sourcing, AI-based analysis and scoring, Notion pipeline updates, workflow alerts, and natural-language search over stored deals.

## MVP Scope
- One-source deal scraper
- Structured deal database
- AI summary + score
- Notion pipeline sync
- n8n workflow automation
- Deal Chat knowledge base

## Architecture
Broker Source -> Scraper -> Cleaner -> SQLite -> AI Enrichment -> Notion -> n8n -> ChromaDB -> Deal Chat

## Tech Stack
Python, BeautifulSoup/Playwright, SQLite, FastAPI, Notion API, n8n, OpenAI API, ChromaDB

## Pipeline Stages
New, Scored, Review, Watchlist, Rejected

## Deliverables
Working MVP, README, architecture diagram, demo script

## Future Improvements
Multi-source ingestion, operator matching, diligence parser, analytics dashboard