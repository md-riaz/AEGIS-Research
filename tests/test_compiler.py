import unittest
from safedash.server.compiler import SQLCompiler, SecurityError
from safedash.server.models import AnalysisPlan, Filter, FilterOperator

class TestSQLCompiler(unittest.TestCase):
    def setUp(self):
        self.compiler = SQLCompiler()



    def test_ast_validation_blocks_forbidden_constructs(self):
        # The query string looks benign but includes UNION
        query_with_union = "SELECT label, value FROM [Order] o UNION SELECT * FROM [Customer]"
        with self.assertRaises(SecurityError):
            self.compiler._validate_sql_safety(query_with_union)

        # DROP pattern
        query_with_drop = "SELECT label FROM [Order] o WHERE o.Id = 1 DROP TABLE Users"
        with self.assertRaises(SecurityError):
            self.compiler._validate_sql_safety(query_with_drop)

    def test_compile_valid_plan(self):
        plan = AnalysisPlan(
            pattern="trend",
            metric="revenue",
            dimension="order_date",
            time_rule="past 24 hours",
            join_path=["Order"],
            filters=[Filter(field="OrderStatusId", operator="=", value=30)],
            visual="area_chart"
        )
        sql, params = self.compiler.compile(plan)
        
        # Verify SELECT contains CAST for date dimension and metric SUM
        self.assertIn("SELECT CAST(o.CreatedOnUtc AS DATE) AS label, SUM(o.OrderTotal - o.RefundedAmount) AS value", sql)
        # Verify time rule translation
        self.assertIn("o.CreatedOnUtc >= DATEADD(hour, -24, GETUTCDATE())", sql)
        # Verify parameterization
        self.assertIn("o.OrderStatusId = @p0", sql)
        self.assertEqual(params["p0"], 30)
        # Verify structure
        self.assertIn("GROUP BY CAST(o.CreatedOnUtc AS DATE)", sql)

    def test_compile_join_path_resolution(self):
        # Metric is revenue (Order), Dimension is category_name (Category)
        plan = AnalysisPlan(
            pattern="segment",
            metric="revenue",
            dimension="category_name",
            join_path=["Order", "Category"],
            filters=[],
            visual="pie_chart"
        )
        sql, params = self.compiler.compile(plan)
        
        # Verify implicitly resolved joins
        self.assertIn("INNER JOIN [OrderItem] oi", sql)
        self.assertIn("INNER JOIN [Product] p", sql)
        self.assertIn("INNER JOIN [Product_Category_Mapping] pcm", sql)
        self.assertIn("INNER JOIN [Category] c", sql)

if __name__ == '__main__':
    unittest.main()
