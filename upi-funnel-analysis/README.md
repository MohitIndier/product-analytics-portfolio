Update: link to Medium for full analysis + queries
https://getmohit.medium.com/upi-funnel-drop-off-analysis-fc15ed8ed067?postPublishedType=initial

## How to reproduce this dataset

### 1. Generate the data
Requires Python 3.8+, no external libraries needed (uses only Python's built-in `random`, `csv`, `datetime`).

```bash
python generate_data.py
```

This creates `upi_transactions.csv` with 50,716 rows — deterministic output 
(seeded), so re-running this always produces the identical dataset used in 
the analysis.

### 2. Load it into Postgres
Requires `pandas` and `sqlalchemy` (`pip install pandas sqlalchemy psycopg2-binary`).

Open `upload_to_postgres.py` and update:
- The `csv_file` path — point it to wherever you saved the CSV from step 1
- The connection string — replace with your own Postgres credentials

Then run:

```bash
python upload_to_postgres.py
```

This creates the schema `upi_funnel` (create it first with 
`CREATE SCHEMA IF NOT EXISTS upi_funnel;` if it doesn't already exist) and 
loads the table `upi_funnel.upi_transactions`.

### 3. Run the analysis
Full SQL queries, findings, and recommendations are published on Medium. Link Above.
