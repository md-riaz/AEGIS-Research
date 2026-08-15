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
    """Executes every record's `field` (raw SQL text) against the DB.

    Returns ``(ok_count, attempted, failures, declined, errored)``.

    "Attempted" counts only the requests that produced SQL. A request AEGIS
    declined produced none *by design*, and counting that as an execution
    failure measures the abstention channel working rather than the compiler
    failing — the system scored 34/107 (31.8%) under that reading while 34 of
    its 40 actual queries ran, because 67 correct refusals were being tallied
    as broken SQL.

    The distinction did not exist when this script was written, because the
    pipeline answered everything; it does now, so execution validity is
    reported over the queries that exist. `declined` is returned alongside so
    the two are always visible together and neither can be quietly dropped.
    """
    ok, fail, declined, errored = 0, [], [], []
    for r in results:
        sql = clean_sql(r.get(field, ""))
        params = (r.get(params_field) or {}) if params_field else {}
        if not sql or sql == "Failed":
            # "No SQL" has two very different causes and they must not share a
            # bucket. A declined request produced none by design; a crashed one
            # produced none because the pipeline broke. Counting the second as
            # the first excludes a fault from the denominator and *raises* the
            # reported rate — the same shape of error as scoring a refusal as a
            # failure, pointing the other way.
            if (r.get("aegis_outcome") == "error"
                    or r.get("aegis_status") in ("failed", "fatal_error")):
                errored.append(r["id"])
            else:
                declined.append(r["id"])
            continue
        try:
            exec_sql = re.sub(r"@(\w+)", r"%(\1)s", sql) if params_field else sql
            for stmt in exec_sql.split(";"):
                stmt = stmt.strip()
                if stmt:
                    cur.execute(stmt, params if params_field else None)
                    cur.fetchall()
            ok += 1
        except Exception as e:
            fail.append((r["id"], str(e)[:150]))
    return ok, ok + len(fail), fail, declined, errored


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
        aegis_ok, aegis_n, aegis_fail, aegis_declined, aegis_errored = verify_field(
            cur, results, "aegis_sql", "aegis_params")
        (baseline_ok, baseline_n, baseline_fail,
         baseline_declined, baseline_errored) = verify_field(
            cur, results, "baseline_sql")

        def pct(ok, n):
            return f"{ok}/{n} ({ok / n * 100:.1f}%)" if n else "n/a (no SQL produced)"

        print("=" * 60)
        print("TRUE EXECUTION VALIDITY (actually ran against MySQL)")
        print("=" * 60)
        print(f"Requests in file: {len(results)}")
        print(f"AEGIS    : {pct(aegis_ok, aegis_n)} of the queries it produced")
        print(f"           {len(aegis_declined)} request(s) declined by design — not an")
        print( "           execution failure, and excluded from the rate above")
        print(f"           {len(aegis_errored)} request(s) produced no SQL because the pipeline")
        print( "           errored. Also outside the rate, but a fault, not a decision:")
        print(f"           {aegis_errored if aegis_errored else 'none'}")
        print(f"Baseline : {pct(baseline_ok, baseline_n)} of the queries it produced")
        print(f"           {len(baseline_declined) + len(baseline_errored)} request(s) produced no SQL")
        print()
        print("Execution validity says the SQL runs. It says nothing about")
        print("whether the answer is right — see evaluate_abstention.py and")
        print("docs/analysis/nopcommerce_sql_parity.md for that.")

        if aegis_fail:
            print("\nAEGIS execution failures:")
            for i, err in aegis_fail[:10]:
                print(f"  id {i}: {err}")
        if baseline_fail:
            print("\nBaseline execution failures (sample):")
            for i, err in baseline_fail[:10]:
                print(f"  id {i}: {err}")
    else:
        ok, n, fail, declined, errored = verify_field(
            cur, results, args.field, args.params_field)
        label = args.label or args.field
        print("=" * 60)
        print(f"TRUE EXECUTION VALIDITY — {label} (actually ran against MySQL)")
        print("=" * 60)
        print(f"Requests in file: {len(results)}")
        rate = f"{ok}/{n} ({ok / n * 100:.1f}%)" if n else "n/a (no SQL produced)"
        print(f"{label:<10}: {rate} of the queries it produced")
        print(f"{'':10}  {len(declined)} declined, {len(errored)} errored — both outside the rate")
        if fail:
            print(f"\n{label} execution failures:")
            for i, err in fail[:15]:
                print(f"  id {i}: {err}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
