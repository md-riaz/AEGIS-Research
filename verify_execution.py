"""
Independent verification: actually EXECUTE the already-recorded SQL from a
benchmark results file against the real seeded MySQL database, rather than
trusting that "compiled without a Python exception" (the benchmark scripts'
own metric) means "runs correctly".

No LLM calls are made here — this only replays SQL strings already captured
by a prior benchmark run, so it needs no API key, only a reachable, seeded
database (see evaluation_dataset/README.md for setup).

Usage:
    python verify_execution.py                         # B1: AEGIS vs. direct-LLM baseline
    python verify_execution.py --file evaluation_dataset/benchmark_results_b3.json --field b3_sql --label B3
    python verify_execution.py --file evaluation_dataset/benchmark_results_b2.json --field b2_sql --label B2
"""
import argparse
import json
import os
import re
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def clean_sql(sql):
    if not sql:
        return ""
    matches = re.findall(r"```sql\n(.*?)\n```", sql, re.DOTALL)
    if matches:
        return matches[0].strip()
    return sql.strip()


def connect():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "root"),
        database=os.getenv("MYSQL_DATABASE", "aegis"),
    )


def verify_field(cur, results, field, params_field=None, label=None):
    """Executes every record's `field` (raw SQL text) against the DB and
    returns (ok_count, total, failures[(id, error)])."""
    ok, fail = 0, []
    for r in results:
        sql = clean_sql(r.get(field, ""))
        params = (r.get(params_field) or {}) if params_field else {}
        try:
            if not sql or sql == "Failed":
                raise ValueError("no SQL produced")
            exec_sql = re.sub(r"@(\w+)", r"%(\1)s", sql) if params_field else sql
            for stmt in exec_sql.split(";"):
                stmt = stmt.strip()
                if stmt:
                    cur.execute(stmt, params if params_field else None)
                    cur.fetchall()
            ok += 1
        except Exception as e:
            fail.append((r["id"], str(e)[:150]))
    return ok, len(results), fail


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="evaluation_dataset/benchmark_results.json",
                         help="Results file to verify (default: B1's benchmark_results.json)")
    parser.add_argument("--field", default=None,
                         help="SQL field name to verify (default: run B1's aegis_sql + baseline_sql comparison)")
    parser.add_argument("--params-field", default=None,
                         help="Params dict field name (only used for @named-parameter SQL, e.g. aegis_params)")
    parser.add_argument("--label", default=None, help="Label for output (e.g. B2, B3)")
    args = parser.parse_args()

    with open(args.file, encoding="utf-8") as f:
        results = json.load(f)

    conn = connect()
    cur = conn.cursor()

    if args.field is None:
        # Default / backward-compatible mode: B1 comparison (AEGIS vs. baseline)
        aegis_ok, total, aegis_fail = verify_field(cur, results, "aegis_sql", "aegis_params")
        baseline_ok, _, baseline_fail = verify_field(cur, results, "baseline_sql")

        print("=" * 60)
        print("TRUE EXECUTION VALIDITY (actually ran against MySQL)")
        print("=" * 60)
        print(f"Total queries: {total}")
        print(f"AEGIS    : {aegis_ok}/{total} executed without a DB error ({aegis_ok/total*100:.1f}%)")
        print(f"Baseline : {baseline_ok}/{total} executed without a DB error ({baseline_ok/total*100:.1f}%)")

        if aegis_fail:
            print("\nAEGIS execution failures:")
            for i, err in aegis_fail[:10]:
                print(f"  id {i}: {err}")
        if baseline_fail:
            print("\nBaseline execution failures (sample):")
            for i, err in baseline_fail[:10]:
                print(f"  id {i}: {err}")
    else:
        ok, total, fail = verify_field(cur, results, args.field, args.params_field)
        label = args.label or args.field
        print("=" * 60)
        print(f"TRUE EXECUTION VALIDITY — {label} (actually ran against MySQL)")
        print("=" * 60)
        print(f"Total queries: {total}")
        print(f"{label:<10}: {ok}/{total} executed without a DB error ({ok/total*100:.1f}%)")
        if fail:
            print(f"\n{label} execution failures:")
            for i, err in fail[:15]:
                print(f"  id {i}: {err}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
