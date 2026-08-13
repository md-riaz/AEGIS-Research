"""
AEGIS Semantic Layer — the closed vocabulary that controls every query.

Three core concepts:
  METRICS     — measurable numerical facts (revenue, order count, etc.).
                Each metric defines an SQL aggregate expression and the
                table it is bound to.
  DIMENSIONS  — grouping/filtering axes (product name, date, country, etc.).
                Each dimension defines an SQL expression and its data type.
  JOIN_GRAPH  — the 11-edge undirected graph that connects the 12 analytics
                tables exposed by the semantic layer (out of 126 tables in
                the full nopCommerce schema).  The compiler uses BFS over
                this graph to find the minimal join path for any given
                metric+dimension combination.

Additional structures:
  STATUS_EXPRESSIONS      — human-readable CASE mappings for coded ID columns.
  BUSINESS_LOGIC_MAPPINGS — abstract business terms → concrete SQL predicates.
  ALIAS_TO_TABLE          — reverse lookup from SQL alias to table name.
  SYNONYMS                — intentionally empty (see comment below).
"""

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
    #: The entity this attribute describes ("product", "customer", "order").
    #: Several attributes share an entity, so a bare entity word like "product"
    #: matches all of them equally and looks ambiguous when it is not.
    entity: str = ""
    #: True for the one attribute that *identifies* its entity — the value a
    #: person would read to tell one instance from another. When a request
    #: names an entity rather than an attribute ("revenue by product"), this is
    #: what they mean; the alternative is asking them to choose between a name,
    #: a price and a published flag, which is not a real question.
    is_label: bool = False

class JoinPath(BaseModel):
    source: str
    target: str
    on_clause: str

# ============================================================
# METRICS — aggregate expressions over the nopCommerce schema.
# Each Metric has an SQL aggregate expression (e.g. SUM/COUNT),
# a binding_table (the primary table it reads from), and
# optional required_joins (additional tables that must be joined).
# Full nopCommerce schema: 126 tables. Semantic layer exposes 12 analytics tables.
# ============================================================

METRICS = [
    Metric(
        id="revenue",
        label="Total Revenue",
        description="Sum of order totals excluding refunded amounts, also called sales or turnover",
        sql_expr="SUM(COALESCE(o.OrderTotal, 0) - COALESCE(o.RefundedAmount, 0))",
        binding_table="Order",
        default_visual="kpi_card"
    ),
    Metric(
        id="order_count",
        label="Number of Orders",
        description="Total count of unique orders, also called order volume",
        sql_expr="COUNT(DISTINCT o.Id)",
        binding_table="Order"
    ),
    Metric(
        id="avg_order_value",
        label="Average Order Value",
        description="Average revenue per order",
        sql_expr="AVG(COALESCE(o.OrderTotal, 0))",
        binding_table="Order"
    ),
    Metric(
        id="item_quantity",
        label="Quantity Sold",
        description="Total number of items sold, also called units sold",
        sql_expr="SUM(COALESCE(oi.Quantity, 0))",
        binding_table="OrderItem",
        required_joins=["OrderItem"]
    ),
    Metric(
        id="shipping_cost",
        label="Shipping Cost",
        description="Total shipping fees (excluding tax)",
        sql_expr="SUM(o.OrderShippingExclTax)",
        binding_table="Order"
    ),
    Metric(
        id="customer_count",
        label="Number of Customers",
        description="Total unique customers, also called buyers or shoppers",
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
        description="Gross profit (order total minus subtotal cost)",
        sql_expr="SUM(COALESCE(o.OrderTotal, 0) - COALESCE(o.OrderSubtotalExclTax, 0))",
        binding_table="Order"
    ),
    Metric(
        id="line_item_revenue",
        label="Product Revenue",
        description="Total revenue from line items (product-level sales)",
        sql_expr="SUM(oi.PriceExclTax)",
        binding_table="OrderItem",
        required_joins=["OrderItem"]
    ),
    Metric(
        id="tax_amount",
        label="Tax Amount",
        description="Total order tax collected",
        sql_expr="SUM(o.OrderTax)",
        binding_table="Order"
    ),
    Metric(
        id="line_item_cost",
        label="Product Cost",
        description="Total original product cost from line items",
        sql_expr="SUM(oi.OriginalProductCost)",
        binding_table="OrderItem",
        required_joins=["OrderItem"]
    ),
    Metric(
        id="line_item_discount",
        label="Line Item Discount",
        description="Total discount applied at line-item level",
        sql_expr="SUM(oi.DiscountAmountExclTax)",
        binding_table="OrderItem",
        required_joins=["OrderItem"]
    ),
    Metric(
        id="shipment_count",
        label="Shipment Count",
        description="Total number of shipments created",
        sql_expr="COUNT(DISTINCT sh.Id)",
        binding_table="Shipment",
        required_joins=["Shipment"]
    ),
    # --- Ratio metrics -------------------------------------------------
    # A rate is the quotient of two aggregates, which is still a single SQL
    # aggregate expression — so ratios need no compiler change, only a
    # definition. NULLIF guards the zero denominator.
    Metric(
        id="refund_rate",
        label="Refund Rate",
        description="Refunded amount as a share of order totals, also called refund percentage",
        sql_expr="SUM(COALESCE(o.RefundedAmount,0)) / NULLIF(SUM(COALESCE(o.OrderTotal,0)), 0)",
        binding_table="Order"
    ),
    Metric(
        id="discount_rate",
        label="Discount Rate",
        description="Discount as a share of order totals, also called discount percentage",
        sql_expr="SUM(COALESCE(o.OrderDiscount,0)) / NULLIF(SUM(COALESCE(o.OrderTotal,0)), 0)",
        binding_table="Order"
    ),
    Metric(
        id="profit_margin",
        label="Profit Margin",
        description="Profit as a share of revenue, also called margin or gross margin",
        sql_expr="SUM(COALESCE(o.OrderTotal,0) - COALESCE(o.OrderSubtotalExclTax,0)) / NULLIF(SUM(COALESCE(o.OrderTotal,0)), 0)",
        binding_table="Order"
    ),
    # --- Newly exposed source tables ------------------------------------
    Metric(
        id="coupon_redemption_count",
        label="Coupon Redemptions",
        description="Number of discount or coupon redemptions recorded against orders",
        sql_expr="COUNT(DISTINCT duh.Id)",
        binding_table="DiscountUsageHistory",
        required_joins=["DiscountUsageHistory"]
    ),
    Metric(
        id="cart_item_count",
        label="Cart Items",
        description="Number of items sitting in shopping carts, used for cart abandonment",
        sql_expr="COUNT(DISTINCT sci.Id)",
        binding_table="ShoppingCartItem",
        required_joins=["ShoppingCartItem"]
    ),
    Metric(
        id="review_count",
        label="Number of Reviews",
        description="Count of product reviews submitted by customers",
        sql_expr="COUNT(DISTINCT pr.Id)",
        binding_table="ProductReview",
        required_joins=["ProductReview"]
    ),
    Metric(
        id="avg_review_rating",
        label="Average Review Rating",
        description="Average star rating across product reviews",
        sql_expr="AVG(pr.Rating)",
        binding_table="ProductReview",
        required_joins=["ProductReview"]
    ),
]

# ============================================================
# DIMENSIONS — grouping and filtering axes.
# Each Dimension defines an SQL expression to SELECT/GROUP BY,
# a data type (string/number/date), and optional required_joins.
# ============================================================
DIMENSIONS = [
    # --- Product dimensions ---
    Dimension(
        id="product_name",
        entity="product",
        is_label=True,
        label="Product Name",
        description="Name of the product",
        sql_expr="p.Name",
        binding_table="Product",
        datatype="string"
    ),
    Dimension(
        id="product_sku",
        entity="product",
        label="Product SKU",
        description="Stock keeping unit code",
        sql_expr="p.Sku",
        binding_table="Product",
        datatype="string"
    ),
    Dimension(
        id="product_price",
        entity="product",
        label="Product Price",
        description="Current listed price of the product",
        sql_expr="p.Price",
        binding_table="Product",
        datatype="number"
    ),
    Dimension(
        id="product_cost",
        entity="product",
        label="Product Cost",
        description="Manufacturing/acquisition cost of the product",
        sql_expr="p.ProductCost",
        binding_table="Product",
        datatype="number"
    ),
    Dimension(
        id="product_stock",
        entity="product",
        label="Stock Level",
        # The description doubles as the vocabulary surface the grounding
        # engine matches against, so business aliases ("inventory", "on hand")
        # belong here rather than in a separate synonym dictionary.
        description="Quantity in stock, also called inventory or stock on hand",
        sql_expr="p.StockQuantity",
        binding_table="Product",
        datatype="number"
    ),
    Dimension(
        id="product_rating",
        entity="product",
        label="Rating",
        description="Number of approved customer reviews, also called stars or review score",
        sql_expr="p.ApprovedTotalReviews",
        binding_table="Product",
        datatype="number"
    ),
    Dimension(
        id="product_published",
        entity="product",
        label="Product Published",
        description="Whether the product is published (1=yes, 0=no)",
        sql_expr="p.Published",
        binding_table="Product",
        datatype="number"
    ),
    Dimension(
        id="product_created_date",
        entity="product",
        label="Product Created Date",
        description="Date product was added to catalog",
        sql_expr="p.CreatedOnUtc",
        binding_table="Product",
        datatype="date"
    ),

    # --- Category dimension ---
    Dimension(
        id="category_name",
        entity="category",
        is_label=True,
        label="Category",
        description="Category name",
        sql_expr="c.Name",
        binding_table="Category",
        datatype="string",
        required_joins=["Product_Category_Mapping", "Category"]
    ),

    # --- Manufacturer dimension ---
    Dimension(
        id="manufacturer_name",
        entity="manufacturer",
        is_label=True,
        label="Manufacturer",
        description="Brand/manufacturer name",
        sql_expr="mf.Name",
        binding_table="Manufacturer",
        datatype="string",
        required_joins=["Product_Manufacturer_Mapping", "Manufacturer"]
    ),

    # --- Customer dimensions ---
    Dimension(
        id="customer_name",
        entity="customer",
        is_label=True,
        label="Customer Name",
        description="Full name of the customer (FirstName LastName)",
        sql_expr="CONCAT(cu.FirstName, ' ', cu.LastName)",
        binding_table="Customer",
        datatype="string"
    ),
    Dimension(
        id="customer_email",
        entity="customer",
        label="Customer Email",
        description="Email address of the customer",
        sql_expr="cu.Email",
        binding_table="Customer",
        datatype="string"
    ),
    Dimension(
        id="customer_active",
        entity="customer",
        label="Customer Active",
        description="Whether customer account is active (1=yes, 0=no)",
        sql_expr="cu.Active",
        binding_table="Customer",
        datatype="number"
    ),
    Dimension(
        id="customer_registration_date",
        entity="customer",
        label="Customer Registration Date",
        description="Date customer registered",
        sql_expr="cu.CreatedOnUtc",
        binding_table="Customer",
        datatype="date"
    ),

    # --- Order dimensions ---
    Dimension(
        id="order_id",
        entity="order",
        is_label=True,
        label="Order ID",
        description="Unique identifier of the order",
        sql_expr="o.Id",
        binding_table="Order",
        datatype="number"
    ),
    Dimension(
        id="order_date",
        entity="order",
        label="Order Date",
        description="Date order was placed",
        sql_expr="o.CreatedOnUtc",
        binding_table="Order",
        datatype="date"
    ),
    Dimension(
        id="order_month",
        entity="order",
        label="Order Month",
        description="Month when order was placed (YYYY-MM format)",
        sql_expr="DATE_FORMAT(o.CreatedOnUtc, '%Y-%m')",
        binding_table="Order",
        datatype="string"
    ),
    Dimension(
        id="order_year",
        entity="order",
        label="Order Year",
        description="Year when order was placed",
        sql_expr="YEAR(o.CreatedOnUtc)",
        binding_table="Order",
        datatype="number"
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
        id="order_status",
        entity="order",
        label="Order Status",
        description="Human-readable order status (Pending, Processing, Complete, Cancelled)",
        sql_expr="CASE o.OrderStatusId WHEN 10 THEN 'Pending' WHEN 20 THEN 'Processing' WHEN 30 THEN 'Complete' WHEN 40 THEN 'Cancelled' ELSE 'Unknown' END",
        binding_table="Order",
        datatype="string"
    ),
    Dimension(
        id="payment_status",
        entity="order",
        label="Payment Status",
        description="Human-readable payment status (Pending, Authorized, Paid, PartiallyRefunded, Refunded, Voided)",
        sql_expr="CASE o.PaymentStatusId WHEN 10 THEN 'Pending' WHEN 20 THEN 'Authorized' WHEN 30 THEN 'Paid' WHEN 35 THEN 'PartiallyRefunded' WHEN 40 THEN 'Refunded' WHEN 50 THEN 'Voided' ELSE 'Unknown' END",
        binding_table="Order",
        datatype="string"
    ),
    Dimension(
        id="shipping_status",
        entity="order",
        label="Shipping Status",
        description="Human-readable shipping status (Not Required, Not Yet Shipped, Shipped, Delivered)",
        sql_expr="CASE o.ShippingStatusId WHEN 10 THEN 'Not Required' WHEN 20 THEN 'Not Yet Shipped' WHEN 30 THEN 'Shipped' WHEN 40 THEN 'Delivered' WHEN 50 THEN 'Partially Shipped' ELSE 'Unknown' END",
        binding_table="Order",
        datatype="string"
    ),
    Dimension(
        id="payment_method",
        entity="order",
        label="Payment Method",
        description="Payment method used for the order",
        sql_expr="o.PaymentMethodSystemName",
        binding_table="Order",
        datatype="string"
    ),
    Dimension(
        id="currency_code",
        entity="order",
        label="Currency",
        description="Currency code used for the order",
        sql_expr="o.CustomerCurrencyCode",
        binding_table="Order",
        datatype="string"
    ),
    Dimension(
        id="shipping_method",
        entity="order",
        label="Shipping Method",
        description="Shipping method chosen for the order",
        sql_expr="o.ShippingMethod",
        binding_table="Order",
        datatype="string"
    ),
    Dimension(
        id="order_number",
        entity="order",
        label="Order Number",
        description="Custom order number (e.g. ORD-00001)",
        sql_expr="o.CustomOrderNumber",
        binding_table="Order",
        datatype="string"
    ),

    # --- Geography dimensions (via Address → Country) ---
    Dimension(
        id="country_name",
        entity="country",
        is_label=True,
        label="Billing Country",
        description="Country name from the billing address",
        sql_expr="co.Name",
        binding_table="Country",
        datatype="string",
        required_joins=["Address", "Country"]
    ),
    Dimension(
        id="billing_city",
        entity="country",
        label="Billing City",
        description="City from the billing address",
        sql_expr="addr.City",
        binding_table="Address",
        datatype="string",
        required_joins=["Address"]
    ),

    # --- Shipment dimensions ---
    Dimension(
        id="tracking_number",
        entity="shipment",
        is_label=True,
        label="Tracking Number",
        description="Shipment tracking number",
        sql_expr="sh.TrackingNumber",
        binding_table="Shipment",
        datatype="string",
        required_joins=["Shipment"]
    ),
    Dimension(
        id="shipped_date",
        entity="shipment",
        label="Shipped Date",
        description="Date the shipment was dispatched",
        sql_expr="sh.ShippedDateUtc",
        binding_table="Shipment",
        datatype="date",
        required_joins=["Shipment"]
    ),
    Dimension(
        id="delivery_date",
        entity="shipment",
        label="Delivery Date",
        description="Date the shipment was delivered",
        sql_expr="sh.DeliveryDateUtc",
        binding_table="Shipment",
        datatype="date",
        required_joins=["Shipment"]
    ),

    # --- Store dimension ---
    Dimension(
        id="store_name",
        entity="store",
        is_label=True,
        label="Store",
        description="Store name for multi-store setups",
        sql_expr="st.Name",
        binding_table="Store",
        datatype="string",
        required_joins=["Store"]
    ),
    Dimension(
        id="product_tag",
        entity="product",
        label="Product Tag",
        description="Tag or keyword attached to a product",
        sql_expr="pt.Name",
        binding_table="ProductTag",
        required_joins=["Product_ProductTag_Mapping", "ProductTag"],
        datatype="string"
    ),
    Dimension(
        id="customer_cohort",
        entity="customer",
        label="Customer Cohort",
        description=(
            "Whether a customer is buying for the first time or returning, "
            "also called first-time versus repeat or new versus returning buyers"
        ),
        sql_expr=(
            "CASE WHEN (SELECT COUNT(*) FROM `Order` o2 "
            "WHERE o2.CustomerId = o.CustomerId AND o2.Deleted = 0) > 1 "
            "THEN 'Returning' ELSE 'First-time' END"
        ),
        binding_table="Order",
        datatype="string"
    ),

]
# ============================================================
# JOIN GRAPH — undirected graph of join relationships.
# The SQLCompiler traverses this graph via BFS to find the
# minimal set of JOIN clauses needed for any query.
# ============================================================
JOIN_GRAPH = [
    JoinPath(source="Order", target="DiscountUsageHistory", on_clause="o.Id = duh.OrderId"),
    JoinPath(source="Order", target="ShoppingCartItem", on_clause="sci.CustomerId = o.CustomerId"),
    JoinPath(source="Product", target="Product_ProductTag_Mapping", on_clause="p.Id = pptm.Product_Id"),
    JoinPath(source="Product_ProductTag_Mapping", target="ProductTag", on_clause="pptm.ProductTag_Id = pt.Id"),
    JoinPath(source="Product", target="ProductReview", on_clause="pr.ProductId = p.Id"),
    # Core order relationships
    JoinPath(source="Order", target="Customer", on_clause="o.CustomerId = cu.Id"),
    JoinPath(source="Order", target="OrderItem", on_clause="o.Id = oi.OrderId"),
    JoinPath(source="OrderItem", target="Product", on_clause="oi.ProductId = p.Id"),

    # Product taxonomy
    JoinPath(source="Product", target="Product_Category_Mapping", on_clause="p.Id = pcm.ProductId"),
    JoinPath(source="Product_Category_Mapping", target="Category", on_clause="pcm.CategoryId = c.Id"),

    # Manufacturer
    JoinPath(source="Product", target="Product_Manufacturer_Mapping", on_clause="p.Id = pmm.ProductId"),
    JoinPath(source="Product_Manufacturer_Mapping", target="Manufacturer", on_clause="pmm.ManufacturerId = mf.Id"),

    # Geography (Order → Address → Country)
    JoinPath(source="Order", target="Address", on_clause="o.BillingAddressId = addr.Id"),
    JoinPath(source="Address", target="Country", on_clause="addr.CountryId = co.Id"),

    # Shipping
    JoinPath(source="Order", target="Shipment", on_clause="o.Id = sh.OrderId"),

    # Store
    JoinPath(source="Order", target="Store", on_clause="o.StoreId = st.Id"),
]

# SYNONYMS is intentionally empty.
# Vocabulary injection embeds all approved metric/dimension IDs directly into
# the LLM system prompt, so the LLM performs the synonym mapping at inference
# time.  Maintaining a separate synonym dict would duplicate that knowledge.
SYNONYMS = {}

# ============================================================
# BUSINESS_LOGIC_MAPPINGS — abstract domain terms → SQL predicates.
# Allows users to say "abandoned orders" instead of knowing the
# internal status code. The SemanticMapper expands these before
# SQL compilation.
# ============================================================
BUSINESS_LOGIC_MAPPINGS = {
    "abandoned": {
        "field": "OrderStatusId",
        "operator": "=",
        "value": 40
    },
    "referral_source": {
        "field": "cu.AdminComment",
        "operator": "contains",
        "value": "ref:"
    }
}

# ALIAS_TO_TABLE — reverse lookup from SQL alias → table name.
# Used by the compiler to infer implicit table requirements from
# WHERE-clause expressions that reference aliased columns.
ALIAS_TO_TABLE = {
    "cu": "Customer",
    "o": "Order",
    "oi": "OrderItem",
    "p": "Product",
    "c": "Category",
    "pcm": "Product_Category_Mapping",
    "pmm": "Product_Manufacturer_Mapping",
    "mf": "Manufacturer",
    "addr": "Address",
    "co": "Country",
    "sh": "Shipment",
    "st": "Store",
}
