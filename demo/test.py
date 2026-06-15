import mysql.connector
c = mysql.connector.connect(host='db', user='root', password='root', database='aegis')
cursor = c.cursor(dictionary=True)

cursor.execute('SELECT count(*) FROM `Order`')
print("Orders:", cursor.fetchall())

cursor.execute('SELECT count(*) FROM `OrderItem`')
print("OrderItems:", cursor.fetchall())

cursor.execute('SELECT count(*) FROM `Product`')
print("Products:", cursor.fetchall())

cursor.execute('''
SELECT p.Name AS label, SUM(oi.Quantity) AS value
FROM `Order` o
INNER JOIN `OrderItem` oi ON o.Id = oi.OrderId
INNER JOIN `Product` p ON oi.ProductId = p.Id
WHERE 1=1
GROUP BY p.Name
ORDER BY value desc
LIMIT 5
''')
print("Query result:", cursor.fetchall())
