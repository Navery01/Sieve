# Sieve

Sieve is a Python project for crawling structured data sources and detecting potentially sensitive information in sampled data. The current implementation centers on PostgreSQL, with an async connector, structured crawler abstractions, and a detection agent built on Microsoft Presidio.

## What it does

- Connects to a PostgreSQL instance using an async SQLAlchemy engine
- Crawls structured database metadata and sample rows
- Runs PII detection using Presidio analyzer components
- Organizes crawling behavior through connector, crawler, and scope abstractions
- Leaves room for future support for flat files, MySQL, and semi-structured sources

## Repository structure

- `apps/sieve-core/` — main Python package and application code
- `docs/` — documentation workspace
- `requirements.txt` — Python dependencies for the current codebase

## Main components

### Detection agent
The detection agent wraps Presidio Analyzer and returns structured matches containing entity type, offsets, confidence score, and matched subtext.

### Connectors
Connectors handle access to data sources.

- `PostgresConnector` is the primary implemented connector today
- `FlatFileConnector` and `mysql_connector.py` appear to be placeholders for future work

### Crawlers
Crawlers orchestrate enumeration and traversal of data sources.

- `StructuredCrawler` is used by the current entrypoint
- Base crawler classes define the common interface
- Semi-structured crawler support is scaffolded but not yet implemented

### Scopes
Scopes define crawl boundaries such as include/exclude patterns, row limits, depth, and timeout behavior.

## Current entrypoint
The current executable flow is in `apps/sieve-core/src/sieve_core/main.py`.

It accepts command-line arguments for:

- target directory
- database server
- port
- username
- password

The script currently:

1. initializes logging
2. creates the detection agent, structured crawler, and PostgreSQL connector
3. connects to the database
4. initializes the crawler with a structured scope
5. runs the crawl
6. prints discovered structure information

## Installation

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

Depending on your environment and the parts of the project you plan to run, you may also need additional packages that are imported in the codebase but not currently listed in `requirements.txt`, such as Presidio-related packages and async PostgreSQL drivers.

## Usage

Example invocation of the current entrypoint:

```bash
python -m sieve_core.main \
  --server localhost \
  --port 5432 \
  --username username \
  --password password
```

If you are running the module from the package source tree, make sure your Python path/package layout is set up so `sieve_core` is importable.

## Status

This repository appears to be an early-stage foundation for a data-discovery and PII-detection tool. Several parts of the architecture are in place, while some connectors and crawler types are still incomplete or stubbed.

## Roadmap ideas

Potential next improvements:

- add a proper installation and packaging flow
- document environment setup and required optional dependencies
- add examples for supported databases
- implement remaining connectors and crawler types
- add tests for connectors, scopes, and detection behavior
- add output/reporting formats for scan results

## License

No license is currently specified for this repository.
