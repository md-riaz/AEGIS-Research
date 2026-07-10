# NopCommerce Database Analysis for AEGIS Integration

## Overview
This document analyzes the nopCommerce database schema and outlines the strategy for mapping its core tables to the AEGIS semantic layer. The goal is to prove that AEGIS can autonomously generate standard analytical reports typically built manually by developers.

## Core nopCommerce Tables

1. **Order**
   - **Fields:** `Id`, `OrderTotal`, `OrderSubtotalInclTax`, `CustomerId`, `CreatedOnUtc`, `OrderStatusId`, `PaymentStatusId`, `ShippingStatusId`, `StoreId`, `Deleted`
   - **Purpose:** Core transaction table for all sales, revenue, and order status tracking.

2. **OrderItem**
   - **Fields:** `Id`, `OrderId`, `ProductId`, `Quantity`, `PriceInclTax`, `DiscountAmountInclTax`
   - **Purpose:** Line items within an order. Needed for product-level sales metrics (Bestsellers).

3. **Customer**
   - **Fields:** `Id`, `Email`, `CreatedOnUtc`, `Active`, `Deleted`, `RegisteredInStoreId`
   - **Purpose:** Customer tracking, segmentation, and analyzing top buyers.

4. **Product**
   - **Fields:** `Id`, `Name`, `ManageInventoryMethodId`, `StockQuantity`, `Published`, `Deleted`
   - **Purpose:** Product dimension, stock tracking (Low Stock reports).

5. **Address / Country**
   - **Fields:** `CountryId`, `Name`
   - **Purpose:** Used for Geographic/Country sales reports.

## Mapping nopCommerce to AEGIS Semantic Layer

To run AEGIS against this schema without developer intervention, the `semantic_layer.py` must define entities matching these tables:

### 1. `orders` entity
Maps to the nopCommerce `Order` table.
- **Metrics:** `SUM(OrderTotal)` as `total_revenue`, `COUNT(Id)` as `order_count`
- **Dimensions:** `CreatedOnUtc` (date), `OrderStatusId`, `PaymentStatusId`
- **Filters:** `Deleted = 0`

### 2. `order_items` entity
Maps to `OrderItem` joined with `Order`.
- **Metrics:** `SUM(Quantity)` as `items_sold`
- **Dimensions:** `ProductId`

### 3. `customers` entity
Maps to `Customer` table.
- **Metrics:** `COUNT(Id)` as `customer_count`
- **Dimensions:** `CreatedOnUtc`

### 4. `products` entity
Maps to `Product` table.
- **Metrics:** `SUM(StockQuantity)` as `total_stock`
- **Dimensions:** `Id`, `Name`

## Emulating Existing nopCommerce Reports

nopCommerce includes 8 standard reports out-of-the-box. AEGIS can dynamically generate the SQL for each using its semantic layer:

| nopCommerce Report | AEGIS Semantic Translation (Natural Language equivalent) | Required Tables |
| :--- | :--- | :--- |
| **Sales Summary** | "Show total revenue and order count grouped by date" | `Order` |
| **Bestsellers** | "Show total quantity sold by product name" | `OrderItem` JOIN `Product` |
| **Low Stock** | "Show products where stock quantity is less than minimum" | `Product` |
| **Never Sold** | "Show products with 0 items sold" | `Product` LEFT JOIN `OrderItem` |
| **Country Sales** | "Show total revenue grouped by billing country" | `Order` JOIN `Address` JOIN `Country` |
| **Registered Customers** | "Show count of customers grouped by creation date" | `Customer` |
| **Best Customers by Total**| "Show top customers by total order amount" | `Customer` JOIN `Order` |
| **Best Customers by Orders**|"Show top customers by order count" | `Customer` JOIN `Order` |

## Next Steps
1. Update `aegis/server/semantic_layer.py` to register the nopCommerce tables, joins, and metric definitions.
2. Update the `mock_data.sql` to represent a valid subset of the nopCommerce schema for testing.
3. Verify that the AEGIS SQL compiler generates correct nopCommerce queries and runs the benchmark cleanly.
