-- SafeDash Schema — Full nopCommerce Structure
-- Derived from: nopCommerce/src/Libraries/Nop.Core/Domain/*.cs
-- Sensitive fields (CardNumber, CardCvv2, etc.) intentionally excluded

-- ============================================================
-- DIRECTORY / GEOGRAPHY
-- ============================================================

CREATE TABLE `Country` (
    `Id` INT PRIMARY KEY AUTO_INCREMENT,
    `Name` VARCHAR(255) NOT NULL,
    `TwoLetterIsoCode` VARCHAR(2) NULL,
    `ThreeLetterIsoCode` VARCHAR(3) NULL,
    `NumericIsoCode` INT NOT NULL DEFAULT 0,
    `AllowsBilling` TINYINT(1) NOT NULL DEFAULT 1,
    `AllowsShipping` TINYINT(1) NOT NULL DEFAULT 1,
    `SubjectToVat` TINYINT(1) NOT NULL DEFAULT 0,
    `Published` TINYINT(1) NOT NULL DEFAULT 1,
    `DisplayOrder` INT NOT NULL DEFAULT 0,
    `LimitedToStores` TINYINT(1) NOT NULL DEFAULT 0
);

CREATE TABLE `StateProvince` (
    `Id` INT PRIMARY KEY AUTO_INCREMENT,
    `CountryId` INT NOT NULL,
    `Name` VARCHAR(255) NOT NULL,
    `Abbreviation` VARCHAR(10) NULL,
    `Published` TINYINT(1) NOT NULL DEFAULT 1,
    `DisplayOrder` INT NOT NULL DEFAULT 0,
    FOREIGN KEY (`CountryId`) REFERENCES `Country`(`Id`)
);

-- ============================================================
-- STORE
-- ============================================================

CREATE TABLE `Store` (
    `Id` INT PRIMARY KEY AUTO_INCREMENT,
    `Name` VARCHAR(400) NOT NULL,
    `Url` VARCHAR(400) NOT NULL,
    `SslEnabled` TINYINT(1) NOT NULL DEFAULT 0,
    `Hosts` VARCHAR(1000) NULL,
    `DefaultLanguageId` INT NOT NULL DEFAULT 0,
    `DisplayOrder` INT NOT NULL DEFAULT 0,
    `CompanyName` VARCHAR(400) NULL,
    `CompanyAddress` VARCHAR(400) NULL,
    `CompanyPhoneNumber` VARCHAR(100) NULL,
    `CompanyVat` VARCHAR(100) NULL,
    `Deleted` TINYINT(1) NOT NULL DEFAULT 0
);

-- ============================================================
-- ADDRESS
-- ============================================================

CREATE TABLE `Address` (
    `Id` INT PRIMARY KEY AUTO_INCREMENT,
    `FirstName` VARCHAR(255) NULL,
    `LastName` VARCHAR(255) NULL,
    `Email` VARCHAR(255) NULL,
    `Company` VARCHAR(255) NULL,
    `CountryId` INT NULL,
    `StateProvinceId` INT NULL,
    `County` VARCHAR(255) NULL,
    `City` VARCHAR(255) NULL,
    `Address1` VARCHAR(255) NULL,
    `Address2` VARCHAR(255) NULL,
    `ZipPostalCode` VARCHAR(30) NULL,
    `PhoneNumber` VARCHAR(30) NULL,
    `FaxNumber` VARCHAR(30) NULL,
    `CreatedOnUtc` DATETIME NOT NULL,
    FOREIGN KEY (`CountryId`) REFERENCES `Country`(`Id`),
    FOREIGN KEY (`StateProvinceId`) REFERENCES `StateProvince`(`Id`)
);

-- ============================================================
-- CUSTOMER
-- ============================================================

CREATE TABLE `Customer` (
    `Id` INT PRIMARY KEY AUTO_INCREMENT,
    `CustomerGuid` CHAR(36) NOT NULL,
    `Username` VARCHAR(255) NULL,
    `Email` VARCHAR(255) NULL,
    `FirstName` VARCHAR(255) NULL,
    `LastName` VARCHAR(255) NULL,
    `Gender` VARCHAR(10) NULL,
    `DateOfBirth` DATETIME NULL,
    `Company` VARCHAR(255) NULL,
    `StreetAddress` VARCHAR(255) NULL,
    `City` VARCHAR(255) NULL,
    `CountryId` INT NOT NULL DEFAULT 0,
    `StateProvinceId` INT NOT NULL DEFAULT 0,
    `Phone` VARCHAR(30) NULL,
    `VatNumber` VARCHAR(100) NULL,
    `AffiliateId` INT NOT NULL DEFAULT 0,
    `VendorId` INT NOT NULL DEFAULT 0,
    `Active` TINYINT(1) NOT NULL DEFAULT 1,
    `Deleted` TINYINT(1) NOT NULL DEFAULT 0,
    `IsSystemAccount` TINYINT(1) NOT NULL DEFAULT 0,
    `SystemName` VARCHAR(400) NULL,
    `LastIpAddress` VARCHAR(100) NULL,
    `CreatedOnUtc` DATETIME NOT NULL,
    `LastLoginDateUtc` DATETIME NULL,
    `LastActivityDateUtc` DATETIME NOT NULL,
    `RegisteredInStoreId` INT NOT NULL DEFAULT 0,
    `BillingAddressId` INT NULL,
    `ShippingAddressId` INT NULL
);

-- ============================================================
-- CATALOG
-- ============================================================

CREATE TABLE `Category` (
    `Id` INT PRIMARY KEY AUTO_INCREMENT,
    `Name` VARCHAR(400) NOT NULL,
    `Description` TEXT NULL,
    `ParentCategoryId` INT NOT NULL DEFAULT 0,
    `Published` TINYINT(1) NOT NULL DEFAULT 1,
    `Deleted` TINYINT(1) NOT NULL DEFAULT 0,
    `DisplayOrder` INT NOT NULL DEFAULT 0,
    `CreatedOnUtc` DATETIME NOT NULL,
    `UpdatedOnUtc` DATETIME NOT NULL
);

CREATE TABLE `Manufacturer` (
    `Id` INT PRIMARY KEY AUTO_INCREMENT,
    `Name` VARCHAR(400) NOT NULL,
    `Description` TEXT NULL,
    `Published` TINYINT(1) NOT NULL DEFAULT 1,
    `Deleted` TINYINT(1) NOT NULL DEFAULT 0,
    `DisplayOrder` INT NOT NULL DEFAULT 0,
    `CreatedOnUtc` DATETIME NOT NULL,
    `UpdatedOnUtc` DATETIME NOT NULL
);

CREATE TABLE `Product` (
    `Id` INT PRIMARY KEY AUTO_INCREMENT,
    `ProductTypeId` INT NOT NULL DEFAULT 5,
    `ParentGroupedProductId` INT NOT NULL DEFAULT 0,
    `VisibleIndividually` TINYINT(1) NOT NULL DEFAULT 1,
    `Name` VARCHAR(400) NOT NULL,
    `ShortDescription` TEXT NULL,
    `Sku` VARCHAR(400) NULL,
    `ManufacturerPartNumber` VARCHAR(400) NULL,
    `Gtin` VARCHAR(400) NULL,
    `IsGiftCard` TINYINT(1) NOT NULL DEFAULT 0,
    `RequireOtherProducts` TINYINT(1) NOT NULL DEFAULT 0,
    `IsDownload` TINYINT(1) NOT NULL DEFAULT 0,
    `IsRecurring` TINYINT(1) NOT NULL DEFAULT 0,
    `IsRental` TINYINT(1) NOT NULL DEFAULT 0,
    `IsShipEnabled` TINYINT(1) NOT NULL DEFAULT 1,
    `IsFreeShipping` TINYINT(1) NOT NULL DEFAULT 0,
    `AdditionalShippingCharge` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `IsTaxExempt` TINYINT(1) NOT NULL DEFAULT 0,
    `TaxCategoryId` INT NOT NULL DEFAULT 0,
    `ManageInventoryMethodId` INT NOT NULL DEFAULT 0,
    `StockQuantity` INT NOT NULL DEFAULT 0,
    `MinStockQuantity` INT NOT NULL DEFAULT 0,
    `LowStockActivityId` INT NOT NULL DEFAULT 0,
    `NotifyAdminForQuantityBelow` INT NOT NULL DEFAULT 1,
    `BackorderModeId` INT NOT NULL DEFAULT 0,
    `OrderMinimumQuantity` INT NOT NULL DEFAULT 1,
    `OrderMaximumQuantity` INT NOT NULL DEFAULT 10000,
    `NotReturnable` TINYINT(1) NOT NULL DEFAULT 0,
    `DisableBuyButton` TINYINT(1) NOT NULL DEFAULT 0,
    `DisableWishlistButton` TINYINT(1) NOT NULL DEFAULT 0,
    `AvailableForPreOrder` TINYINT(1) NOT NULL DEFAULT 0,
    `CallForPrice` TINYINT(1) NOT NULL DEFAULT 0,
    `Price` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `OldPrice` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `ProductCost` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `MarkAsNew` TINYINT(1) NOT NULL DEFAULT 0,
    `MarkAsNewStartDateTimeUtc` DATETIME NULL,
    `MarkAsNewEndDateTimeUtc` DATETIME NULL,
    `Weight` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `Length` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `Width` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `Height` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `DisplayOrder` INT NOT NULL DEFAULT 0,
    `Published` TINYINT(1) NOT NULL DEFAULT 1,
    `Deleted` TINYINT(1) NOT NULL DEFAULT 0,
    `CreatedOnUtc` DATETIME NOT NULL,
    `UpdatedOnUtc` DATETIME NOT NULL,
    `VendorId` INT NOT NULL DEFAULT 0,
    `AllowCustomerReviews` TINYINT(1) NOT NULL DEFAULT 1,
    `ApprovedRatingSum` INT NOT NULL DEFAULT 0,
    `NotApprovedRatingSum` INT NOT NULL DEFAULT 0,
    `ApprovedTotalReviews` INT NOT NULL DEFAULT 0,
    `NotApprovedTotalReviews` INT NOT NULL DEFAULT 0
);

-- ============================================================
-- CATALOG MAPPINGS
-- ============================================================

CREATE TABLE `Product_Category_Mapping` (
    `Id` INT PRIMARY KEY AUTO_INCREMENT,
    `ProductId` INT NOT NULL,
    `CategoryId` INT NOT NULL,
    `IsFeaturedProduct` TINYINT(1) NOT NULL DEFAULT 0,
    `DisplayOrder` INT NOT NULL DEFAULT 0,
    FOREIGN KEY (`ProductId`) REFERENCES `Product`(`Id`),
    FOREIGN KEY (`CategoryId`) REFERENCES `Category`(`Id`)
);

CREATE TABLE `Product_Manufacturer_Mapping` (
    `Id` INT PRIMARY KEY AUTO_INCREMENT,
    `ProductId` INT NOT NULL,
    `ManufacturerId` INT NOT NULL,
    `IsFeaturedProduct` TINYINT(1) NOT NULL DEFAULT 0,
    `DisplayOrder` INT NOT NULL DEFAULT 0,
    FOREIGN KEY (`ProductId`) REFERENCES `Product`(`Id`),
    FOREIGN KEY (`ManufacturerId`) REFERENCES `Manufacturer`(`Id`)
);

-- ============================================================
-- ORDERS
-- ============================================================

CREATE TABLE `Order` (
    `Id` INT PRIMARY KEY AUTO_INCREMENT,
    `OrderGuid` CHAR(36) NOT NULL,
    `StoreId` INT NOT NULL DEFAULT 0,
    `CustomerId` INT NOT NULL,
    `BillingAddressId` INT NOT NULL,
    `ShippingAddressId` INT NULL,
    `PickupInStore` TINYINT(1) NOT NULL DEFAULT 0,
    `OrderStatusId` INT NOT NULL DEFAULT 10,
    `ShippingStatusId` INT NOT NULL DEFAULT 10,
    `PaymentStatusId` INT NOT NULL DEFAULT 10,
    `PaymentMethodSystemName` VARCHAR(255) NULL,
    `CustomerCurrencyCode` VARCHAR(5) NULL,
    `CurrencyRate` DECIMAL(18,8) NOT NULL DEFAULT 1,
    `OrderSubtotalInclTax` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `OrderSubtotalExclTax` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `OrderSubTotalDiscountInclTax` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `OrderSubTotalDiscountExclTax` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `OrderShippingInclTax` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `OrderShippingExclTax` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `PaymentMethodAdditionalFeeInclTax` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `PaymentMethodAdditionalFeeExclTax` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `OrderTax` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `OrderDiscount` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `OrderTotal` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `RefundedAmount` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `CustomerLanguageId` INT NOT NULL DEFAULT 0,
    `AffiliateId` INT NOT NULL DEFAULT 0,
    `CustomerIp` VARCHAR(100) NULL,
    `PaidDateUtc` DATETIME NULL,
    `ShippingMethod` VARCHAR(255) NULL,
    `Deleted` TINYINT(1) NOT NULL DEFAULT 0,
    `CreatedOnUtc` DATETIME NOT NULL,
    `CustomOrderNumber` VARCHAR(100) NULL,
    FOREIGN KEY (`CustomerId`) REFERENCES `Customer`(`Id`),
    FOREIGN KEY (`BillingAddressId`) REFERENCES `Address`(`Id`)
);

CREATE TABLE `OrderItem` (
    `Id` INT PRIMARY KEY AUTO_INCREMENT,
    `OrderItemGuid` CHAR(36) NOT NULL,
    `OrderId` INT NOT NULL,
    `ProductId` INT NOT NULL,
    `Quantity` INT NOT NULL,
    `UnitPriceInclTax` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `UnitPriceExclTax` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `PriceInclTax` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `PriceExclTax` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `DiscountAmountInclTax` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `DiscountAmountExclTax` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `OriginalProductCost` DECIMAL(18,4) NOT NULL DEFAULT 0,
    `ItemWeight` DECIMAL(18,4) NULL,
    FOREIGN KEY (`OrderId`) REFERENCES `Order`(`Id`),
    FOREIGN KEY (`ProductId`) REFERENCES `Product`(`Id`)
);

-- ============================================================
-- SHIPPING
-- ============================================================

CREATE TABLE `Shipment` (
    `Id` INT PRIMARY KEY AUTO_INCREMENT,
    `OrderId` INT NOT NULL,
    `TrackingNumber` VARCHAR(255) NULL,
    `TotalWeight` DECIMAL(18,4) NULL,
    `ShippedDateUtc` DATETIME NULL,
    `DeliveryDateUtc` DATETIME NULL,
    `ReadyForPickupDateUtc` DATETIME NULL,
    `AdminComment` TEXT NULL,
    `CreatedOnUtc` DATETIME NOT NULL,
    FOREIGN KEY (`OrderId`) REFERENCES `Order`(`Id`)
);

CREATE TABLE `ShipmentItem` (
    `Id` INT PRIMARY KEY AUTO_INCREMENT,
    `ShipmentId` INT NOT NULL,
    `OrderItemId` INT NOT NULL,
    `Quantity` INT NOT NULL,
    `WarehouseId` INT NOT NULL DEFAULT 0,
    FOREIGN KEY (`ShipmentId`) REFERENCES `Shipment`(`Id`),
    FOREIGN KEY (`OrderItemId`) REFERENCES `OrderItem`(`Id`)
);
