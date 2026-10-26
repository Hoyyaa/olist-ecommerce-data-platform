"""Summarize local CSVs without changing source data or enforcing contracts."""

import argparse
import csv
import hashlib
import json
from pathlib import Path


def profile_csv(path):
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        headers = next(reader, [])
        if not headers or len(headers) != len(set(headers)):
            raise ValueError(f"{path.name}: missing or duplicate column names")
        columns = {name: {"missing": 0, "whitespace_only": 0} for name in headers}
        distinct = {name: set() for name in headers}
        seen_rows = set()
        row_count = duplicate_rows = 0
        for row in reader:
            if len(row) != len(headers):
                raise ValueError(f"{path.name}, line {reader.line_num}: wrong field count")
            row_count += 1
            values = tuple(row)
            duplicate_rows += int(values in seen_rows)
            seen_rows.add(values)
            for name, value in zip(headers, row):
                columns[name]["missing"] += int(value == "")
                columns[name]["whitespace_only"] += int(bool(value) and value.isspace())
                if value.strip():
                    distinct[name].add(value)
        for name, stats in columns.items():
            stats["distinct_count"] = len(distinct[name])
    return {"file": path.name, "sha256": digest, "row_count": row_count,
            "column_count": len(headers), "duplicate_rows": duplicate_rows,
            "columns": columns}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        source, output = args.source_dir.resolve(), args.output.resolve()
        files = sorted(source.glob("*.csv"))
        if not files:
            raise ValueError("No CSV files found in the source directory")
        if output.is_relative_to(source):
            raise ValueError("Output must be outside the source directory")
        report = {"datasets": [profile_csv(path) for path in files]}
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
    except (OSError, ValueError, csv.Error) as exc:
        parser.exit(1, f"Profiling failed: {exc}\n")
    print(f"Profiled {len(files)} CSV files. Report: {output}")


if __name__ == "__main__":
    main()
