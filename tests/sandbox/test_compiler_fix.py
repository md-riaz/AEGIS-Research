from aegis.server.compiler import SQLCompiler
from aegis.server.models import AnalysisPlan, Filter

def test_compiler_objects():
    compiler = SQLCompiler()
    f = Filter(field="status", operator="=", value="complete")
    plan = AnalysisPlan(
        pattern="kpi",
        metric="order_count",
        dimension=None,
        join_path=["Order"],
        filters=[f],
        visual="kpi_card"
    )
    
    try:
        sql = compiler.compile(plan)
        print("Success!")
        print(sql)
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_compiler_objects()
