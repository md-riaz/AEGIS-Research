import random
from datetime import datetime, timedelta

def generate_mock_sql():
    output_file = "mock_data.sql"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("-- SafeDash Mock Data Generator\n")
        f.write("-- Executes against schema.sql\n\n")
        
        # Manufacturers
        f.write("SET IDENTITY_INSERT [Manufacturer] ON;\n")
        f.write("INSERT INTO [Manufacturer] ([Id], [Name]) VALUES \n")
        f.write("(1, 'Apple'),\n(2, 'Samsung'),\n(3, 'Sony'),\n(4, 'Dell');\n")
        f.write("SET IDENTITY_INSERT [Manufacturer] OFF;\n\n")

        # Categories
        f.write("SET IDENTITY_INSERT [Category] ON;\n")
        f.write("INSERT INTO [Category] ([Id], [Name]) VALUES \n")
        f.write("(1, 'Electronics'),\n(2, 'Laptops'),\n(3, 'Smartphones'),\n(4, 'Accessories');\n")
        f.write("SET IDENTITY_INSERT [Category] OFF;\n\n")

        # Products
        f.write("SET IDENTITY_INSERT [Product] ON;\n")
        f.write("INSERT INTO [Product] ([Id], [Name], [Price], [ManufacturerId]) VALUES \n")
        products = [
            (1, "iPhone 15", 999.00, 1),
            (2, "Galaxy S24", 899.00, 2),
            (3, "Sony WH-1000XM5", 349.00, 3),
            (4, "MacBook Pro", 1999.00, 1),
            (5, "Dell XPS 15", 1799.00, 4)
        ]
        prod_strings = [f"({p[0]}, '{p[1]}', {p[2]}, {p[3]})" for p in products]
        f.write(",\n".join(prod_strings) + ";\n")
        f.write("SET IDENTITY_INSERT [Product] OFF;\n\n")

        # Customers
        f.write("SET IDENTITY_INSERT [Customer] ON;\n")
        f.write("INSERT INTO [Customer] ([Id], [Email], [CreatedOnUtc]) VALUES \n")
        customers = []
        now = datetime.utcnow()
        for i in range(1, 51):
            created = (now - timedelta(days=random.randint(10, 100))).strftime("%Y-%m-%d %H:%M:%S")
            customers.append(f"({i}, 'user{i}@example.com', '{created}')")
        f.write(",\n".join(customers) + ";\n")
        f.write("SET IDENTITY_INSERT [Customer] OFF;\n\n")

        # Orders & OrderItems
        f.write("SET IDENTITY_INSERT [Order] ON;\n")
        f.write("INSERT INTO [Order] ([Id], [CustomerId], [OrderTotal], [CreatedOnUtc]) VALUES \n")
        
        orders = []
        order_items = []
        item_id = 1
        
        for order_id in range(1, 201):
            cust_id = random.randint(1, 50)
            created = (now - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d %H:%M:%S")
            
            num_items = random.randint(1, 3)
            total = 0
            for _ in range(num_items):
                prod = random.choice(products)
                qty = random.randint(1, 2)
                price = prod[2]
                total += price * qty
                order_items.append(f"({item_id}, {order_id}, {prod[0]}, {qty}, {price})")
                item_id += 1
                
            orders.append(f"({order_id}, {cust_id}, {total}, '{created}')")
            
        f.write(",\n".join(orders) + ";\n")
        f.write("SET IDENTITY_INSERT [Order] OFF;\n\n")

        f.write("SET IDENTITY_INSERT [OrderItem] ON;\n")
        f.write("INSERT INTO [OrderItem] ([Id], [OrderId], [ProductId], [Quantity], [PriceExclTax]) VALUES \n")
        f.write(",\n".join(order_items) + ";\n")
        f.write("SET IDENTITY_INSERT [OrderItem] OFF;\n\n")

    print(f"Successfully generated {output_file}")

if __name__ == "__main__":
    generate_mock_sql()
