# Automation Workflow Notes

## Overview

This project includes an n8n workflow named `Deal Flow OS - Manual Pipeline Run`.

Its job is to execute the Python pipeline from the project virtual environment and return a compact structured summary that can be used for manual testing, scheduled runs, or webhook-based automation.

## Workflow File

Source file:

- [Deal Flow OS - Manual Pipeline Run.json](/c:/RRR/projects/gen-ai-engineer-portfolio/ai-deal-flow-os/automation/n8n_workflows/Deal%20Flow%20OS%20-%20Manual%20Pipeline%20Run.json)

## Triggers

The workflow currently supports three trigger styles:

- `Manual Run`
- `Scheduled Run`
- `Webhook Trigger`

### Manual Run

Used for interactive testing inside n8n.

### Scheduled Run

Configured to run daily at hour `9`.

### Webhook Trigger

Configured with path:

```text
run-deal-pipeline
```

This makes it suitable for external automation or later orchestration from another system.

## Core Execution Step

The main execution node is:

- `Run Deal Pipeline`

It uses the n8n `Execute Command` node to run:

```text
cd /d C:\RRR\projects\gen-ai-engineer-portfolio\ai-deal-flow-os && C:\RRR\projects\gen-ai-engineer-portfolio\ai-deal-flow-os\.venv\Scripts\python.exe -m app.run_pipeline --scrape-limit 15 --enrich-limit 15 --sync-limit 15
```

This means the workflow currently runs the full pipeline with:

- scrape limit = `15`
- enrich limit = `15`
- sync limit = `15`

The command uses the project virtual environment directly, which is good for consistency across local automation runs.

## Error Handling

The `Run Deal Pipeline` node is configured with:

```text
onError = continueErrorOutput
```

That means the workflow still forwards output to the next formatting step even if the command fails. This is useful because the final summary can still report:

- exit code
- stderr
- partial stdout
- status

instead of the whole n8n workflow stopping without context.

## Output Formatting Step

The workflow includes a code node:

- `Format Run Summary`

This node parses the command output and extracts a few useful fields from stdout:

- `insertedDeals`
- `skippedDeals`
- `dealsToEnrich`
- `dealsToSync`
- `syncedDeals`
- `failedDeals`
- `pipelineComplete`
- `status`
- `exitCode`
- `rawStdout`
- `rawStderr`
- `shortSummary`

### Current parsing behavior

The formatter looks for patterns like:

- `Inserted new deals: X`
- `Skipped existing deals: Y`
- `Found X deals to enrich`
- `Found X deal(s) to sync.`
- `[SYNCED]`
- `[FAILED]`

It also checks whether:

- no eligible deals were found for Notion sync
- the pipeline finished completely
- stderr exists
- exit code is non-zero

## Current Summary Logic

If the command fails, the summary returns:

```text
Pipeline failed. Synced A deal(s), failed B. Check stderr/raw logs.
```

If the command succeeds, it returns a summary like:

```text
Pipeline succeeded. Inserted X new deals, skipped Y, enriched Z, synced A, failed B.
```

## Practical Meaning

This workflow already gives you a useful MVP automation layer:

- manual execution from n8n
- daily scheduled execution
- webhook-triggered execution
- structured status reporting after the Python run

That is a strong base for the next step where n8n becomes the operating layer around the pipeline.

## Notes For Future Improvement

- Parse failed enrichment count and failed Notion sync count
- Add Slack, email, or Notion logging for workflow status
- Add separate workflows for:
  - default new-deals pipeline
  - refresh-existing mode
- Add webhook authentication if the workflow is exposed externally
