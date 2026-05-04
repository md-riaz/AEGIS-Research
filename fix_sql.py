import re

# Fix schema.sql
with open('database/schema.sql', 'r') as f:
    schema = f.read()

schema = schema.replace('[', '`').replace(']', '`')
schema = schema.replace('IDENTITY(1,1)', 'AUTO_INCREMENT')
schema = schema.replace('NVARCHAR', 'VARCHAR')

with open('database/schema.sql', 'w') as f:
    f.write(schema)

# Fix mock_data.sql
with open('database/mock_data.sql', 'r') as f:
    mock_data = f.read()

mock_data = mock_data.replace('[', '`').replace(']', '`')
# Remove SET IDENTITY_INSERT
mock_data = re.sub(r'SET IDENTITY_INSERT `.*?` (ON|OFF);\n', '', mock_data)

def scale_order(match):
    id_ = match.group(1)
    cust_id = match.group(2)
    t1, t2, t3, t4, t5 = map(float, [match.group(3), match.group(4), match.group(5), match.group(6), match.group(7)])
    rest = match.group(8)
    return f"INSERT INTO `Order` (`Id`, `CustomerId`, `OrderTotal`, `RefundedAmount`, `OrderShipping`, `OrderDiscount`, `OrderSubtotalExclTax`, `OrderStatusId`, `PaymentStatusId`, `ShippingStatusId`, `PaymentMethodSystemName`, `BillingCountry`, `CreatedOnUtc`) VALUES ({id_}, {cust_id}, {t1*120:.2f}, {t2*120:.2f}, {t3*120:.2f}, {t4*120:.2f}, {t5*120:.2f}, {rest})"

pattern_order = r"INSERT INTO `Order` \(`Id`, `CustomerId`, `OrderTotal`, `RefundedAmount`, `OrderShipping`, `OrderDiscount`, `OrderSubtotalExclTax`, `OrderStatusId`, `PaymentStatusId`, `ShippingStatusId`, `PaymentMethodSystemName`, `BillingCountry`, `CreatedOnUtc`\) VALUES \((\d+),\s*(\d+),\s*([\d\.]+),\s*([\d\.]+),\s*([\d\.]+),\s*([\d\.]+),\s*([\d\.]+),\s*(.*)\)"

mock_data = re.sub(pattern_order, scale_order, mock_data)

def scale_orderitem(match):
    id_ = match.group(1)
    order_id = match.group(2)
    prod_id = match.group(3)
    qty = match.group(4)
    price = float(match.group(5))
    return f"INSERT INTO `OrderItem` (`Id`, `OrderId`, `ProductId`, `Quantity`, `PriceExclTax`) VALUES ({id_}, {order_id}, {prod_id}, {qty}, {price*120:.2f})"

pattern_orderitem = r"INSERT INTO `OrderItem` \(`Id`, `OrderId`, `ProductId`, `Quantity`, `PriceExclTax`\) VALUES \((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*([\d\.]+)\)"

mock_data = re.sub(pattern_orderitem, scale_orderitem, mock_data)

with open('database/mock_data.sql', 'w') as f:
    f.write(mock_data)

print('Updated sql scripts')
