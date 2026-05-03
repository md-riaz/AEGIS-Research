from typing import List, Dict, Any
from pydantic import BaseModel

class SemanticObject(BaseModel):
    id: str
    label: str
    description: str
    sql_expr: str
    binding_table: str
    required_joins: List[str] = []

class Metric(SemanticObject):
    default_visual: str = "kpi_card"
    security_class: str = "public"

class Dimension(SemanticObject):
    datatype: str

class JoinPath(BaseModel):
    source: str
    target: str
    on_clause: str

# nopCommerce Semantic Layer Definition
METRICS = [
    Metric(
        id="revenue",
        label="Total Revenue",
        description="Sum of order totals excluding refunded amounts",
        sql_expr="SUM(o.OrderTotal - o.RefundedAmount)",
        binding_table="Order",
        default_visual="kpi_card"
    ),
    Metric(
        id="order_count",
        label="Number of Orders",
        description="Total count of unique orders",
        sql_expr="COUNT(DISTINCT o.Id)",
        binding_table="Order"
    ),
    Metric(
        id="avg_order_value",
        label="Average Order Value",
        description="Average revenue per order",
        sql_expr="AVG(o.OrderTotal)",
        binding_table="Order"
    ),
    Metric(
        id="item_quantity",
        label="Quantity Sold",
        description="Total number of items sold",
        sql_expr="SUM(oi.Quantity)",
        binding_table="OrderItem",
        required_joins=["OrderItem"]
    ),
    Metric(
        id="shipping_cost",
        label="Shipping Cost",
        description="Total shipping fees",
        sql_expr="SUM(o.OrderShipping)",
        binding_table="Order"
    ),
    Metric(
        id="customer_count",
        label="Number of Customers",
        description="Total unique customers",
        sql_expr="COUNT(DISTINCT cu.Id)",
        binding_table="Customer",
        required_joins=["Customer"]
    ),
    Metric(
        id="refund_count",
        label="Number of Refunds",
        description="Total count of orders with refunds",
        sql_expr="COUNT(DISTINCT CASE WHEN o.RefundedAmount > 0 THEN o.Id END)",
        binding_table="Order"
    ),
    Metric(
        id="refund_amount",
        label="Total Refunded",
        description="Sum of all refunded amounts",
        sql_expr="SUM(o.RefundedAmount)",
        binding_table="Order"
    ),
    Metric(
        id="discount_amount",
        label="Total Discount",
        description="Sum of all order discounts",
        sql_expr="SUM(o.OrderDiscount)",
        binding_table="Order"
    ),
    Metric(
        id="profit",
        label="Profit",
        description="Gross profit (revenue minus cost)",
        sql_expr="SUM(o.OrderTotal - o.OrderSubtotalExclTax)",
        binding_table="Order"
    )
]

DIMENSIONS = [
    Dimension(
        id="product_name",
        label="Product Name",
        description="Name of the product",
        sql_expr="p.Name",
        binding_table="Product",
        datatype="string"
    ),
    Dimension(
        id="category_name",
        label="Category",
        description="Category name",
        sql_expr="c.Name",
        binding_table="Category",
        datatype="string",
        required_joins=["Product_Category_Mapping", "Category"]
    ),
    Dimension(
        id="customer_email",
        label="Customer Email",
        description="Email address of the customer",
        sql_expr="cu.Email",
        binding_table="Customer",
        datatype="string"
    ),
    Dimension(
        id="product_stock",
        label="Stock Level",
        description="Quantity in stock",
        sql_expr="p.StockQuantity",
        binding_table="Product",
        datatype="number"
    ),
    Dimension(
        id="product_rating",
        label="Rating",
        description="Average customer rating",
        sql_expr="p.ApprovedTotalReviews", # Simplified
        binding_table="Product",
        datatype="number"
    ),
    Dimension(
        id="order_date",
        label="Order Date",
        description="Date order was placed",
        sql_expr="o.CreatedOnUtc",
        binding_table="Order",
        datatype="date"
    ),
    Dimension(
        id="customer_registration_date",
        label="Customer Registration Date",
        description="Date customer registered",
        sql_expr="cu.CreatedOnUtc",
        binding_table="Customer",
        datatype="date"
    ),
    Dimension(
        id="OrderStatusId",
        label="Order Status ID",
        description="Internal status code of the order",
        sql_expr="o.OrderStatusId",
        binding_table="Order",
        datatype="number"
    ),
    Dimension(
        id="PaymentStatusId",
        label="Payment Status ID",
        description="Internal payment status code",
        sql_expr="o.PaymentStatusId",
        binding_table="Order",
        datatype="number"
    ),
    Dimension(
        id="ShippingStatusId",
        label="Shipping Status ID",
        description="Internal shipping status code",
        sql_expr="o.ShippingStatusId",
        binding_table="Order",
        datatype="number"
    ),
    Dimension(
        id="payment_method",
        label="Payment Method",
        description="Payment method used for the order",
        sql_expr="o.PaymentMethodSystemName",
        binding_table="Order",
        datatype="string"
    ),
    Dimension(
        id="country_name",
        label="Country",
        description="Billing country of the order",
        sql_expr="o.BillingCountry",
        binding_table="Order",
        datatype="string"
    )
]

JOIN_GRAPH = [
    JoinPath(source="Order", target="Customer", on_clause="o.CustomerId = cu.Id"),
    JoinPath(source="Order", target="OrderItem", on_clause="o.Id = oi.OrderId"),
    JoinPath(source="OrderItem", target="Product", on_clause="oi.ProductId = p.Id"),
    JoinPath(source="Product", target="Product_Category_Mapping", on_clause="p.Id = pcm.ProductId"),
    JoinPath(source="Product_Category_Mapping", target="Category", on_clause="pcm.CategoryId = c.Id")
]

# No synonym dictionary needed — the LLM prompt contains the full approved
# vocabulary and maps user language directly to canonical metric/dimension IDs.
SYNONYMS = {}

# Mapping of abstract terms to schema-level filters
BUSINESS_LOGIC_MAPPINGS = {
    "abandoned": {
        "field": "OrderStatusId",
        "operator": "=",
        "value": 40
    },
    "first_time": {
        "field": "o.Id", # Placeholder for complex logic, mapped to a dimension in a real system
        "operator": "is_not_null",
        "value": True
    },
    "referral_source": {
        "field": "cu.AdminComment", # Real nopCommerce often uses a generic field or plugin
        "operator": "contains",
        "value": "ref:"
    }
}

# Mapping of table aliases to actual table names for the compiler
ALIAS_TO_TABLE = {
    "cu": "Customer",
    "o": "Order",
    "oi": "OrderItem",
    "p": "Product",
    "c": "Category",
    "pcm": "Product_Category_Mapping"
}
