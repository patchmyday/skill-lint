---
name: perfect-skill
description: >-
  Analyze and transform CSV data files into structured reports. Use this skill whenever the user
  wants to parse CSV files, generate summary statistics, create pivot tables, or export data to
  JSON/Excel formats. TRIGGER when user mentions .csv files, data analysis, or asks to summarize
  tabular data. Supports pandas, polars, and built-in csv module. DO NOT use when the user wants
  to create charts or visualizations — use the chart-builder skill instead. Examples: "summarize
  this CSV", "convert CSV to JSON", "find duplicates in my data file".
license: MIT
---

# CSV Data Analyzer

## Overview

This skill processes CSV files and produces structured reports. It handles common data tasks
like deduplication, aggregation, and format conversion.

## When to Use

- User has a `.csv` file and wants analysis
- User asks to convert tabular data between formats
- User needs summary statistics from a dataset

## Common Patterns

### Reading CSV Files

```python
import pandas as pd

df = pd.read_csv("data.csv")
print(df.describe())
```

### Exporting to JSON

```python
df.to_json("output.json", orient="records", indent=2)
```

## Gotchas and Pitfalls

- Always check encoding — many CSV files use `latin-1` instead of `utf-8`
- Large files (>1GB) should use `polars` instead of `pandas` for memory efficiency
- Watch out for mixed types in columns — use `dtype=str` to avoid silent coercion

## Advanced Usage

For detailed column mapping and custom aggregations, see references/ADVANCED.md.
Run scripts/validate.sh to check data integrity before processing.
