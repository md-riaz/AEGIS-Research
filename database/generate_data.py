import random
import uuid
from datetime import datetime, timedelta

def generate_mock_sql():
    output_file = "d:/Development/Personal/research/database/mock_data.sql"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("-- AEGIS Mock Data (Truth Schema Compatible)\n")
        f.write("-- Aligned with NopCommerce Truth Schema\n\n")
        f.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")
        
        # Country
        f.write("INSERT INTO `Country` (`Name`, `TwoLetterIsoCode`, `ThreeLetterIsoCode`, `AllowsBilling`, `AllowsShipping`, `NumericIsoCode`, `SubjectToVat`, `Published`, `DisplayOrder`, `LimitedToStores`) VALUES \n")
        f.write("('United States', 'US', 'USA', 1, 1, 840, 0, 1, 1, 0),\n")
        f.write("('Canada', 'CA', 'CAN', 1, 1, 124, 0, 1, 2, 0);\n\n")

        # StateProvince
        f.write("INSERT INTO `StateProvince` (`Name`, `Abbreviation`, `CountryId`, `Published`, `DisplayOrder`) VALUES \n")
        f.write("('New York', 'NY', 1, 1, 1),\n")
        f.write("('California', 'CA', 1, 1, 2);\n\n")

        # Store
        f.write("INSERT INTO `Store` (`Name`, `Url`, `SslEnabled`, `DefaultLanguageId`, `DisplayOrder`) VALUES \n")
        f.write("('AEGIS Main Store', 'http://localhost/', 1, 1, 1);\n\n")

        # Address
        f.write("INSERT INTO `Address` (`CountryId`, `StateProvinceId`, `FirstName`, `LastName`, `Email`, `City`, `Address1`, `ZipPostalCode`, `CreatedOnUtc`) VALUES \n")
        f.write("(1, 1, 'John', 'Doe', 'john@example.com', 'New York', '123 Main St', '10001', NOW()),\n")
        f.write("(1, 2, 'Jane', 'Smith', 'jane@example.com', 'Los Angeles', '456 West Blvd', '90001', NOW());\n\n")

        # Manufacturer
        f.write("INSERT INTO `Manufacturer` (`Name`, `ManufacturerTemplateId`, `PictureId`, `PageSize`, `AllowCustomersToSelectPageSize`, `SubjectToAcl`, `LimitedToStores`, `Published`, `Deleted`, `DisplayOrder`, `CreatedOnUtc`, `UpdatedOnUtc`) VALUES \n")
        f.write("('Apple', 1, 0, 10, 1, 0, 0, 1, 0, 0, NOW(), NOW()),\n")
        f.write("('Samsung', 1, 0, 10, 1, 0, 0, 1, 0, 1, NOW(), NOW());\n\n")

        # Category
        f.write("INSERT INTO `Category` (`Name`, `CategoryTemplateId`, `ParentCategoryId`, `PictureId`, `PageSize`, `AllowCustomersToSelectPageSize`, `ShowOnHomepage`, `IncludeInTopMenu`, `SubjectToAcl`, `LimitedToStores`, `Published`, `Deleted`, `DisplayOrder`, `CreatedOnUtc`, `UpdatedOnUtc`) VALUES \n")
        f.write("('Electronics', 1, 0, 0, 10, 1, 1, 1, 0, 0, NOW(), NOW()),\n")
        f.write("('Laptops', 1, 1, 0, 10, 1, 0, 1, 0, 1, NOW(), NOW());\n\n")

        # Product
        # Note: Only including essential columns to keep INSERT manageable, using defaults for others if allowed
        f.write("INSERT INTO `Product` (`Name`, `ProductTypeId`, `ParentGroupedProductId`, `VisibleIndividually`, `ShortDescription`, `FullDescription`, `ProductTemplateId`, `VendorId`, `ShowOnHomepage`, `AllowCustomerReviews`, `ApprovedRatingSum`, `NotApprovedRatingSum`, `ApprovedTotalReviews`, `NotApprovedTotalReviews`, `SubjectToAcl`, `LimitedToStores`, `IsGiftCard`, `GiftCardTypeId`, `RequireOtherProducts`, `AutomaticallyAddRequiredProducts`, `IsDownload`, `DownloadId`, `UnlimitedDownloads`, `MaxNumberOfDownloads`, `DownloadActivationTypeId`, `HasSampleDownload`, `SampleDownloadId`, `HasUserAgreement`, `IsRecurring`, `RecurringCycleLength`, `RecurringCyclePeriodId`, `RecurringTotalCycles`, `IsRental`, `RentalPriceLength`, `RentalPricePeriodId`, `IsShipEnabled`, `IsFreeShipping`, `ShipSeparately`, `AdditionalShippingCharge`, `DeliveryDateId`, `IsTaxExempt`, `TaxCategoryId`, `IsTelecommunicationsOrBroadcastingOrElectronicServices`, `ManageInventoryMethodId`, `ProductAvailabilityRangeId`, `UseMultipleWarehouses`, `WarehouseId`, `StockQuantity`, `DisplayStockAvailability`, `DisplayStockQuantity`, `MinStockQuantity`, `LowStockActivityId`, `NotifyAdminForQuantityBelow`, `BackorderModeId`, `AllowBackInStockSubscriptions`, `OrderMinimumQuantity`, `OrderMaximumQuantity`, `AllowAddingOnlyExistingAttributeCombinations`, `NotReturnable`, `DisableBuyButton`, `DisableWishlistButton`, `AvailableForPreOrder`, `CallForPrice`, `Price`, `OldPrice`, `ProductCost`, `CustomerEntersPrice`, `MinimumCustomerEnteredPrice`, `MaximumCustomerEnteredPrice`, `BasepriceEnabled`, `BasepriceAmount`, `BasepriceUnitId`, `BasepriceBaseAmount`, `BasepriceBaseUnitId`, `MarkAsNew`, `HasTierPrices`, `HasDiscountsApplied`, `Weight`, `Length`, `Width`, `Height`, `DisplayOrder`, `Published`, `Deleted`, `CreatedOnUtc`, `UpdatedOnUtc`) VALUES \n")
        f.write(f"('iPhone 15', 5, 0, 1, 'Latest Apple iPhone', 'Full description here', 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 100, 1, 1, 0, 0, 5, 0, 1, 1, 1000, 0, 0, 0, 0, 999.00, 1099.00, 500.00, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 1.0, 1.0, 1.0, 0, 1, 0, NOW(), NOW());\n\n")

        # Customer
        f.write("INSERT INTO `Customer` (`CustomerGuid`, `BillingAddress_Id`, `ShippingAddress_Id`, `IsTaxExempt`, `AffiliateId`, `VendorId`, `HasShoppingCartItems`, `RequireReLogin`, `FailedLoginAttempts`, `Active`, `Deleted`, `IsSystemAccount`, `CreatedOnUtc`, `LastActivityDateUtc`, `RegisteredInStoreId`, `Email`) VALUES \n")
        customers = []
        for i in range(1, 11):
            uid = str(uuid.uuid4())
            addr_id = 1 if i % 2 == 0 else 2
            customers.append(f"('{uid}', {addr_id}, {addr_id}, 0, 0, 0, 0, 0, 0, 1, 0, 0, NOW(), NOW(), 1, 'user{i}@example.com')")
        f.write(",\n".join(customers) + ";\n\n")

        # Order
        f.write("INSERT INTO `Order` (`CustomOrderNumber`, `BillingAddressId`, `CustomerId`, `OrderGuid`, `StoreId`, `PickupInStore`, `OrderStatusId`, `ShippingStatusId`, `PaymentStatusId`, `CurrencyRate`, `CustomerTaxDisplayTypeId`, `OrderSubtotalInclTax`, `OrderSubtotalExclTax`, `OrderSubTotalDiscountInclTax`, `OrderSubTotalDiscountExclTax`, `OrderShippingInclTax`, `OrderShippingExclTax`, `PaymentMethodAdditionalFeeInclTax`, `PaymentMethodAdditionalFeeExclTax`, `OrderTax`, `OrderDiscount`, `OrderTotal`, `RefundedAmount`, `CustomerLanguageId`, `AffiliateId`, `AllowStoringCreditCardNumber`, `Deleted`, `CreatedOnUtc`) VALUES \n")
        orders = []
        now = datetime.utcnow()
        for i in range(1, 21):
            onum = f"ORD-{i:05d}"
            uid = str(uuid.uuid4())
            cust_id = random.randint(1, 10)
            total = random.uniform(100, 1000)
            refunded = random.choice([0, 0, 0, random.uniform(0, total/2)])
            discount = random.choice([0, 0, random.uniform(5, 50)])
            created = (now - timedelta(days=random.randint(0, 60))).strftime("%Y-%m-%d %H:%M:%S")
            orders.append(f"('{onum}', 1, {cust_id}, '{uid}', 1, 0, 30, 30, 30, 1.0, 1, {total}, {total}, {discount}, {discount}, 10, 10, 0, 0, 0, {discount}, {total - discount}, {refunded}, 1, 0, 0, 0, '{created}')")
        f.write(",\n".join(orders) + ";\n\n")

        # OrderItem
        f.write("INSERT INTO `OrderItem` (`OrderId`, `ProductId`, `OrderItemGuid`, `Quantity`, `UnitPriceInclTax`, `UnitPriceExclTax`, `PriceInclTax`, `PriceExclTax`, `DiscountAmountInclTax`, `DiscountAmountExclTax`, `OriginalProductCost`, `DownloadCount`, `IsDownloadActivated`) VALUES \n")
        items = []
        for i in range(1, 21):
            uid = str(uuid.uuid4())
            items.append(f"({i}, 1, '{uid}', 1, 999.00, 999.00, 999.00, 999.00, 0, 0, 500.00, 0, 0)")
        f.write(",\n".join(items) + ";\n\n")

        # Mappings
        f.write("INSERT INTO `Product_Category_Mapping` (`ProductId`, `CategoryId`, `IsFeaturedProduct`, `DisplayOrder`) VALUES (1, 1, 0, 0);\n")
        f.write("INSERT INTO `Product_Manufacturer_Mapping` (`ProductId`, `ManufacturerId`, `IsFeaturedProduct`, `DisplayOrder`) VALUES (1, 1, 0, 0);\n\n")

        # Shipment
        f.write("INSERT INTO `Shipment` (`OrderId`, `TrackingNumber`, `TotalWeight`, `ShippedDateUtc`, `DeliveryDateUtc`, `AdminComment`, `CreatedOnUtc`) VALUES \n")
        f.write("(1, 'TRACK001', 1.5, NOW(), NOW(), 'Standard shipping', NOW());\n\n")

        f.write("SET FOREIGN_KEY_CHECKS = 1;\n")

    print(f"Mock data generated in {output_file}")

if __name__ == "__main__":
    generate_mock_sql()
