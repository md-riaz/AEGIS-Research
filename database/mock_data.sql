-- SafeDash Mock Data (Truth Schema Compatible)
-- Aligned with NopCommerce Truth Schema

SET FOREIGN_KEY_CHECKS = 0;

INSERT INTO `Country` (`Name`, `TwoLetterIsoCode`, `ThreeLetterIsoCode`, `AllowsBilling`, `AllowsShipping`, `NumericIsoCode`, `SubjectToVat`, `Published`, `DisplayOrder`, `LimitedToStores`) VALUES 
('United States', 'US', 'USA', 1, 1, 840, 0, 1, 1, 0),
('Canada', 'CA', 'CAN', 1, 1, 124, 0, 1, 2, 0);

INSERT INTO `StateProvince` (`Name`, `Abbreviation`, `CountryId`, `Published`, `DisplayOrder`) VALUES 
('New York', 'NY', 1, 1, 1),
('California', 'CA', 1, 1, 2);

INSERT INTO `Store` (`Name`, `Url`, `SslEnabled`, `DefaultLanguageId`, `DisplayOrder`) VALUES 
('SafeDash Main Store', 'http://localhost/', 1, 1, 1);

INSERT INTO `Address` (`CountryId`, `StateProvinceId`, `FirstName`, `LastName`, `Email`, `City`, `Address1`, `ZipPostalCode`, `CreatedOnUtc`) VALUES 
(1, 1, 'John', 'Doe', 'john@example.com', 'New York', '123 Main St', '10001', NOW()),
(1, 2, 'Jane', 'Smith', 'jane@example.com', 'Los Angeles', '456 West Blvd', '90001', NOW());

INSERT INTO `Manufacturer` (`Name`, `ManufacturerTemplateId`, `PictureId`, `PageSize`, `AllowCustomersToSelectPageSize`, `SubjectToAcl`, `LimitedToStores`, `Published`, `Deleted`, `DisplayOrder`, `CreatedOnUtc`, `UpdatedOnUtc`) VALUES 
('Apple', 1, 0, 10, 1, 0, 0, 1, 0, 0, NOW(), NOW()),
('Samsung', 1, 0, 10, 1, 0, 0, 1, 0, 1, NOW(), NOW());

INSERT INTO `Category` (`Name`, `CategoryTemplateId`, `ParentCategoryId`, `PictureId`, `PageSize`, `AllowCustomersToSelectPageSize`, `ShowOnHomepage`, `IncludeInTopMenu`, `SubjectToAcl`, `LimitedToStores`, `Published`, `Deleted`, `DisplayOrder`, `CreatedOnUtc`, `UpdatedOnUtc`) VALUES 
('Electronics', 1, 0, 0, 10, 1, 1, 1, 0, 0, NOW(), NOW()),
('Laptops', 1, 1, 0, 10, 1, 0, 1, 0, 1, NOW(), NOW());

INSERT INTO `Product` (`Name`, `ProductTypeId`, `ParentGroupedProductId`, `VisibleIndividually`, `ShortDescription`, `FullDescription`, `ProductTemplateId`, `VendorId`, `ShowOnHomepage`, `AllowCustomerReviews`, `ApprovedRatingSum`, `NotApprovedRatingSum`, `ApprovedTotalReviews`, `NotApprovedTotalReviews`, `SubjectToAcl`, `LimitedToStores`, `IsGiftCard`, `GiftCardTypeId`, `RequireOtherProducts`, `AutomaticallyAddRequiredProducts`, `IsDownload`, `DownloadId`, `UnlimitedDownloads`, `MaxNumberOfDownloads`, `DownloadActivationTypeId`, `HasSampleDownload`, `SampleDownloadId`, `HasUserAgreement`, `IsRecurring`, `RecurringCycleLength`, `RecurringCyclePeriodId`, `RecurringTotalCycles`, `IsRental`, `RentalPriceLength`, `RentalPricePeriodId`, `IsShipEnabled`, `IsFreeShipping`, `ShipSeparately`, `AdditionalShippingCharge`, `DeliveryDateId`, `IsTaxExempt`, `TaxCategoryId`, `IsTelecommunicationsOrBroadcastingOrElectronicServices`, `ManageInventoryMethodId`, `ProductAvailabilityRangeId`, `UseMultipleWarehouses`, `WarehouseId`, `StockQuantity`, `DisplayStockAvailability`, `DisplayStockQuantity`, `MinStockQuantity`, `LowStockActivityId`, `NotifyAdminForQuantityBelow`, `BackorderModeId`, `AllowBackInStockSubscriptions`, `OrderMinimumQuantity`, `OrderMaximumQuantity`, `AllowAddingOnlyExistingAttributeCombinations`, `NotReturnable`, `DisableBuyButton`, `DisableWishlistButton`, `AvailableForPreOrder`, `CallForPrice`, `Price`, `OldPrice`, `ProductCost`, `CustomerEntersPrice`, `MinimumCustomerEnteredPrice`, `MaximumCustomerEnteredPrice`, `BasepriceEnabled`, `BasepriceAmount`, `BasepriceUnitId`, `BasepriceBaseAmount`, `BasepriceBaseUnitId`, `MarkAsNew`, `HasTierPrices`, `HasDiscountsApplied`, `Weight`, `Length`, `Width`, `Height`, `DisplayOrder`, `Published`, `Deleted`, `CreatedOnUtc`, `UpdatedOnUtc`) VALUES 
('iPhone 15', 5, 0, 1, 'Latest Apple iPhone', 'Full description here', 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 100, 1, 1, 0, 0, 5, 0, 1, 1, 1000, 0, 0, 0, 0, 999.00, 1099.00, 500.00, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 1.0, 1.0, 1.0, 0, 1, 0, NOW(), NOW());

INSERT INTO `Customer` (`CustomerGuid`, `BillingAddress_Id`, `ShippingAddress_Id`, `IsTaxExempt`, `AffiliateId`, `VendorId`, `HasShoppingCartItems`, `RequireReLogin`, `FailedLoginAttempts`, `Active`, `Deleted`, `IsSystemAccount`, `CreatedOnUtc`, `LastActivityDateUtc`, `RegisteredInStoreId`, `Email`) VALUES 
('4c051075-d41c-4193-a948-89bf60b0bbee', 2, 2, 0, 0, 0, 0, 0, 0, 1, 0, 0, NOW(), NOW(), 1, 'user1@example.com'),
('6832e2cf-b8e5-4416-a094-b9ac06f594cc', 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, NOW(), NOW(), 1, 'user2@example.com'),
('62ea827f-ffd2-4692-8b42-f4cdbad94691', 2, 2, 0, 0, 0, 0, 0, 0, 1, 0, 0, NOW(), NOW(), 1, 'user3@example.com'),
('11a4346b-7848-4765-bb0e-c6b4682c3a18', 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, NOW(), NOW(), 1, 'user4@example.com'),
('29e8e1b9-90b0-48dc-a105-a7b8f903c41d', 2, 2, 0, 0, 0, 0, 0, 0, 1, 0, 0, NOW(), NOW(), 1, 'user5@example.com'),
('db2012ad-a054-4769-8e30-8b4b9d116560', 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, NOW(), NOW(), 1, 'user6@example.com'),
('818f5940-fd45-484d-8fa2-9bd31cb071dc', 2, 2, 0, 0, 0, 0, 0, 0, 1, 0, 0, NOW(), NOW(), 1, 'user7@example.com'),
('01b42f28-c5fa-4956-b4e7-4630025e8330', 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, NOW(), NOW(), 1, 'user8@example.com'),
('1bda7cb8-d39d-40c5-8c47-af193a033c42', 2, 2, 0, 0, 0, 0, 0, 0, 1, 0, 0, NOW(), NOW(), 1, 'user9@example.com'),
('14a6f875-ad09-4a84-b63f-5a44171fe653', 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, NOW(), NOW(), 1, 'user10@example.com');

INSERT INTO `Order` (`CustomOrderNumber`, `BillingAddressId`, `CustomerId`, `OrderGuid`, `StoreId`, `PickupInStore`, `OrderStatusId`, `ShippingStatusId`, `PaymentStatusId`, `CurrencyRate`, `CustomerTaxDisplayTypeId`, `OrderSubtotalInclTax`, `OrderSubtotalExclTax`, `OrderSubTotalDiscountInclTax`, `OrderSubTotalDiscountExclTax`, `OrderShippingInclTax`, `OrderShippingExclTax`, `PaymentMethodAdditionalFeeInclTax`, `PaymentMethodAdditionalFeeExclTax`, `OrderTax`, `OrderDiscount`, `OrderTotal`, `RefundedAmount`, `CustomerLanguageId`, `AffiliateId`, `AllowStoringCreditCardNumber`, `Deleted`, `CreatedOnUtc`) VALUES 
('ORD-00001', 1, 2, 'a68292d0-1676-4e43-8c4f-aa9f7299700b', 1, 0, 30, 30, 30, 1.0, 1, 853.4639355764917, 853.4639355764917, 0, 0, 10, 10, 0, 0, 0, 0, 853.4639355764917, 45.946917270288075, 1, 0, 0, 0, '2026-05-01 11:37:00'),
('ORD-00002', 1, 7, 'd061d213-ad15-4e0c-a93d-3cbda09dc7fa', 1, 0, 30, 30, 30, 1.0, 1, 540.2773628634279, 540.2773628634279, 0, 0, 10, 10, 0, 0, 0, 0, 540.2773628634279, 110.7047797263906, 1, 0, 0, 0, '2026-03-31 11:37:00'),
('ORD-00003', 1, 9, '824030a7-5b45-491c-8a91-2e00566df600', 1, 0, 30, 30, 30, 1.0, 1, 246.2896597445777, 246.2896597445777, 11.661736729230089, 11.661736729230089, 10, 10, 0, 0, 0, 11.661736729230089, 234.62792301534762, 0, 1, 0, 0, 0, '2026-03-11 11:37:00'),
('ORD-00004', 1, 9, 'c6afdb90-2ee1-4037-add7-3c162fb3e445', 1, 0, 30, 30, 30, 1.0, 1, 179.716092307596, 179.716092307596, 26.716142944817648, 26.716142944817648, 10, 10, 0, 0, 0, 26.716142944817648, 152.99994936277835, 0, 1, 0, 0, 0, '2026-04-21 11:37:00'),
('ORD-00005', 1, 10, 'b4a11a57-429c-4d24-92c9-08c13b372473', 1, 0, 30, 30, 30, 1.0, 1, 234.33436217239654, 234.33436217239654, 32.12025628012974, 32.12025628012974, 10, 10, 0, 0, 0, 32.12025628012974, 202.2141058922668, 61.477069516504926, 1, 0, 0, 0, '2026-05-04 11:37:00'),
('ORD-00006', 1, 5, '7081f7c4-f0aa-426a-b0b5-96128eb49412', 1, 0, 30, 30, 30, 1.0, 1, 726.6167198840564, 726.6167198840564, 0, 0, 10, 10, 0, 0, 0, 0, 726.6167198840564, 0, 1, 0, 0, 0, '2026-03-07 11:37:00'),
('ORD-00007', 1, 8, 'de5bfb7f-f73e-4572-a159-38437ce334d2', 1, 0, 30, 30, 30, 1.0, 1, 415.311588068521, 415.311588068521, 0, 0, 10, 10, 0, 0, 0, 0, 415.311588068521, 0, 1, 0, 0, 0, '2026-04-01 11:37:00'),
('ORD-00008', 1, 6, '6a039f90-c77e-4713-aaa6-339fa77a8a66', 1, 0, 30, 30, 30, 1.0, 1, 611.9954565019509, 611.9954565019509, 0, 0, 10, 10, 0, 0, 0, 0, 611.9954565019509, 251.27249996792224, 1, 0, 0, 0, '2026-04-14 11:37:00'),
('ORD-00009', 1, 4, 'bcb636c6-904b-4377-b5f2-592f0e6b0359', 1, 0, 30, 30, 30, 1.0, 1, 613.9082018374377, 613.9082018374377, 47.3460808445911, 47.3460808445911, 10, 10, 0, 0, 0, 47.3460808445911, 566.5621209928465, 0, 1, 0, 0, 0, '2026-03-25 11:37:00'),
('ORD-00010', 1, 3, '92209625-bdc6-4a39-bb78-4cfa0cb6f288', 1, 0, 30, 30, 30, 1.0, 1, 688.2129025163179, 688.2129025163179, 38.148684690096104, 38.148684690096104, 10, 10, 0, 0, 0, 38.148684690096104, 650.0642178262217, 0, 1, 0, 0, 0, '2026-04-18 11:37:00'),
('ORD-00011', 1, 7, '474f9e44-446d-4b5d-aca0-57f679c413a9', 1, 0, 30, 30, 30, 1.0, 1, 323.83608905172696, 323.83608905172696, 0, 0, 10, 10, 0, 0, 0, 0, 323.83608905172696, 0, 1, 0, 0, 0, '2026-04-08 11:37:00'),
('ORD-00012', 1, 10, 'd11c8eca-880f-4e77-8e39-af1f99d8dd21', 1, 0, 30, 30, 30, 1.0, 1, 384.06686438446656, 384.06686438446656, 0, 0, 10, 10, 0, 0, 0, 0, 384.06686438446656, 0, 1, 0, 0, 0, '2026-04-22 11:37:00'),
('ORD-00013', 1, 10, '531b59c0-7207-4003-a6ce-1a7abbd800fe', 1, 0, 30, 30, 30, 1.0, 1, 832.4073645940206, 832.4073645940206, 0, 0, 10, 10, 0, 0, 0, 0, 832.4073645940206, 384.365919291519, 1, 0, 0, 0, '2026-05-02 11:37:00'),
('ORD-00014', 1, 5, 'e4583a5c-5191-41da-91f1-f0e16d372902', 1, 0, 30, 30, 30, 1.0, 1, 699.481861398174, 699.481861398174, 0, 0, 10, 10, 0, 0, 0, 0, 699.481861398174, 0, 1, 0, 0, 0, '2026-04-21 11:37:00'),
('ORD-00015', 1, 10, '0ec85b2b-9932-4271-8368-c7409bdc73e1', 1, 0, 30, 30, 30, 1.0, 1, 680.3341740319845, 680.3341740319845, 0, 0, 10, 10, 0, 0, 0, 0, 680.3341740319845, 0, 1, 0, 0, 0, '2026-04-14 11:37:00'),
('ORD-00016', 1, 2, '8d03985f-8e97-4c66-bb14-a27d32894034', 1, 0, 30, 30, 30, 1.0, 1, 913.1639995665762, 913.1639995665762, 0, 0, 10, 10, 0, 0, 0, 0, 913.1639995665762, 0, 1, 0, 0, 0, '2026-04-10 11:37:00'),
('ORD-00017', 1, 3, 'd1a93eb1-65ad-4ba3-aaa6-f592452e9716', 1, 0, 30, 30, 30, 1.0, 1, 921.0921508927889, 921.0921508927889, 0, 0, 10, 10, 0, 0, 0, 0, 921.0921508927889, 0, 1, 0, 0, 0, '2026-03-20 11:37:00'),
('ORD-00018', 1, 1, 'a6b64b63-b61b-4f5a-a9a2-6dc44b21c3d3', 1, 0, 30, 30, 30, 1.0, 1, 229.40859997974295, 229.40859997974295, 0, 0, 10, 10, 0, 0, 0, 0, 229.40859997974295, 0, 1, 0, 0, 0, '2026-04-24 11:37:00'),
('ORD-00019', 1, 7, '6ef13778-43e1-4d5c-9a28-dcb7391edaa9', 1, 0, 30, 30, 30, 1.0, 1, 999.240526370919, 999.240526370919, 0, 0, 10, 10, 0, 0, 0, 0, 999.240526370919, 0, 1, 0, 0, 0, '2026-03-28 11:37:00'),
('ORD-00020', 1, 4, 'feecc354-c6f9-4a51-a013-393370accfa7', 1, 0, 30, 30, 30, 1.0, 1, 541.5105394296526, 541.5105394296526, 8.469445353223204, 8.469445353223204, 10, 10, 0, 0, 0, 8.469445353223204, 533.0410940764293, 0, 1, 0, 0, 0, '2026-04-16 11:37:00');

INSERT INTO `OrderItem` (`OrderId`, `ProductId`, `OrderItemGuid`, `Quantity`, `UnitPriceInclTax`, `UnitPriceExclTax`, `PriceInclTax`, `PriceExclTax`, `DiscountAmountInclTax`, `DiscountAmountExclTax`, `OriginalProductCost`, `DownloadCount`, `IsDownloadActivated`) VALUES 
(1, 1, 'a7374baa-cefc-44f5-82fc-4c7e4b8c3d0c', 1, 999.00, 999.00, 999.00, 999.00, 0, 0, 500.00, 0, 0),
(2, 1, '16a0a853-cf9e-4dce-a5fb-e742976936f5', 1, 999.00, 999.00, 999.00, 999.00, 0, 0, 500.00, 0, 0),
(3, 1, '4bcb11fc-b71a-484e-bb72-bd1b279775fd', 1, 999.00, 999.00, 999.00, 999.00, 0, 0, 500.00, 0, 0),
(4, 1, 'ad277ff1-adb7-48c1-8745-3dc4103110f1', 1, 999.00, 999.00, 999.00, 999.00, 0, 0, 500.00, 0, 0),
(5, 1, '80f2223b-50f5-45d6-a5d9-b7f61808729c', 1, 999.00, 999.00, 999.00, 999.00, 0, 0, 500.00, 0, 0),
(6, 1, '9311a4ec-0940-41fe-8598-83e129534360', 1, 999.00, 999.00, 999.00, 999.00, 0, 0, 500.00, 0, 0),
(7, 1, 'd3a6f1da-bfbd-4348-88e5-0c161843e9c5', 1, 999.00, 999.00, 999.00, 999.00, 0, 0, 500.00, 0, 0),
(8, 1, 'fd10509a-2158-4407-899c-95a05ca13e8e', 1, 999.00, 999.00, 999.00, 999.00, 0, 0, 500.00, 0, 0),
(9, 1, '7100cf78-6070-4244-940f-4bf26eb11cdb', 1, 999.00, 999.00, 999.00, 999.00, 0, 0, 500.00, 0, 0),
(10, 1, '5a996018-55b7-4801-9228-53aa3736c368', 1, 999.00, 999.00, 999.00, 999.00, 0, 0, 500.00, 0, 0),
(11, 1, 'b4f2ec24-0185-4241-9953-450afd09ec40', 1, 999.00, 999.00, 999.00, 999.00, 0, 0, 500.00, 0, 0),
(12, 1, '12d5c409-dc6d-47ab-aadb-572a143c5af2', 1, 999.00, 999.00, 999.00, 999.00, 0, 0, 500.00, 0, 0),
(13, 1, '75818c11-2885-4695-906f-2c49a67583b1', 1, 999.00, 999.00, 999.00, 999.00, 0, 0, 500.00, 0, 0),
(14, 1, 'aeefbd8f-6dab-4019-a98c-202ea8867e93', 1, 999.00, 999.00, 999.00, 999.00, 0, 0, 500.00, 0, 0),
(15, 1, '1292bcf4-91cd-4228-833e-678886167e6c', 1, 999.00, 999.00, 999.00, 999.00, 0, 0, 500.00, 0, 0),
(16, 1, '35724f11-eff2-4cb8-a6fd-037942b388e8', 1, 999.00, 999.00, 999.00, 999.00, 0, 0, 500.00, 0, 0),
(17, 1, '680eb596-43c0-4f6c-b402-6a01940e7913', 1, 999.00, 999.00, 999.00, 999.00, 0, 0, 500.00, 0, 0),
(18, 1, '6d5b5aff-8832-4579-b596-dc9ea6e8cde9', 1, 999.00, 999.00, 999.00, 999.00, 0, 0, 500.00, 0, 0),
(19, 1, 'baf9ebb1-dc95-4607-a2d1-ce01e23cd423', 1, 999.00, 999.00, 999.00, 999.00, 0, 0, 500.00, 0, 0),
(20, 1, '54f12256-3116-45cb-a12d-ef544ef7c2ef', 1, 999.00, 999.00, 999.00, 999.00, 0, 0, 500.00, 0, 0);

INSERT INTO `Product_Category_Mapping` (`ProductId`, `CategoryId`, `IsFeaturedProduct`, `DisplayOrder`) VALUES (1, 1, 0, 0);
INSERT INTO `Product_Manufacturer_Mapping` (`ProductId`, `ManufacturerId`, `IsFeaturedProduct`, `DisplayOrder`) VALUES (1, 1, 0, 0);

INSERT INTO `Shipment` (`OrderId`, `TrackingNumber`, `TotalWeight`, `ShippedDateUtc`, `DeliveryDateUtc`, `AdminComment`, `CreatedOnUtc`) VALUES 
(1, 'TRACK001', 1.5, NOW(), NOW(), 'Standard shipping', NOW());

SET FOREIGN_KEY_CHECKS = 1;
