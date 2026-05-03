-- SafeDash Demo Schema
-- Based on a simplified nopCommerce / E-Commerce database structure

CREATE TABLE [Customer] (
    [Id] INT PRIMARY KEY IDENTITY(1,1),
    [Email] NVARCHAR(255) NOT NULL,
    [CreatedOnUtc] DATETIME NOT NULL
);

CREATE TABLE [Category] (
    [Id] INT PRIMARY KEY IDENTITY(1,1),
    [Name] NVARCHAR(255) NOT NULL
);

CREATE TABLE [Product] (
    [Id] INT PRIMARY KEY IDENTITY(1,1),
    [Name] NVARCHAR(255) NOT NULL,
    [StockQuantity] INT NOT NULL DEFAULT 0,
    [ApprovedTotalReviews] INT NOT NULL DEFAULT 0
);

CREATE TABLE [Product_Category_Mapping] (
    [Id] INT PRIMARY KEY IDENTITY(1,1),
    [ProductId] INT NOT NULL,
    [CategoryId] INT NOT NULL,
    FOREIGN KEY ([ProductId]) REFERENCES [Product]([Id]),
    FOREIGN KEY ([CategoryId]) REFERENCES [Category]([Id])
);

CREATE TABLE [Order] (
    [Id] INT PRIMARY KEY IDENTITY(1,1),
    [CustomerId] INT NOT NULL,
    [OrderTotal] DECIMAL(18,2) NOT NULL,
    [RefundedAmount] DECIMAL(18,2) NOT NULL DEFAULT 0,
    [OrderShipping] DECIMAL(18,2) NOT NULL DEFAULT 0,
    [OrderDiscount] DECIMAL(18,2) NOT NULL DEFAULT 0,
    [OrderSubtotalExclTax] DECIMAL(18,2) NOT NULL DEFAULT 0,
    [OrderStatusId] INT NOT NULL DEFAULT 10,
    [PaymentStatusId] INT NOT NULL DEFAULT 10,
    [ShippingStatusId] INT NOT NULL DEFAULT 10,
    [PaymentMethodSystemName] NVARCHAR(255) NULL,
    [BillingCountry] NVARCHAR(255) NULL,
    [CreatedOnUtc] DATETIME NOT NULL,
    FOREIGN KEY ([CustomerId]) REFERENCES [Customer]([Id])
);

CREATE TABLE [OrderItem] (
    [Id] INT PRIMARY KEY IDENTITY(1,1),
    [OrderId] INT NOT NULL,
    [ProductId] INT NOT NULL,
    [Quantity] INT NOT NULL,
    [PriceExclTax] DECIMAL(18,2) NOT NULL,
    FOREIGN KEY ([OrderId]) REFERENCES [Order]([Id]),
    FOREIGN KEY ([ProductId]) REFERENCES [Product]([Id])
);
