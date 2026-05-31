# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "duckdb==1.53",
#   "pandas==3.0.3",
# ]
# ///
"""
Inspect a local data file and print shape, types, sample rows, and quality findings.

Usage:
    uv run scripts/inspect_data.py path/to/file.csv
    uv run scripts/inspect_data.py path/to/file.parquet

Supported formats: .csv, .tsv, .parquet, .json, .jsonl
For .xlsx files, convert to CSV first (see DuckDB gotchas in SKILL.md).
"""

import argparse
import sys
from pathlib import Path

import duckdb

_READER: dict[str, str] = {
    ".csv": "read_csv_auto('{p}')",
    ".tsv": "read_csv_auto('{p}', delim='\\t')",
    ".parquet": "read_parquet('{p}')",
    ".json": "read_json_auto('{p}')",
    ".jsonl": "read_json_auto('{p}')",
}

_CATEGORICAL_TYPES = ("VARCHAR", "BOOLEAN", "ENUM")


def from_expr(path: str) -> str:
    ext = Path(path).suffix.lower()
    template = _READER.get(ext)
    if template is None:
        print(
            f"Error: unsupported extension '{ext}'. Supported: {', '.join(_READER)}",
            file=sys.stderr,
        )
        sys.exit(2)
    return template.format(p=path)


def null_counts(con: duckdb.DuckDBPyConnection, expr: str, cols: list[str]) -> list[int]:
    """Return per-column null counts in column order."""
    null_sql = ", ".join(
        f"SUM(CASE WHEN \"{col}\" IS NULL THEN 1 ELSE 0 END)"
        for col in cols
    )
    return list(con.execute(f"SELECT {null_sql} FROM {expr}").fetchone())


def cardinality(con: duckdb.DuckDBPyConnection, expr: str, col: str) -> int:
    return con.execute(f'SELECT COUNT(DISTINCT "{col}") FROM {expr}').fetchone()[0]


def inspect(path: str) -> None:
    con = duckdb.connect()
    expr = from_expr(path)

    row_count: int = con.execute(f"SELECT COUNT(*) FROM {expr}").fetchone()[0]
    schema = con.execute(f"DESCRIBE SELECT * FROM {expr}").df()
    sample = con.execute(f"SELECT * FROM {expr} LIMIT 5").df()

    cols = list(schema["column_name"])
    dtypes = list(schema["column_type"])
    nulls = null_counts(con, expr, cols)

    print(f"File: {path}")
    print(f"Shape: {row_count} rows × {len(cols)} columns\n")
    print("Columns:")
    for col, dtype, null_n in zip(cols, dtypes, nulls):
        parts = [f"  {col} ({dtype})"]
        if null_n:
            parts.append(f"{null_n} nulls")
        if any(t in dtype for t in _CATEGORICAL_TYPES):
            n_unique = cardinality(con, expr, col)
            if n_unique <= 50:
                parts.append(f"{n_unique} unique values")
        print(", ".join(parts))

    print("\nSample (first 5 rows):")
    print(sample.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect a local data file and print shape, types, and sample rows.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Supported formats: .csv, .tsv, .parquet, .json, .jsonl",
    )
    parser.add_argument("path", help="Path to the data file")
    args = parser.parse_args()

    if not Path(args.path).exists():
        print(f"Error: file not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    inspect(args.path)


if __name__ == "__main__":
    main()
