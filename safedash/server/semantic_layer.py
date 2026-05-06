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

# ============================================================
# nopCommerce Truth Schema Semantic Layer Definition
# Schema: 16 tables (extracted from production MSSQL backup)
# ============================================================

METRICS = [
    Metric(
        id="revenue",
        label="Total Revenue",
        description="Sum of order totals excluding refunded amounts",
        sql_expr="SUM(COALESCE(o.OrderTotal, 0) - COALESCE(o.RefundedAmount, 0))",
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
        sql_expr="AVG(COALESCE(o.OrderTotal, 0))",
        binding_table="Order"
    ),
    Metric(
        id="item_quantity",
        label="Quantity Sold",
        description="Total number of items sold",
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
]

DIMENSIONS = [
    # --- Product dimensions ---
    Dimension(
        id="product_name",
        label="Product Name",
        description="Name of the product",
        sql_expr="p.Name",
        binding_table="Product",
        datatype="string"
    ),
    Dimension(
        id="product_sku",
        label="Product SKU",
        description="Stock keeping unit code",
        sql_expr="p.Sku",
        binding_table="Product",
        datatype="string"
    ),
    Dimension(
        id="product_price",
        label="Product Price",
        description="Current listed price of the product",
        sql_expr="p.Price",
        binding_table="Product",
        datatype="number"
    ),
    Dimension(
        id="product_cost",
        label="Product Cost",
        description="Manufacturing/acquisition cost of the product",
        sql_expr="p.ProductCost",
        binding_table="Product",
        datatype="number"
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
        description="Number of approved customer reviews",
        sql_expr="p.ApprovedTotalReviews",
        binding_table="Product",
        datatype="number"
    ),
    Dimension(
        id="product_published",
        label="Product Published",
        description="Whether the product is published (1=yes, 0=no)",
        sql_expr="p.Published",
        binding_table="Product",
        datatype="number"
    ),
    Dimension(
        id="product_created_date",
        label="Product Created Date",
        description="Date product was added to catalog",
        sql_expr="p.CreatedOnUtc",
        binding_table="Product",
        datatype="date"
    ),

    # --- Category dimension ---
    Dimension(
        id="category_name",
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
        label="Customer Name",
        description="Full name of the customer (FirstName LastName)",
        sql_expr="CONCAT(cu.FirstName, ' ', cu.LastName)",
        binding_table="Customer",
        datatype="string"
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
        id="customer_active",
        label="Customer Active",
        description="Whether customer account is active (1=yes, 0=no)",
        sql_expr="cu.Active",
        binding_table="Customer",
        datatype="number"
    ),
    Dimension(
        id="customer_registration_date",
        label="Customer Registration Date",
        description="Date customer registered",
        sql_expr="cu.CreatedOnUtc",
        binding_table="Customer",
        datatype="date"
    ),

    # --- Order dimensions ---
    Dimension(
        id="order_id",
        label="Order ID",
        description="Unique identifier of the order",
        sql_expr="o.Id",
        binding_table="Order",
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
        id="order_month",
        label="Order Month",
        description="Month when order was placed (YYYY-MM format)",
        sql_expr="DATE_FORMAT(o.CreatedOnUtc, '%Y-%m')",
        binding_table="Order",
        datatype="string"
    ),
    Dimension(
        id="order_year",
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
        label="Order Status",
        description="Human-readable order status (Pending, Processing, Complete, Cancelled)",
        sql_expr="CASE o.OrderStatusId WHEN 10 THEN 'Pending' WHEN 20 THEN 'Processing' WHEN 30 THEN 'Complete' WHEN 40 THEN 'Cancelled' ELSE 'Unknown' END",
        binding_table="Order",
        datatype="string"
    ),
    Dimension(
        id="payment_status",
        label="Payment Status",
        description="Human-readable payment status (Pending, Authorized, Paid, PartiallyRefunded, Refunded, Voided)",
        sql_expr="CASE o.PaymentStatusId WHEN 10 THEN 'Pending' WHEN 20 THEN 'Authorized' WHEN 30 THEN 'Paid' WHEN 35 THEN 'PartiallyRefunded' WHEN 40 THEN 'Refunded' WHEN 50 THEN 'Voided' ELSE 'Unknown' END",
        binding_table="Order",
        datatype="string"
    ),
    Dimension(
        id="shipping_status",
        label="Shipping Status",
        description="Human-readable shipping status (Not Required, Not Yet Shipped, Shipped, Delivered)",
        sql_expr="CASE o.ShippingStatusId WHEN 10 THEN 'Not Required' WHEN 20 THEN 'Not Yet Shipped' WHEN 30 THEN 'Shipped' WHEN 40 THEN 'Delivered' WHEN 50 THEN 'Partially Shipped' ELSE 'Unknown' END",
        binding_table="Order",
        datatype="string"
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
        id="currency_code",
        label="Currency",
        description="Currency code used for the order",
        sql_expr="o.CustomerCurrencyCode",
        binding_table="Order",
        datatype="string"
    ),
    Dimension(
        id="shipping_method",
        label="Shipping Method",
        description="Shipping method chosen for the order",
        sql_expr="o.ShippingMethod",
        binding_table="Order",
        datatype="string"
    ),
    Dimension(
        id="order_number",
        label="Order Number",
        description="Custom order number (e.g. ORD-00001)",
        sql_expr="o.CustomOrderNumber",
        binding_table="Order",
        datatype="string"
    ),

    # --- Geography dimensions (via Address → Country) ---
    Dimension(
        id="country_name",
        label="Billing Country",
        description="Country name from the billing address",
        sql_expr="co.Name",
        binding_table="Country",
        datatype="string",
        required_joins=["Address", "Country"]
    ),
    Dimension(
        id="billing_city",
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
        label="Tracking Number",
        description="Shipment tracking number",
        sql_expr="sh.TrackingNumber",
        binding_table="Shipment",
        datatype="string",
        required_joins=["Shipment"]
    ),
    Dimension(
        id="shipped_date",
        label="Shipped Date",
        description="Date the shipment was dispatched",
        sql_expr="sh.ShippedDateUtc",
        binding_table="Shipment",
        datatype="date",
        required_joins=["Shipment"]
    ),
    Dimension(
        id="delivery_date",
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
        label="Store",
        description="Store name for multi-store setups",
        sql_expr="st.Name",
        binding_table="Store",
        datatype="string",
        required_joins=["Store"]
    ),
]

# ============================================================
# JOIN GRAPH — 14 tables, 12 join paths
# ============================================================
JOIN_GRAPH = [
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
        "field": "o.Id",
        "operator": "is_not_null",
        "value": True
    },
    "referral_source": {
        "field": "cu.AdminComment",
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
    "pcm": "Product_Category_Mapping",
    "pmm": "Product_Manufacturer_Mapping",
    "mf": "Manufacturer",
    "addr": "Address",
    "co": "Country",
    "sh": "Shipment",
    "st": "Store",
}
