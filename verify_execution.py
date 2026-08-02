"""
Independent verification: actually EXECUTE the already-recorded aegis_sql and
baseline_sql from evaluation_dataset/benchmark_results.json against the real
seeded MySQL database, rather than trusting that "compiled without a Python
exception" (run_benchmark.py's own metric) means "runs correctly".

No LLM calls are made here — this only replays SQL strings already captured
by a prior `python run_benchmark.py --rerun`, so it needs no API key, only a
reachable, seeded database (see evaluation_dataset/README.md for setup).

Usage:
    python verify_execution.py
"""
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

def main():
    with open("evaluation_dataset/benchmark_results.json", encoding="utf-8") as f:
        results = json.load(f)

    conn = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "root"),
        database=os.getenv("MYSQL_DATABASE", "aegis"),
    )
    cur = conn.cursor()

    aegis_exec_ok, aegis_exec_fail = 0, []
    baseline_exec_ok, baseline_exec_fail = 0, []

    for r in results:
        # --- AEGIS side ---
        sql = r.get("aegis_sql", "")
        params = r.get("aegis_params", {}) or {}
        try:
            # translate @name -> %(name)s for mysql-connector
            exec_sql = re.sub(r"@(\w+)", r"%(\1)s", sql)
            cur.execute(exec_sql, params)
            cur.fetchall()
            aegis_exec_ok += 1
        except Exception as e:
            aegis_exec_fail.append((r["id"], str(e)[:150]))

        # --- Baseline side ---
        bsql = clean_sql(r.get("baseline_sql", ""))
        try:
            if not bsql or bsql == "Failed":
                raise ValueError("no SQL produced")
            for stmt in bsql.split(";"):
                stmt = stmt.strip()
                if stmt:
                    cur.execute(stmt)
                    cur.fetchall()
            baseline_exec_ok += 1
        except Exception as e:
            baseline_exec_fail.append((r["id"], str(e)[:150]))

    total = len(results)
    print("=" * 60)
    print("TRUE EXECUTION VALIDITY (actually ran against MySQL)")
    print("=" * 60)
    print(f"Total queries: {total}")
    print(f"AEGIS    : {aegis_exec_ok}/{total} executed without a DB error ({aegis_exec_ok/total*100:.1f}%)")
    print(f"Baseline : {baseline_exec_ok}/{total} executed without a DB error ({baseline_exec_ok/total*100:.1f}%)")

    if aegis_exec_fail:
        print("\nAEGIS execution failures:")
        for i, err in aegis_exec_fail[:10]:
            print(f"  id {i}: {err}")

    if baseline_exec_fail:
        print("\nBaseline execution failures (sample):")
        for i, err in baseline_exec_fail[:10]:
            print(f"  id {i}: {err}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
