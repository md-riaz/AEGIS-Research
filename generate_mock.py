import random
import datetime

def generate():
    sql = []
    sql.append("-- SafeDash Mock Data Generator")
    sql.append("-- Executes against schema.sql")
    sql.append("")
    
    # Categories
    sql.append("SET IDENTITY_INSERT [Category] ON;")
    categories = ["Electronics", "Laptops", "Smartphones", "Accessories", "Apparel"]
    for i, c in enumerate(categories, 1):
        sql.append(f"INSERT INTO [Category] ([Id], [Name]) VALUES ({i}, '{c}');")
    sql.append("SET IDENTITY_INSERT [Category] OFF;")
    sql.append("")

    # Products
    sql.append("SET IDENTITY_INSERT [Product] ON;")
    products = [
        ("iPhone 15", 150, 120),
        ("Galaxy S24", 200, 85),
        ("Sony WH-1000XM5", 50, 300),
        ("MacBook Pro", 10, 45),
        ("Dell XPS 15", 15, 60),
        ("T-Shirt", 500, 10)
    ]
    for i, (name, stock, reviews) in enumerate(products, 1):
        sql.append(f"INSERT INTO [Product] ([Id], [Name], [StockQuantity], [ApprovedTotalReviews]) VALUES ({i}, '{name}', {stock}, {reviews});")
    sql.append("SET IDENTITY_INSERT [Product] OFF;")
    sql.append("")

    # Product_Category_Mapping
    sql.append("SET IDENTITY_INSERT [Product_Category_Mapping] ON;")
    mappings = [(1, 3), (2, 3), (3, 1), (3, 4), (4, 2), (5, 2), (6, 5)]
    for i, (pid, cid) in enumerate(mappings, 1):
        sql.append(f"INSERT INTO [Product_Category_Mapping] ([Id], [ProductId], [CategoryId]) VALUES ({i}, {pid}, {cid});")
    sql.append("SET IDENTITY_INSERT [Product_Category_Mapping] OFF;")
    sql.append("")

    # Customers
    sql.append("SET IDENTITY_INSERT [Customer] ON;")
    for i in range(1, 51):
        dt = datetime.datetime(2026, random.randint(1, 4), random.randint(1, 28), 9, 4, 43)
        sql.append(f"INSERT INTO [Customer] ([Id], [Email], [CreatedOnUtc]) VALUES ({i}, 'user{i}@example.com', '{dt.strftime('%Y-%m-%d %H:%M:%S')}');")
    sql.append("SET IDENTITY_INSERT [Customer] OFF;")
    sql.append("")

    # Orders
    sql.append("SET IDENTITY_INSERT [Order] ON;")
    order_items_sql = []
    order_items_sql.append("SET IDENTITY_INSERT [OrderItem] ON;")
    
    order_item_id = 1
    countries = ["US", "CA", "UK", "AU", "DE"]
    payment_methods = ["CreditCard", "PayPal", "BankTransfer"]
    
    for i in range(1, 201):
        cust_id = random.randint(1, 50)
        dt = datetime.datetime(2026, random.randint(3, 5), random.randint(1, 28), 9, 4, 43)
        
        num_items = random.randint(1, 3)
        total_subtotal = 0
        
        for _ in range(num_items):
            prod_id = random.randint(1, len(products))
            qty = random.randint(1, 2)
            price = random.choice([349.0, 899.0, 999.0, 1799.0, 1999.0])
            total_subtotal += price * qty
            
            order_items_sql.append(f"INSERT INTO [OrderItem] ([Id], [OrderId], [ProductId], [Quantity], [PriceExclTax]) VALUES ({order_item_id}, {i}, {prod_id}, {qty}, {price});")
            order_item_id += 1
            
        discount = random.choice([0, 0, 10, 20])
        shipping = random.choice([0, 10, 15])
        refund = random.choice([0, 0, 0, total_subtotal]) if random.random() > 0.9 else 0
        order_total = total_subtotal - discount + shipping
        
        status = random.choice([10, 20, 30, 40])
        payment_status = random.choice([10, 20, 30])
        shipping_status = random.choice([10, 20, 30])
        country = random.choice(countries)
        pm = random.choice(payment_methods)
        
        sql.append(f"INSERT INTO [Order] ([Id], [CustomerId], [OrderTotal], [RefundedAmount], [OrderShipping], [OrderDiscount], [OrderSubtotalExclTax], [OrderStatusId], [PaymentStatusId], [ShippingStatusId], [PaymentMethodSystemName], [BillingCountry], [CreatedOnUtc]) VALUES ({i}, {cust_id}, {order_total}, {refund}, {shipping}, {discount}, {total_subtotal}, {status}, {payment_status}, {shipping_status}, '{pm}', '{country}', '{dt.strftime('%Y-%m-%d %H:%M:%S')}');")
        
    sql.append("SET IDENTITY_INSERT [Order] OFF;")
    sql.append("")
    
    order_items_sql.append("SET IDENTITY_INSERT [OrderItem] OFF;")
    sql.extend(order_items_sql)
    
    with open('database/mock_data.sql', 'w') as f:
        f.write('\n'.join(sql))

if __name__ == '__main__':
    generate()
