import random
import datetime

def generate():
    sql = []
    sql.append("-- SafeDash Mock Data Generator")
    sql.append("-- Executes against schema.sql")
    sql.append("")
    
    # Categories
    categories = ["Electronics", "Laptops", "Smartphones", "Accessories", "Apparel", "Home Appliances", "Books", "Toys"]
    for i, c in enumerate(categories, 1):
        sql.append(f"INSERT INTO `Category` (`Id`, `Name`) VALUES ({i}, '{c}');")
    sql.append("")

    # Products (realistic BDT prices)
    products = [
        ("iPhone 15 Pro", 150, 120, 150000),
        ("Galaxy S24 Ultra", 200, 85, 140000),
        ("Sony WH-1000XM5", 50, 300, 35000),
        ("MacBook Pro 16", 10, 45, 280000),
        ("Dell XPS 15", 15, 60, 220000),
        ("Polo T-Shirt", 500, 10, 1200),
        ("Jeans Pant", 300, 20, 2500),
        ("Nike Air Max", 100, 55, 15000),
        ("Walton Refrigerator", 40, 15, 45000),
        ("Vision Smart TV 55", 60, 80, 55000),
        ("Logitech MX Master 3S", 120, 200, 12000),
        ("Apple AirPods Pro", 80, 150, 28000),
        ("Samsung Microwave", 70, 30, 18000),
        ("Clean Code Book", 200, 400, 800),
        ("Lego Star Wars", 90, 50, 8500),
        ("Rolex Watch Replica", 0, 0, 5000), # Never sold / 0 stock
        ("Old Nokia 3310", 0, 0, 1500) # Never sold
    ]
    for i, (name, stock, reviews, base_price) in enumerate(products, 1):
        sql.append(f"INSERT INTO `Product` (`Id`, `Name`, `StockQuantity`, `ApprovedTotalReviews`) VALUES ({i}, '{name}', {stock}, {reviews});")
    sql.append("")

    # Product_Category_Mapping
    mappings = [(1, 3), (2, 3), (3, 4), (4, 2), (5, 2), (6, 5), (7, 5), (8, 5), (9, 6), (10, 6), (11, 4), (12, 4), (13, 6), (14, 7), (15, 8), (16, 4), (17, 3)]
    for i, (pid, cid) in enumerate(mappings, 1):
        sql.append(f"INSERT INTO `Product_Category_Mapping` (`Id`, `ProductId`, `CategoryId`) VALUES ({i}, {pid}, {cid});")
    sql.append("")

    # Customers (1200 customers)
    for i in range(1, 1201):
        year = random.choice([2024, 2025, 2026])
        month = random.randint(1, 12) if year < 2026 else random.randint(1, 5)
        day = random.randint(1, 28)
        dt = datetime.datetime(year, month, day, random.randint(0, 23), random.randint(0, 59), random.randint(0, 59))
        sql.append(f"INSERT INTO `Customer` (`Id`, `Email`, `CreatedOnUtc`) VALUES ({i}, 'customer{i}@example.com', '{dt.strftime('%Y-%m-%d %H:%M:%S')}');")
    sql.append("")

    # Orders (2500 orders)
    order_items_sql = []
    
    order_item_id = 1
    countries = ["Bangladesh", "Bangladesh", "Bangladesh", "Bangladesh", "India", "USA", "UK"] # BDT context means mostly BD
    payment_methods = ["bKash", "bKash", "Nagad", "CreditCard", "CashOnDelivery"]
    
    for i in range(1, 2501):
        cust_id = random.randint(1, 1200)
        
        # Determine order date
        year = random.choice([2024, 2025, 2026, 2026])
        month = random.randint(1, 12) if year < 2026 else random.randint(1, 5)
        day = random.randint(1, 28)
        dt = datetime.datetime(year, month, day, random.randint(0, 23), random.randint(0, 59), random.randint(0, 59))
        
        num_items = random.randint(1, 4)
        total_subtotal = 0
        
        for _ in range(num_items):
            prod_id = random.randint(1, len(products) - 2) # Exclude the last two "never sold" products
            qty = random.randint(1, 3)
            price = products[prod_id - 1][3] # Get realistic price
            total_subtotal += price * qty
            
            order_items_sql.append(f"INSERT INTO `OrderItem` (`Id`, `OrderId`, `ProductId`, `Quantity`, `PriceExclTax`) VALUES ({order_item_id}, {i}, {prod_id}, {qty}, {price});")
            order_item_id += 1
            
        discount = random.choice([0, 0, 500, 1000, 2000]) if total_subtotal > 10000 else random.choice([0, 0, 100])
        shipping = random.choice([60, 120])
        refund = random.choice([0, 0, 0, 0, 0, total_subtotal]) if random.random() > 0.95 else 0
        order_total = total_subtotal - discount + shipping
        
        status = random.choice([10, 20, 30, 30, 30, 40])
        payment_status = random.choice([10, 20, 30, 30, 30])
        shipping_status = random.choice([10, 20, 30, 30, 30])
        country = random.choice(countries)
        pm = random.choice(payment_methods)
        
        sql.append(f"INSERT INTO `Order` (`Id`, `CustomerId`, `OrderTotal`, `RefundedAmount`, `OrderShipping`, `OrderDiscount`, `OrderSubtotalExclTax`, `OrderStatusId`, `PaymentStatusId`, `ShippingStatusId`, `PaymentMethodSystemName`, `BillingCountry`, `CreatedOnUtc`) VALUES ({i}, {cust_id}, {order_total}, {refund}, {shipping}, {discount}, {total_subtotal}, {status}, {payment_status}, {shipping_status}, '{pm}', '{country}', '{dt.strftime('%Y-%m-%d %H:%M:%S')}');")
        
    sql.append("")
    
    sql.extend(order_items_sql)
    
    with open('database/mock_data.sql', 'w') as f:
        f.write('\n'.join(sql))
        
    print(f"Generated {len(sql)} SQL statements with 1200 customers, 2500 orders and {order_item_id-1} order items.")

if __name__ == '__main__':
    generate()
