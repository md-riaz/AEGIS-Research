import random
import datetime
import uuid

def generate():
    sql = []
    sql.append("-- AEGIS Mock Data — Full nopCommerce Schema")
    sql.append("-- Executes against database/schema.sql")
    sql.append("")

    def batch_insert(table, columns, rows, batch_size=200):
        if not rows: return
        cols_str = ",".join([f"`{c}`" for c in columns])
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            values_list = []
            for row in batch:
                vals = []
                for v in row:
                    if v is None: vals.append("NULL")
                    elif isinstance(v, str): 
                        esc = v.replace("'", "''")
                        vals.append(f"'{esc}'")
                    else: vals.append(str(v))
                values_list.append(f"({','.join(vals)})")
            sql.append(f"INSERT INTO `{table}` ({cols_str}) VALUES {','.join(values_list)};")

    sql.append("-- AEGIS Mock Data — Full nopCommerce Schema")
    sql.append("-- Executes against database/schema.sql")
    sql.append("SET FOREIGN_KEY_CHECKS=0;")
    sql.append("START TRANSACTION;")
    sql.append("")

    # ============================================================
    # COUNTRIES
    # ============================================================
    countries_data = [
        (1, "Bangladesh", "BD", "BGD", 50),
        (2, "India", "IN", "IND", 356),
        (3, "United States", "US", "USA", 840),
        (4, "United Kingdom", "GB", "GBR", 826),
        (5, "Australia", "AU", "AUS", 36),
        (6, "Canada", "CA", "CAN", 124),
        (7, "Germany", "DE", "DEU", 276),
        (8, "Japan", "JP", "JPN", 392),
    ]
    batch_insert("Country", ["Id", "Name", "TwoLetterIsoCode", "ThreeLetterIsoCode", "NumericIsoCode"], countries_data)
    sql.append("")

    # ============================================================
    # STATE PROVINCES (sample)
    # ============================================================
    states_data = [
        (1, 1, "Dhaka"), (2, 1, "Chattogram"), (3, 1, "Sylhet"), (4, 1, "Rajshahi"),
        (5, 2, "Maharashtra"), (6, 2, "Karnataka"), (7, 2, "Delhi"),
        (8, 3, "California"), (9, 3, "New York"), (10, 3, "Texas"),
        (11, 4, "England"), (12, 4, "Scotland"),
    ]
    batch_insert("StateProvince", ["Id", "CountryId", "Name"], states_data)
    sql.append("")

    # ============================================================
    # STORE
    # ============================================================
    sql.append("INSERT INTO `Store` (`Id`,`Name`,`Url`,`SslEnabled`,`CompanyName`) VALUES (1,'AEGIS Demo Store','https://demo.aegis.io',1,'AEGIS Ltd.');")
    sql.append("")

    # ============================================================
    # ADDRESSES
    # ============================================================
    address_id = 1
    cities_by_country = {
        1: ["Dhaka", "Chattogram", "Sylhet", "Rajshahi", "Khulna"],
        2: ["Mumbai", "Bangalore", "Delhi", "Chennai"],
        3: ["San Francisco", "New York", "Austin", "Seattle"],
        4: ["London", "Manchester", "Edinburgh"],
        5: ["Sydney", "Melbourne"],
        6: ["Toronto", "Vancouver"],
        7: ["Berlin", "Munich"],
        8: ["Tokyo", "Osaka"],
    }
    first_names = ["Rahim", "Karim", "Farhan", "Aisha", "Nusrat", "Tanvir", "Sadia", "Mariam", "Imran", "Rashid",
                   "John", "Jane", "David", "Sarah", "Michael", "Emily", "James", "Emma", "Robert", "Olivia"]
    last_names = ["Ahmed", "Islam", "Khan", "Rahman", "Hossain", "Akter", "Begum", "Uddin", "Chowdhury", "Ali",
                  "Smith", "Johnson", "Williams", "Brown", "Jones", "Davis", "Miller", "Wilson", "Moore", "Taylor"]

    addresses = []
    for i in range(1, 1501):
        cid = random.choices([1,1,1,1,2,3,4,5,6,7,8], weights=[50,50,50,50,15,10,8,3,3,3,3])[0]
        city = random.choice(cities_by_country[cid])
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        email = f"{fn.lower()}.{ln.lower()}{i}@example.com"
        dt = datetime.datetime(random.choice([2023,2024,2025,2026]), random.randint(1,12), random.randint(1,28), 10, 0, 0)
        if dt.year == 2026 and dt.month > 5:
            dt = dt.replace(month=random.randint(1,5))
        addresses.append((i, fn, ln, email, cid, city, dt))

    address_rows = []
    for addr in addresses:
        # i, fn, ln, email, cid, city, dt
        address_rows.append((addr[0], addr[1], addr[2], addr[3], addr[4], addr[5], addr[6].strftime('%Y-%m-%d %H:%M:%S')))
    batch_insert("Address", ["Id", "FirstName", "LastName", "Email", "CountryId", "City", "CreatedOnUtc"], address_rows)
    sql.append("")

    # ============================================================
    # CATEGORIES
    # ============================================================
    categories = [
        (1, "Electronics", 0),
        (2, "Laptops", 1),
        (3, "Smartphones", 1),
        (4, "Accessories", 1),
        (5, "Apparel", 0),
        (6, "Home Appliances", 0),
        (7, "Books", 0),
        (8, "Toys & Games", 0),
    ]
    now = datetime.datetime(2024, 1, 1, 0, 0, 0)
    cat_rows = []
    for cid, name, parent in categories:
        cat_rows.append((cid, name, parent, now.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d %H:%M:%S')))
    batch_insert("Category", ["Id", "Name", "ParentCategoryId", "CreatedOnUtc", "UpdatedOnUtc"], cat_rows)
    sql.append("")

    # ============================================================
    # MANUFACTURERS
    # ============================================================
    manufacturers = [
        (1, "Apple"), (2, "Samsung"), (3, "Sony"), (4, "Dell"),
        (5, "Nike"), (6, "Walton"), (7, "Logitech"), (8, "Lego"),
    ]
    mfg_rows = []
    for mid, name in manufacturers:
        mfg_rows.append((mid, name, now.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d %H:%M:%S')))
    batch_insert("Manufacturer", ["Id", "Name", "CreatedOnUtc", "UpdatedOnUtc"], mfg_rows)
    sql.append("")

    # ============================================================
    # PRODUCTS (BDT prices — realistic)
    # ============================================================
    #  (name, stock, reviews, price, cost, sku, manufacturer_id, category_id)
    products = [
        ("iPhone 15 Pro",        150, 120, 150000, 120000, "APPL-IPH15P", 1, 3),
        ("Galaxy S24 Ultra",     200,  85, 140000, 105000, "SAMS-GS24U",  2, 3),
        ("Sony WH-1000XM5",      50, 300,  35000,  22000, "SONY-WH1K5",  3, 4),
        ("MacBook Pro 16",        10,  45, 280000, 230000, "APPL-MBP16",  1, 2),
        ("Dell XPS 15",           15,  60, 220000, 170000, "DELL-XPS15",  4, 2),
        ("Polo T-Shirt",         500,  10,   1200,    600, "APRL-POLO1",  0, 5),
        ("Jeans Pant",           300,  20,   2500,   1200, "APRL-JEAN1",  0, 5),
        ("Nike Air Max",         100,  55,  15000,   9000, "NIKE-AIRM1",  5, 5),
        ("Walton Refrigerator",   40,  15,  45000,  32000, "WALT-REF01",  6, 6),
        ("Vision Smart TV 55",    60,  80,  55000,  38000, "VISN-TV055",  0, 6),
        ("Logitech MX Master 3S",120, 200,  12000,   7500, "LOGI-MXM3S",  7, 4),
        ("Apple AirPods Pro",     80, 150,  28000,  18000, "APPL-APP02",  1, 4),
        ("Samsung Microwave",     70,  30,  18000,  12000, "SAMS-MW001",  2, 6),
        ("Clean Code Book",      200, 400,    800,    400, "BOOK-CC001",  0, 7),
        ("Lego Star Wars",        90,  50,   8500,   5500, "LEGO-SW001",  8, 8),
        ("Rolex Watch Replica",    0,   0,   5000,   2000, "MISC-RWR01",  0, 4),  # Never sold
        ("Old Nokia 3310",         0,   0,   1500,    800, "MISC-NK331",  0, 3),  # Never sold
    ]
    product_rows = []
    for i, (name, stock, reviews, price, cost, sku, mfg_id, cat_id) in enumerate(products, 1):
        pdt = datetime.datetime(2024, random.randint(1,6), random.randint(1,28), 10, 0, 0)
        product_rows.append((i, name, sku, price, int(price*1.15), cost, stock, 5, reviews, 1, pdt.strftime('%Y-%m-%d %H:%M:%S'), pdt.strftime('%Y-%m-%d %H:%M:%S')))
    batch_insert("Product", ["Id", "Name", "Sku", "Price", "OldPrice", "ProductCost", "StockQuantity", "MinStockQuantity", "ApprovedTotalReviews", "Published", "CreatedOnUtc", "UpdatedOnUtc"], product_rows)
    # Mark never-sold as unpublished
    sql.append("UPDATE `Product` SET `Published`=0 WHERE `Id` IN (16,17);")
    sql.append("")

    # ============================================================
    # PRODUCT_CATEGORY_MAPPING
    # ============================================================
    pcm = [(1,3),(2,3),(3,4),(4,2),(5,2),(6,5),(7,5),(8,5),(9,6),(10,6),(11,4),(12,4),(13,6),(14,7),(15,8),(16,4),(17,3)]
    pcm_rows = []
    for i, (pid, cid) in enumerate(pcm, 1):
        pcm_rows.append((i, pid, cid))
    batch_insert("Product_Category_Mapping", ["Id", "ProductId", "CategoryId"], pcm_rows)
    sql.append("")

    # ============================================================
    # PRODUCT_MANUFACTURER_MAPPING
    # ============================================================
    pmm_id = 1
    pmm_rows = []
    for i, (name, stock, reviews, price, cost, sku, mfg_id, cat_id) in enumerate(products, 1):
        if mfg_id > 0:
            pmm_rows.append((pmm_id, i, mfg_id))
            pmm_id += 1
    batch_insert("Product_Manufacturer_Mapping", ["Id", "ProductId", "ManufacturerId"], pmm_rows)
    sql.append("")

    # ============================================================
    # CUSTOMERS (1200)
    # ============================================================
    customer_addresses = []  # (customer_id, billing_address_id)
    customer_rows = []
    for i in range(1, 1201):
        addr = addresses[i - 1]
        fn, ln, email, country_id = addr[1], addr[2], addr[3], addr[4]
        year = random.choice([2024, 2025, 2026])
        month = random.randint(1, 12) if year < 2026 else random.randint(1, 5)
        day = random.randint(1, 28)
        cdt = datetime.datetime(year, month, day, random.randint(0,23), random.randint(0,59), random.randint(0,59))
        active = 1 if random.random() > 0.03 else 0
        guid = str(uuid.uuid4())
        customer_addresses.append((i, i))
        customer_rows.append((i, guid, email, fn, ln, country_id, active, cdt.strftime('%Y-%m-%d %H:%M:%S'), cdt.strftime('%Y-%m-%d %H:%M:%S'), 1, i))
    batch_insert("Customer", ["Id", "CustomerGuid", "Email", "FirstName", "LastName", "CountryId", "Active", "CreatedOnUtc", "LastActivityDateUtc", "RegisteredInStoreId", "BillingAddressId"], customer_rows)
    sql.append("")

    # ============================================================
    # ORDERS (2500)
    # ============================================================
    # ============================================================
    # ORDERS (2500)
    # ============================================================
    order_item_id = 1
    shipment_id = 1
    shipment_item_id = 1
    payment_methods = ["Payments.bKash", "Payments.bKash", "Payments.Nagad", "Payments.Manual", "Payments.CashOnDelivery"]

    order_rows = []
    oi_rows = []
    ship_rows = []
    si_rows = []

    for i in range(1, 2501):
        cust_id = random.randint(1, 1200)
        billing_addr_id = cust_id
        year = random.choice([2024, 2025, 2026, 2026])
        month = random.randint(1, 12) if year < 2026 else random.randint(1, 5)
        day = random.randint(1, 28)
        odt = datetime.datetime(year, month, day, random.randint(0,23), random.randint(0,59), random.randint(0,59))
        num_items = random.randint(1, 4)
        total_subtotal = 0
        total_cost = 0
        item_ids_this_order = []

        for _ in range(num_items):
            prod_idx = random.randint(0, len(products) - 3)
            prod_id = prod_idx + 1
            qty = random.randint(1, 3)
            price, cost = products[prod_idx][3], products[prod_idx][4]
            line_price, orig_cost = price * qty, cost * qty
            line_disc = random.choice([0, 0, 0, int(line_price * 0.05)]) if line_price > 5000 else 0
            total_subtotal += line_price
            total_cost += orig_cost
            oig = str(uuid.uuid4())
            oi_rows.append((order_item_id, oig, i, prod_id, qty, price, price, line_price, line_price, line_disc, line_disc, orig_cost))
            item_ids_this_order.append(order_item_id)
            order_item_id += 1

        discount = random.choice([0, 0, 500, 1000, 2000]) if total_subtotal > 10000 else random.choice([0, 0, 100])
        shipping_excl = random.choice([60, 120, 150])
        tax = int(total_subtotal * 0.05)
        refund = total_subtotal if random.random() > 0.95 else 0
        order_total = total_subtotal + tax + shipping_excl - discount
        status, payment_status, shipping_status = random.choice([10,20,30,30,30,40]), random.choice([10,20,30,30,30]), random.choice([10,20,30,30,40])
        currency = random.choices(["BDT","BDT","BDT","USD","GBP","INR"], weights=[60,60,60,10,5,5])[0]
        pm, paid_dt = random.choice(payment_methods), odt.strftime('%Y-%m-%d %H:%M:%S') if payment_status == 30 else None
        order_rows.append((i, str(uuid.uuid4()), 1, cust_id, billing_addr_id, status, shipping_status, payment_status, pm, currency, 1.0, total_subtotal + tax, total_subtotal, shipping_excl, shipping_excl, tax, discount, order_total, refund, paid_dt, 'Ground', odt.strftime('%Y-%m-%d %H:%M:%S'), f'ORD-{i:05d}'))

        if shipping_status in (30, 40):
            ship_dt = odt + datetime.timedelta(days=random.randint(1, 3))
            del_dt = ship_dt + datetime.timedelta(days=random.randint(1, 5)) if shipping_status == 40 else None
            ship_rows.append((shipment_id, i, f'TRK{i:06d}', ship_dt.strftime('%Y-%m-%d %H:%M:%S'), del_dt.strftime('%Y-%m-%d %H:%M:%S') if del_dt else None, ship_dt.strftime('%Y-%m-%d %H:%M:%S')))
            for oi_id in item_ids_this_order:
                si_rows.append((shipment_item_id, shipment_id, oi_id, 1))
                shipment_item_id += 1
            shipment_id += 1

    batch_insert("Order", ["Id", "OrderGuid", "StoreId", "CustomerId", "BillingAddressId", "OrderStatusId", "ShippingStatusId", "PaymentStatusId", "PaymentMethodSystemName", "CustomerCurrencyCode", "CurrencyRate", "OrderSubtotalInclTax", "OrderSubtotalExclTax", "OrderShippingInclTax", "OrderShippingExclTax", "OrderTax", "OrderDiscount", "OrderTotal", "RefundedAmount", "PaidDateUtc", "ShippingMethod", "CreatedOnUtc", "CustomOrderNumber"], order_rows)
    sql.append("")
    batch_insert("OrderItem", ["Id", "OrderItemGuid", "OrderId", "ProductId", "Quantity", "UnitPriceInclTax", "UnitPriceExclTax", "PriceInclTax", "PriceExclTax", "DiscountAmountInclTax", "DiscountAmountExclTax", "OriginalProductCost"], oi_rows)
    sql.append("")
    batch_insert("Shipment", ["Id", "OrderId", "TrackingNumber", "ShippedDateUtc", "DeliveryDateUtc", "CreatedOnUtc"], ship_rows)
    sql.append("")
    batch_insert("ShipmentItem", ["Id", "ShipmentId", "OrderItemId", "Quantity"], si_rows)

    sql.append("")
    sql.append("COMMIT;")
    sql.append("SET FOREIGN_KEY_CHECKS=1;")

    with open('database/mock_data.sql', 'w') as f:
        f.write('\n'.join(sql))

    print(f"Generated mock data:")
    print(f"  Countries: {len(countries_data)}")
    print(f"  States: {len(states_data)}")
    print(f"  Addresses: 1500")
    print(f"  Categories: {len(categories)}")
    print(f"  Manufacturers: {len(manufacturers)}")
    print(f"  Products: {len(products)}")
    print(f"  Customers: 1200")
    print(f"  Orders: 2500")
    print(f"  OrderItems: {order_item_id - 1}")
    print(f"  Shipments: {shipment_id - 1}")
    print(f"  ShipmentItems: {shipment_item_id - 1}")

if __name__ == '__main__':
    generate()
