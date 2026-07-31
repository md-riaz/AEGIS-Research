SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE `AclRecord`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `EntityName` VARCHAR(400) NOT NULL,
  `CustomerRoleId` INT NOT NULL,
  `EntityId` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ActivityLog`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Comment` TEXT NOT NULL,
  `IpAddress` VARCHAR(200) NULL,
  `EntityName` VARCHAR(400) NULL,
  `ActivityLogTypeId` INT NOT NULL,
  `CustomerId` INT NOT NULL,
  `EntityId` INT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ActivityLogType`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `SystemKeyword` VARCHAR(100) NOT NULL,
  `Name` VARCHAR(200) NOT NULL,
  `Enabled` TINYINT(1) NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Address`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `CountryId` INT NULL,
  `StateProvinceId` INT NULL,
  `FirstName` TEXT NULL,
  `LastName` TEXT NULL,
  `Email` TEXT NULL,
  `Company` TEXT NULL,
  `County` TEXT NULL,
  `City` TEXT NULL,
  `Address1` TEXT NULL,
  `Address2` TEXT NULL,
  `ZipPostalCode` TEXT NULL,
  `PhoneNumber` TEXT NULL,
  `FaxNumber` TEXT NULL,
  `CustomAttributes` TEXT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `AddressAttribute`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `IsRequired` TINYINT(1) NOT NULL,
  `AttributeControlTypeId` INT NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `AddressAttributeValue`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `AddressAttributeId` INT NOT NULL,
  `IsPreSelected` TINYINT(1) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Affiliate`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `AddressId` INT NOT NULL,
  `AdminComment` TEXT NULL,
  `FriendlyUrlName` TEXT NULL,
  `Deleted` TINYINT(1) NOT NULL,
  `Active` TINYINT(1) NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `BackInStockSubscription`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `CustomerId` INT NOT NULL,
  `ProductId` INT NOT NULL,
  `StoreId` INT NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `BlogComment`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `StoreId` INT NOT NULL,
  `CustomerId` INT NOT NULL,
  `BlogPostId` INT NOT NULL,
  `CommentText` TEXT NULL,
  `IsApproved` TINYINT(1) NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `BlogPost`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Title` TEXT NOT NULL,
  `Body` TEXT NOT NULL,
  `MetaKeywords` VARCHAR(400) NULL,
  `MetaTitle` VARCHAR(400) NULL,
  `LanguageId` INT NOT NULL,
  `IncludeInSitemap` TINYINT(1) NOT NULL,
  `BodyOverview` TEXT NULL,
  `AllowComments` TINYINT(1) NOT NULL,
  `Tags` TEXT NULL,
  `StartDateUtc` DATETIME NULL,
  `EndDateUtc` DATETIME NULL,
  `MetaDescription` TEXT NULL,
  `LimitedToStores` TINYINT(1) NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Campaign`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` TEXT NOT NULL,
  `Subject` TEXT NOT NULL,
  `Body` TEXT NOT NULL,
  `StoreId` INT NOT NULL,
  `CustomerRoleId` INT NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  `DontSendBeforeDateUtc` DATETIME NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Category`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `MetaKeywords` VARCHAR(400) NULL,
  `MetaTitle` VARCHAR(400) NULL,
  `PriceRanges` VARCHAR(400) NULL,
  `PageSizeOptions` VARCHAR(200) NULL,
  `Description` TEXT NULL,
  `CategoryTemplateId` INT NOT NULL,
  `MetaDescription` TEXT NULL,
  `ParentCategoryId` INT NOT NULL,
  `PictureId` INT NOT NULL,
  `PageSize` INT NOT NULL,
  `AllowCustomersToSelectPageSize` TINYINT(1) NOT NULL,
  `ShowOnHomepage` TINYINT(1) NOT NULL,
  `IncludeINTopMenu` TINYINT(1) NOT NULL,
  `SubjectToAcl` TINYINT(1) NOT NULL,
  `LimitedToStores` TINYINT(1) NOT NULL,
  `Published` TINYINT(1) NOT NULL,
  `Deleted` TINYINT(1) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  `UpdatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `CategoryTemplate`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `ViewPath` VARCHAR(400) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `CheckoutAttribute`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `TextPrompt` TEXT NULL,
  `IsRequired` TINYINT(1) NOT NULL,
  `ShippableProductRequired` TINYINT(1) NOT NULL,
  `IsTaxExempt` TINYINT(1) NOT NULL,
  `TaxCategoryId` INT NOT NULL,
  `AttributeControlTypeId` INT NOT NULL,
  `DisplayOrder` INT NOT NULL,
  `LimitedToStores` TINYINT(1) NOT NULL,
  `ValidationMinLength` INT NULL,
  `ValidationMaxLength` INT NULL,
  `ValidationFileAllowedExtensions` TEXT NULL,
  `ValidationFileMaximumSize` INT NULL,
  `DefaultValue` TEXT NULL,
  `ConditionAttributeTEXT` TEXT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `CheckoutAttributeValue`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `ColorSquaresRgb` VARCHAR(100) NULL,
  `CheckoutAttributeId` INT NOT NULL,
  `PriceAdjustment` DECIMAL(18, 4) NOT NULL,
  `WeightAdjustment` DECIMAL(18, 4) NOT NULL,
  `IsPreSelected` TINYINT(1) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Country`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(100) NOT NULL,
  `TwoLetterIsoCode` VARCHAR(2) NULL,
  `ThreeLetterIsoCode` VARCHAR(3) NULL,
  `AllowsBilling` TINYINT(1) NOT NULL,
  `AllowsShipping` TINYINT(1) NOT NULL,
  `NumericIsoCode` INT NOT NULL,
  `SubjectToVat` TINYINT(1) NOT NULL,
  `Published` TINYINT(1) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  `LimitedToStores` TINYINT(1) NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `CrossSellProduct`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `ProductId1` INT NOT NULL,
  `ProductId2` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Currency`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(50) NOT NULL,
  `CurrencyCode` VARCHAR(5) NOT NULL,
  `DisplayLocale` VARCHAR(50) NULL,
  `CustomFormatting` VARCHAR(50) NULL,
  `Rate` DECIMAL(18, 4) NOT NULL,
  `LimitedToStores` TINYINT(1) NOT NULL,
  `Published` TINYINT(1) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  `UpdatedOnUtc` DATETIME NOT NULL,
  `RoundingTypeId` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Customer`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Username` VARCHAR(1000) NULL,
  `Email` VARCHAR(1000) NULL,
  `EmailToRevalidate` VARCHAR(1000) NULL,
  `SystemName` VARCHAR(400) NULL,
  -- nopCommerce keeps customer names in GenericAttribute; the AEGIS semantic
  -- layer resolves the customer_name dimension as CONCAT(cu.FirstName,' ',
  -- cu.LastName), so the Truth Schema carries them directly on Customer.
  `FirstName` VARCHAR(400) NULL,
  `LastName` VARCHAR(400) NULL,
  `BillingAddress_Id` INT NULL,
  `ShippingAddress_Id` INT NULL,
  `CustomerGuid` VARCHAR(36) NOT NULL,
  `AdminComment` TEXT NULL,
  `IsTaxExempt` TINYINT(1) NOT NULL,
  `AffiliateId` INT NOT NULL,
  `VendorId` INT NOT NULL,
  `HasShoppingCartItems` TINYINT(1) NOT NULL,
  `RequireReLogin` TINYINT(1) NOT NULL,
  `FailedLoginAttempts` INT NOT NULL,
  `CannotLoginUntilDateUtc` DATETIME NULL,
  `Active` TINYINT(1) NOT NULL,
  `Deleted` TINYINT(1) NOT NULL,
  `IsSystemAccount` TINYINT(1) NOT NULL,
  `LastIpAddress` TEXT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  `LastLoginDateUtc` DATETIME NULL,
  `LastActivityDateUtc` DATETIME NOT NULL,
  `RegisteredInStoreId` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Customer_CustomerRole_Mapping`(
  `Customer_Id` INT NOT NULL,
  `CustomerRole_Id` INT NOT NULL,
  PRIMARY KEY (`Customer_Id`, `CustomerRole_Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `CustomerAddresses`(
  `Address_Id` INT NOT NULL,
  `Customer_Id` INT NOT NULL,
  PRIMARY KEY (`Address_Id`, `Customer_Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `CustomerAttribute`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `IsRequired` TINYINT(1) NOT NULL,
  `AttributeControlTypeId` INT NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `CustomerAttributeValue`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `CustomerAttributeId` INT NOT NULL,
  `IsPreSelected` TINYINT(1) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `CustomerPassword`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `CustomerId` INT NOT NULL,
  `Password` TEXT NULL,
  `PasswordFormatId` INT NOT NULL,
  `PasswordSalt` TEXT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `CustomerRole`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(255) NOT NULL,
  `SystemName` VARCHAR(255) NULL,
  `FreeShipping` TINYINT(1) NOT NULL,
  `TaxExempt` TINYINT(1) NOT NULL,
  `Active` TINYINT(1) NOT NULL,
  `IsSystemRole` TINYINT(1) NOT NULL,
  `EnablePasswordLifetime` TINYINT(1) NOT NULL,
  `OverrideTaxDisplayType` TINYINT(1) NOT NULL,
  `DefaultTaxDisplayTypeId` INT NOT NULL,
  `PurchasedWithProductId` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `DeliveryDate`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Discount`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(200) NOT NULL,
  `CouponCode` VARCHAR(100) NULL,
  `AdminComment` TEXT NULL,
  `DiscountTypeId` INT NOT NULL,
  `UsePercentage` TINYINT(1) NOT NULL,
  `DiscountPercentage` DECIMAL(18, 4) NOT NULL,
  `DiscountAmount` DECIMAL(18, 4) NOT NULL,
  `MaximumDiscountAmount` DECIMAL(18, 4) NULL,
  `StartDateUtc` DATETIME NULL,
  `EndDateUtc` DATETIME NULL,
  `RequiresCouponCode` TINYINT(1) NOT NULL,
  `IsCumulative` TINYINT(1) NOT NULL,
  `DiscountLimitationId` INT NOT NULL,
  `LimitationTimes` INT NOT NULL,
  `MaximumDiscountedQuantity` INT NULL,
  `AppliedToSubCategories` TINYINT(1) NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Discount_AppliedToCategories`(
  `Discount_Id` INT NOT NULL,
  `Category_Id` INT NOT NULL,
  PRIMARY KEY (`Discount_Id`, `Category_Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Discount_AppliedToManufacturers`(
  `Discount_Id` INT NOT NULL,
  `Manufacturer_Id` INT NOT NULL,
  PRIMARY KEY (`Discount_Id`, `Manufacturer_Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Discount_AppliedToProducts`(
  `Discount_Id` INT NOT NULL,
  `Product_Id` INT NOT NULL,
  PRIMARY KEY (`Discount_Id`, `Product_Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `DiscountRequirement`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `DiscountId` INT NOT NULL,
  `ParentId` INT NULL,
  `DiscountRequirementRuleSystemName` TEXT NULL,
  `INTeractionTypeId` INT NULL,
  `IsGroup` TINYINT(1) NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `DiscountUsageHistory`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `DiscountId` INT NOT NULL,
  `OrderId` INT NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Download`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `DownloadGuid` VARCHAR(36) NOT NULL,
  `UseDownloadUrl` TINYINT(1) NOT NULL,
  `DownloadUrl` TEXT NULL,
  `DownloadBinary` LONGBLOB NULL,
  `ContentType` TEXT NULL,
  `Filename` TEXT NULL,
  `Extension` TEXT NULL,
  `IsNew` TINYINT(1) NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `EmailAccount`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `DisplayName` VARCHAR(255) NULL,
  `Email` VARCHAR(255) NOT NULL,
  `Host` VARCHAR(255) NOT NULL,
  `Username` VARCHAR(255) NOT NULL,
  `Password` VARCHAR(255) NOT NULL,
  `Port` INT NOT NULL,
  `EnableSsl` TINYINT(1) NOT NULL,
  `UseDefaultCredentials` TINYINT(1) NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ExternalAuthenticationRecord`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `CustomerId` INT NOT NULL,
  `Email` TEXT NULL,
  `ExternalIdentifier` TEXT NULL,
  `ExternalDisplayIdentifier` TEXT NULL,
  `OAuthToken` TEXT NULL,
  `OAuthAccessToken` TEXT NULL,
  `ProviderSystemName` TEXT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `FacebookPixelConfiguration`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `PixelId` TEXT NULL,
  `Enabled` TINYINT(1) NOT NULL,
  `DisableForUsersNotAcceptingCookieConsent` TINYINT(1) NOT NULL,
  `StoreId` INT NOT NULL,
  `PassUserProperties` TINYINT(1) NOT NULL,
  `UseAdvancedMatching` TINYINT(1) NOT NULL,
  `TrackPageView` TINYINT(1) NOT NULL,
  `TrackAddToCart` TINYINT(1) NOT NULL,
  `TrackPurchase` TINYINT(1) NOT NULL,
  `TrackViewContent` TINYINT(1) NOT NULL,
  `TrackAddToWishlist` TINYINT(1) NOT NULL,
  `TrackInitiateCheckout` TINYINT(1) NOT NULL,
  `TrackSearch` TINYINT(1) NOT NULL,
  `TrackContact` TINYINT(1) NOT NULL,
  `TrackCompleteRegistration` TINYINT(1) NOT NULL,
  `CustomEvents` TEXT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Forums_Forum`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(200) NOT NULL,
  `ForumGroupId` INT NOT NULL,
  `Description` TEXT NULL,
  `NumTopics` INT NOT NULL,
  `NumPosts` INT NOT NULL,
  `LastTopicId` INT NOT NULL,
  `LastPostId` INT NOT NULL,
  `LastPostCustomerId` INT NOT NULL,
  `LastPostTime` DATETIME NULL,
  `DisplayOrder` INT NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  `UpdatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Forums_Group`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(200) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  `UpdatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Forums_Post`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Text` TEXT NOT NULL,
  `IPAddress` VARCHAR(100) NULL,
  `CustomerId` INT NOT NULL,
  `TopicId` INT NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  `UpdatedOnUtc` DATETIME NOT NULL,
  `VoteCount` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Forums_PostVote`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `ForumPostId` INT NOT NULL,
  `CustomerId` INT NOT NULL,
  `IsUp` TINYINT(1) NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Forums_PrivateMessage`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Subject` VARCHAR(450) NOT NULL,
  `Text` TEXT NOT NULL,
  `FromCustomerId` INT NOT NULL,
  `ToCustomerId` INT NOT NULL,
  `StoreId` INT NOT NULL,
  `IsRead` TINYINT(1) NOT NULL,
  `IsDeletedByAuthor` TINYINT(1) NOT NULL,
  `IsDeletedByRecipient` TINYINT(1) NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Forums_Subscription`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `CustomerId` INT NOT NULL,
  `SubscriptionGuid` VARCHAR(36) NOT NULL,
  `ForumId` INT NOT NULL,
  `TopicId` INT NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Forums_Topic`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Subject` VARCHAR(450) NOT NULL,
  `CustomerId` INT NOT NULL,
  `ForumId` INT NOT NULL,
  `TopicTypeId` INT NOT NULL,
  `NumPosts` INT NOT NULL,
  `Views` INT NOT NULL,
  `LastPostId` INT NOT NULL,
  `LastPostCustomerId` INT NOT NULL,
  `LastPostTime` DATETIME NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  `UpdatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `GdprConsent`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Message` TEXT NOT NULL,
  `IsRequired` TINYINT(1) NOT NULL,
  `RequiredMessage` TEXT NULL,
  `DisplayDuringRegistration` TINYINT(1) NOT NULL,
  `DisplayOnCustomerInfoPage` TINYINT(1) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `GdprLog`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `CustomerId` INT NOT NULL,
  `ConsentId` INT NOT NULL,
  `CustomerInfo` TEXT NULL,
  `RequestTypeId` INT NOT NULL,
  `RequestDetails` TEXT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `GenericAttribute`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `KeyGroup` VARCHAR(400) NOT NULL,
  `Key` VARCHAR(400) NOT NULL,
  `Value` TEXT NOT NULL,
  `EntityId` INT NOT NULL,
  `StoreId` INT NOT NULL,
  `CreatedOrUpdatedDateUTC` DATETIME NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `GiftCard`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `PurchasedWithOrderItemId` INT NULL,
  `GiftCardTypeId` INT NOT NULL,
  `Amount` DECIMAL(18, 4) NOT NULL,
  `IsGiftCardActivated` TINYINT(1) NOT NULL,
  `GiftCardCouponCode` TEXT NULL,
  `RecipientName` TEXT NULL,
  `RecipientEmail` TEXT NULL,
  `SenderName` TEXT NULL,
  `SenderEmail` TEXT NULL,
  `Message` TEXT NULL,
  `IsRecipientNotified` TINYINT(1) NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `GiftCardUsageHistory`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `GiftCardId` INT NOT NULL,
  `UsedWithOrderId` INT NOT NULL,
  `UsedValue` DECIMAL(18, 4) NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Language`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(100) NOT NULL,
  `LanguageCulture` VARCHAR(20) NOT NULL,
  `UniqueSeoCode` VARCHAR(2) NULL,
  `FlagImageFileName` VARCHAR(50) NULL,
  `Rtl` TINYINT(1) NOT NULL,
  `LimitedToStores` TINYINT(1) NOT NULL,
  `DefaultCurrencyId` INT NOT NULL,
  `Published` TINYINT(1) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `LocaleStringResource`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `ResourceName` VARCHAR(200) NOT NULL,
  `ResourceValue` TEXT NOT NULL,
  `LanguageId` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `LocalizedProperty`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `LocaleKeyGroup` VARCHAR(400) NOT NULL,
  `LocaleKey` VARCHAR(400) NOT NULL,
  `LocaleValue` TEXT NOT NULL,
  `LanguageId` INT NOT NULL,
  `EntityId` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Log`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `ShortMessage` TEXT NOT NULL,
  `IpAddress` VARCHAR(200) NULL,
  `CustomerId` INT NULL,
  `LogLevelId` INT NOT NULL,
  `FullMessage` TEXT NULL,
  `PageUrl` TEXT NULL,
  `ReferrerUrl` TEXT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Manufacturer`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `MetaKeywords` VARCHAR(400) NULL,
  `MetaTitle` VARCHAR(400) NULL,
  `PriceRanges` VARCHAR(400) NULL,
  `PageSizeOptions` VARCHAR(200) NULL,
  `Description` TEXT NULL,
  `ManufacturerTemplateId` INT NOT NULL,
  `MetaDescription` TEXT NULL,
  `PictureId` INT NOT NULL,
  `PageSize` INT NOT NULL,
  `AllowCustomersToSelectPageSize` TINYINT(1) NOT NULL,
  `SubjectToAcl` TINYINT(1) NOT NULL,
  `LimitedToStores` TINYINT(1) NOT NULL,
  `Published` TINYINT(1) NOT NULL,
  `Deleted` TINYINT(1) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  `UpdatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ManufacturerTemplate`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `ViewPath` VARCHAR(400) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `MeasureDimension`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(100) NOT NULL,
  `SystemKeyword` VARCHAR(100) NOT NULL,
  `Ratio` DECIMAL(18, 8) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `MeasureWeight`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(100) NOT NULL,
  `SystemKeyword` VARCHAR(100) NOT NULL,
  `Ratio` DECIMAL(18, 8) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `MessageTemplate`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(200) NOT NULL,
  `BccEmailAddresses` VARCHAR(200) NULL,
  `Subject` VARCHAR(1000) NULL,
  `EmailAccountId` INT NOT NULL,
  `Body` TEXT NULL,
  `IsActive` TINYINT(1) NOT NULL,
  `DelayBeforeSend` INT NULL,
  `DelayPeriodId` INT NOT NULL,
  `AttachedDownloadId` INT NOT NULL,
  `LimitedToStores` TINYINT(1) NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `MigrationVersionInfo`(
  `Version` BIGINT NOT NULL,
  `AppliedOn` DATETIME NULL,
  `Description` VARCHAR(1024) NULL,
  PRIMARY KEY (`Version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `News`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Title` TEXT NOT NULL,
  `Short` TEXT NOT NULL,
  `Full` TEXT NOT NULL,
  `MetaKeywords` VARCHAR(400) NULL,
  `MetaTitle` VARCHAR(400) NULL,
  `LanguageId` INT NOT NULL,
  `Published` TINYINT(1) NOT NULL,
  `StartDateUtc` DATETIME NULL,
  `EndDateUtc` DATETIME NULL,
  `AllowComments` TINYINT(1) NOT NULL,
  `LimitedToStores` TINYINT(1) NOT NULL,
  `MetaDescription` TEXT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `NewsComment`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `CustomerId` INT NOT NULL,
  `NewsItemId` INT NOT NULL,
  `StoreId` INT NOT NULL,
  `CommentTitle` TEXT NULL,
  `CommentText` TEXT NULL,
  `IsApproved` TINYINT(1) NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `NewsLetterSubscription`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Email` VARCHAR(255) NOT NULL,
  `NewsLetterSubscriptionGuid` VARCHAR(36) NOT NULL,
  `Active` TINYINT(1) NOT NULL,
  `StoreId` INT NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Order`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `CustomOrderNumber` TEXT NOT NULL,
  `BillingAddressId` INT NOT NULL,
  `CustomerId` INT NOT NULL,
  `PickupAddressId` INT NULL,
  `ShippingAddressId` INT NULL,
  `OrderGuid` VARCHAR(36) NOT NULL,
  `StoreId` INT NOT NULL,
  `PickupInStore` TINYINT(1) NOT NULL,
  `OrderStatusId` INT NOT NULL,
  `ShippingStatusId` INT NOT NULL,
  `PaymentStatusId` INT NOT NULL,
  `PaymentMethodSystemName` TEXT NULL,
  `CustomerCurrencyCode` TEXT NULL,
  `CurrencyRate` DECIMAL(18, 4) NOT NULL,
  `CustomerTaxDisplayTypeId` INT NOT NULL,
  `VatNumber` TEXT NULL,
  `OrderSubtotalInclTax` DECIMAL(18, 4) NOT NULL,
  `OrderSubtotalExclTax` DECIMAL(18, 4) NOT NULL,
  `OrderSubTotalDiscountInclTax` DECIMAL(18, 4) NOT NULL,
  `OrderSubTotalDiscountExclTax` DECIMAL(18, 4) NOT NULL,
  `OrderShippingInclTax` DECIMAL(18, 4) NOT NULL,
  `OrderShippingExclTax` DECIMAL(18, 4) NOT NULL,
  `PaymentMethodAdditionalFeeInclTax` DECIMAL(18, 4) NOT NULL,
  `PaymentMethodAdditionalFeeExclTax` DECIMAL(18, 4) NOT NULL,
  `TaxRates` TEXT NULL,
  `OrderTax` DECIMAL(18, 4) NOT NULL,
  `OrderDiscount` DECIMAL(18, 4) NOT NULL,
  `OrderTotal` DECIMAL(18, 4) NOT NULL,
  `RefundedAmount` DECIMAL(18, 4) NOT NULL,
  `RewardPoINTsHistoryEntryId` INT NULL,
  `CheckoutAttributeDescription` TEXT NULL,
  `CheckoutAttributesTEXT` TEXT NULL,
  `CustomerLanguageId` INT NOT NULL,
  `AffiliateId` INT NOT NULL,
  `CustomerIp` TEXT NULL,
  `AllowStoringCreditCardNumber` TINYINT(1) NOT NULL,
  `CardType` TEXT NULL,
  `CardName` TEXT NULL,
  `CardNumber` TEXT NULL,
  `MaskedCreditCardNumber` TEXT NULL,
  `CardCvv2` TEXT NULL,
  `CardExpirationMonth` TEXT NULL,
  `CardExpirationYear` TEXT NULL,
  `AuthorizationTransactionId` TEXT NULL,
  `AuthorizationTransactionCode` TEXT NULL,
  `AuthorizationTransactionResult` TEXT NULL,
  `CaptureTransactionId` TEXT NULL,
  `CaptureTransactionResult` TEXT NULL,
  `SubscriptionTransactionId` TEXT NULL,
  `PaidDateUtc` DATETIME NULL,
  `ShippingMethod` TEXT NULL,
  `ShippingRateComputationMethodSystemName` TEXT NULL,
  `CustomValuesTEXT` TEXT NULL,
  `Deleted` TINYINT(1) NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  `RedeemedRewardPoINTsEntryId` INT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `OrderItem`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `OrderId` INT NOT NULL,
  `ProductId` INT NOT NULL,
  `OrderItemGuid` VARCHAR(36) NOT NULL,
  `Quantity` INT NOT NULL,
  `UnitPriceInclTax` DECIMAL(18, 4) NOT NULL,
  `UnitPriceExclTax` DECIMAL(18, 4) NOT NULL,
  `PriceInclTax` DECIMAL(18, 4) NOT NULL,
  `PriceExclTax` DECIMAL(18, 4) NOT NULL,
  `DiscountAmountInclTax` DECIMAL(18, 4) NOT NULL,
  `DiscountAmountExclTax` DECIMAL(18, 4) NOT NULL,
  `OriginalProductCost` DECIMAL(18, 4) NOT NULL,
  `AttributeDescription` TEXT NULL,
  `AttributesTEXT` TEXT NULL,
  `DownloadCount` INT NOT NULL,
  `IsDownloadActivated` TINYINT(1) NOT NULL,
  `LicenseDownloadId` INT NULL,
  `ItemWeight` DECIMAL(18, 4) NULL,
  `RentalStartDateUtc` DATETIME NULL,
  `RentalEndDateUtc` DATETIME NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `OrderNote`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Note` TEXT NOT NULL,
  `OrderId` INT NOT NULL,
  `DownloadId` INT NOT NULL,
  `DisplayToCustomer` TINYINT(1) NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `PermissionRecord`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` TEXT NOT NULL,
  `SystemName` VARCHAR(255) NOT NULL,
  `Category` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `PermissionRecord_Role_Mapping`(
  `PermissionRecord_Id` INT NOT NULL,
  `CustomerRole_Id` INT NOT NULL,
  PRIMARY KEY (`PermissionRecord_Id`, `CustomerRole_Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Picture`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `MimeType` VARCHAR(40) NOT NULL,
  `SeoFilename` VARCHAR(300) NULL,
  `AltAttribute` TEXT NULL,
  `TitleAttribute` TEXT NULL,
  `IsNew` TINYINT(1) NOT NULL,
  `VirtualPath` TEXT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `PictureBinary`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `PictureId` INT NOT NULL,
  `BinaryData` LONGBLOB NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Poll`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` TEXT NOT NULL,
  `LanguageId` INT NOT NULL,
  `SystemKeyword` TEXT NULL,
  `Published` TINYINT(1) NOT NULL,
  `ShowOnHomepage` TINYINT(1) NOT NULL,
  `AllowGuestsToVote` TINYINT(1) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  `LimitedToStores` TINYINT(1) NOT NULL,
  `StartDateUtc` DATETIME NULL,
  `EndDateUtc` DATETIME NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `PollAnswer`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` TEXT NOT NULL,
  `PollId` INT NOT NULL,
  `NumberOfVotes` INT NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `PollVotingRecord`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `PollAnswerId` INT NOT NULL,
  `CustomerId` INT NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `PredefinedProductAttributeValue`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `ProductAttributeId` INT NOT NULL,
  `PriceAdjustment` DECIMAL(18, 4) NOT NULL,
  `PriceAdjustmentUsePercentage` TINYINT(1) NOT NULL,
  `WeightAdjustment` DECIMAL(18, 4) NOT NULL,
  `Cost` DECIMAL(18, 4) NOT NULL,
  `IsPreSelected` TINYINT(1) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Product`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `MetaKeywords` VARCHAR(400) NULL,
  `MetaTitle` VARCHAR(400) NULL,
  `Sku` VARCHAR(400) NULL,
  `ManufacturerPartNumber` VARCHAR(400) NULL,
  `Gtin` VARCHAR(400) NULL,
  `RequiredProductIds` VARCHAR(1000) NULL,
  `AllowedQuantities` VARCHAR(1000) NULL,
  `ProductTypeId` INT NOT NULL,
  `ParentGroupedProductId` INT NOT NULL,
  `VisibleIndividually` TINYINT(1) NOT NULL,
  `ShortDescription` TEXT NULL,
  `FullDescription` TEXT NULL,
  `AdminComment` TEXT NULL,
  `ProductTemplateId` INT NOT NULL,
  `VendorId` INT NOT NULL,
  `ShowOnHomepage` TINYINT(1) NOT NULL,
  `MetaDescription` TEXT NULL,
  `AllowCustomerReviews` TINYINT(1) NOT NULL,
  `ApprovedRatingSum` INT NOT NULL,
  `NotApprovedRatingSum` INT NOT NULL,
  `ApprovedTotalReviews` INT NOT NULL,
  `NotApprovedTotalReviews` INT NOT NULL,
  `SubjectToAcl` TINYINT(1) NOT NULL,
  `LimitedToStores` TINYINT(1) NOT NULL,
  `IsGiftCard` TINYINT(1) NOT NULL,
  `GiftCardTypeId` INT NOT NULL,
  `OverriddenGiftCardAmount` DECIMAL(18, 4) NULL,
  `RequireOtherProducts` TINYINT(1) NOT NULL,
  `AutomaticallyAddRequiredProducts` TINYINT(1) NOT NULL,
  `IsDownload` TINYINT(1) NOT NULL,
  `DownloadId` INT NOT NULL,
  `UnlimitedDownloads` TINYINT(1) NOT NULL,
  `MaxNumberOfDownloads` INT NOT NULL,
  `DownloadExpirationDays` INT NULL,
  `DownloadActivationTypeId` INT NOT NULL,
  `HasSampleDownload` TINYINT(1) NOT NULL,
  `SampleDownloadId` INT NOT NULL,
  `HasUserAgreement` TINYINT(1) NOT NULL,
  `UserAgreementText` TEXT NULL,
  `IsRecurring` TINYINT(1) NOT NULL,
  `RecurringCycleLength` INT NOT NULL,
  `RecurringCyclePeriodId` INT NOT NULL,
  `RecurringTotalCycles` INT NOT NULL,
  `IsRental` TINYINT(1) NOT NULL,
  `RentalPriceLength` INT NOT NULL,
  `RentalPricePeriodId` INT NOT NULL,
  `IsShipEnabled` TINYINT(1) NOT NULL,
  `IsFreeShipping` TINYINT(1) NOT NULL,
  `ShipSeparately` TINYINT(1) NOT NULL,
  `AdditionalShippingCharge` DECIMAL(18, 4) NOT NULL,
  `DeliveryDateId` INT NOT NULL,
  `IsTaxExempt` TINYINT(1) NOT NULL,
  `TaxCategoryId` INT NOT NULL,
  `IsTelecommunicationsOrBroadcastingOrElectronicServices` TINYINT(1) NOT NULL,
  `ManageInventoryMethodId` INT NOT NULL,
  `ProductAvailabilityRangeId` INT NOT NULL,
  `UseMultipleWarehouses` TINYINT(1) NOT NULL,
  `WarehouseId` INT NOT NULL,
  `StockQuantity` INT NOT NULL,
  `DisplayStockAvailability` TINYINT(1) NOT NULL,
  `DisplayStockQuantity` TINYINT(1) NOT NULL,
  `MinStockQuantity` INT NOT NULL,
  `LowStockActivityId` INT NOT NULL,
  `NotifyAdminForQuantityBelow` INT NOT NULL,
  `BackorderModeId` INT NOT NULL,
  `AllowBackInStockSubscriptions` TINYINT(1) NOT NULL,
  `OrderMinimumQuantity` INT NOT NULL,
  `OrderMaximumQuantity` INT NOT NULL,
  `AllowAddingOnlyExistingAttributeCombinations` TINYINT(1) NOT NULL,
  `NotReturnable` TINYINT(1) NOT NULL,
  `DisableBuyButton` TINYINT(1) NOT NULL,
  `DisableWishlistButton` TINYINT(1) NOT NULL,
  `AvailableForPreOrder` TINYINT(1) NOT NULL,
  `PreOrderAvailabilityStartDATETIMEUtc` DATETIME NULL,
  `CallForPrice` TINYINT(1) NOT NULL,
  `Price` DECIMAL(18, 4) NOT NULL,
  `OldPrice` DECIMAL(18, 4) NOT NULL,
  `ProductCost` DECIMAL(18, 4) NOT NULL,
  `CustomerEntersPrice` TINYINT(1) NOT NULL,
  `MinimumCustomerEnteredPrice` DECIMAL(18, 4) NOT NULL,
  `MaximumCustomerEnteredPrice` DECIMAL(18, 4) NOT NULL,
  `BasepriceEnabled` TINYINT(1) NOT NULL,
  `BasepriceAmount` DECIMAL(18, 4) NOT NULL,
  `BasepriceUnitId` INT NOT NULL,
  `BasepriceBaseAmount` DECIMAL(18, 4) NOT NULL,
  `BasepriceBaseUnitId` INT NOT NULL,
  `MarkAsNew` TINYINT(1) NOT NULL,
  `MarkAsNewStartDATETIMEUtc` DATETIME NULL,
  `MarkAsNewEndDATETIMEUtc` DATETIME NULL,
  `HasTierPrices` TINYINT(1) NOT NULL,
  `HasDiscountsApplied` TINYINT(1) NOT NULL,
  `Weight` DECIMAL(18, 4) NOT NULL,
  `Length` DECIMAL(18, 4) NOT NULL,
  `Width` DECIMAL(18, 4) NOT NULL,
  `Height` DECIMAL(18, 4) NOT NULL,
  `AvailableStartDATETIMEUtc` DATETIME NULL,
  `AvailableEndDATETIMEUtc` DATETIME NULL,
  `DisplayOrder` INT NOT NULL,
  `Published` TINYINT(1) NOT NULL,
  `Deleted` TINYINT(1) NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  `UpdatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Product_Category_Mapping`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `CategoryId` INT NOT NULL,
  `ProductId` INT NOT NULL,
  `IsFeaturedProduct` TINYINT(1) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Product_Manufacturer_Mapping`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `ManufacturerId` INT NOT NULL,
  `ProductId` INT NOT NULL,
  `IsFeaturedProduct` TINYINT(1) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Product_Picture_Mapping`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `PictureId` INT NOT NULL,
  `ProductId` INT NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Product_ProductAttribute_Mapping`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `ProductAttributeId` INT NOT NULL,
  `ProductId` INT NOT NULL,
  `TextPrompt` TEXT NULL,
  `IsRequired` TINYINT(1) NOT NULL,
  `AttributeControlTypeId` INT NOT NULL,
  `DisplayOrder` INT NOT NULL,
  `ValidationMinLength` INT NULL,
  `ValidationMaxLength` INT NULL,
  `ValidationFileAllowedExtensions` TEXT NULL,
  `ValidationFileMaximumSize` INT NULL,
  `DefaultValue` TEXT NULL,
  `ConditionAttributeTEXT` TEXT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Product_ProductTag_Mapping`(
  `Product_Id` INT NOT NULL,
  `ProductTag_Id` INT NOT NULL,
  PRIMARY KEY (`Product_Id`, `ProductTag_Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Product_SpecificationAttribute_Mapping`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `CustomValue` VARCHAR(4000) NULL,
  `ProductId` INT NOT NULL,
  `SpecificationAttributeOptionId` INT NOT NULL,
  `AttributeTypeId` INT NOT NULL,
  `AllowFiltering` TINYINT(1) NOT NULL,
  `ShowOnProductPage` TINYINT(1) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ProductAttribute`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` TEXT NOT NULL,
  `Description` TEXT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ProductAttributeCombination`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Sku` VARCHAR(400) NULL,
  `ManufacturerPartNumber` VARCHAR(400) NULL,
  `Gtin` VARCHAR(400) NULL,
  `ProductId` INT NOT NULL,
  `AttributesTEXT` TEXT NULL,
  `StockQuantity` INT NOT NULL,
  `AllowOutOfStockOrders` TINYINT(1) NOT NULL,
  `OverriddenPrice` DECIMAL(18, 4) NULL,
  `NotifyAdminForQuantityBelow` INT NOT NULL,
  `PictureId` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ProductAttributeValue`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `ColorSquaresRgb` VARCHAR(100) NULL,
  `ProductAttributeMappingId` INT NOT NULL,
  `AttributeValueTypeId` INT NOT NULL,
  `AssociatedProductId` INT NOT NULL,
  `ImageSquaresPictureId` INT NOT NULL,
  `PriceAdjustment` DECIMAL(18, 4) NOT NULL,
  `PriceAdjustmentUsePercentage` TINYINT(1) NOT NULL,
  `WeightAdjustment` DECIMAL(18, 4) NOT NULL,
  `Cost` DECIMAL(18, 4) NOT NULL,
  `CustomerEntersQty` TINYINT(1) NOT NULL,
  `Quantity` INT NOT NULL,
  `IsPreSelected` TINYINT(1) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  `PictureId` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ProductAvailabilityRange`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ProductReview`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `CustomerId` INT NOT NULL,
  `ProductId` INT NOT NULL,
  `StoreId` INT NOT NULL,
  `IsApproved` TINYINT(1) NOT NULL,
  `Title` TEXT NULL,
  `ReviewText` TEXT NULL,
  `ReplyText` TEXT NULL,
  `CustomerNotifiedOfReply` TINYINT(1) NOT NULL,
  `Rating` INT NOT NULL,
  `HelpfulYesTotal` INT NOT NULL,
  `HelpfulNoTotal` INT NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ProductReview_ReviewType_Mapping`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `ProductReviewId` INT NOT NULL,
  `ReviewTypeId` INT NOT NULL,
  `Rating` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ProductReviewHelpfulness`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `ProductReviewId` INT NOT NULL,
  `WasHelpful` TINYINT(1) NOT NULL,
  `CustomerId` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ProductTag`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ProductTemplate`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `ViewPath` VARCHAR(400) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  `IgnoredProductTypes` TEXT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ProductWarehouseInventory`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `ProductId` INT NOT NULL,
  `WarehouseId` INT NOT NULL,
  `StockQuantity` INT NOT NULL,
  `ReservedQuantity` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `QueuedEmail`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `From` VARCHAR(500) NOT NULL,
  `FromName` VARCHAR(500) NULL,
  `To` VARCHAR(500) NOT NULL,
  `ToName` VARCHAR(500) NULL,
  `ReplyTo` VARCHAR(500) NULL,
  `ReplyToName` VARCHAR(500) NULL,
  `CC` VARCHAR(500) NULL,
  `Bcc` VARCHAR(500) NULL,
  `Subject` VARCHAR(1000) NULL,
  `EmailAccountId` INT NOT NULL,
  `PriorityId` INT NOT NULL,
  `Body` TEXT NULL,
  `AttachmentFilePath` TEXT NULL,
  `AttachmentFileName` TEXT NULL,
  `AttachedDownloadId` INT NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  `DontSendBeforeDateUtc` DATETIME NULL,
  `SentTries` INT NOT NULL,
  `SentOnUtc` DATETIME NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `RecurringPayment`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `InitialOrderId` INT NOT NULL,
  `CycleLength` INT NOT NULL,
  `CyclePeriodId` INT NOT NULL,
  `TotalCycles` INT NOT NULL,
  `StartDateUtc` DATETIME NOT NULL,
  `IsActive` TINYINT(1) NOT NULL,
  `LastPaymentFailed` TINYINT(1) NOT NULL,
  `Deleted` TINYINT(1) NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `RecurringPaymentHistory`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `RecurringPaymentId` INT NOT NULL,
  `OrderId` INT NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `RelatedProduct`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `ProductId1` INT NOT NULL,
  `ProductId2` INT NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ReturnRequest`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `ReasonForReturn` TEXT NOT NULL,
  `RequestedAction` TEXT NOT NULL,
  `CustomerId` INT NOT NULL,
  `CustomNumber` TEXT NULL,
  `StoreId` INT NOT NULL,
  `OrderItemId` INT NOT NULL,
  `Quantity` INT NOT NULL,
  `CustomerComments` TEXT NULL,
  `UploadedFileId` INT NOT NULL,
  `StaffNotes` TEXT NULL,
  `ReturnRequestStatusId` INT NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  `UpdatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ReturnRequestAction`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ReturnRequestReason`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ReviewType`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `Description` VARCHAR(400) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  `VisibleToAllCustomers` TINYINT(1) NOT NULL,
  `IsRequired` TINYINT(1) NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `RewardPointsHistory`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `CustomerId` INT NOT NULL,
  `StoreId` INT NOT NULL,
  `PoINTs` INT NOT NULL,
  `PoINTsBalance` INT NULL,
  `UsedAmount` DECIMAL(18, 4) NOT NULL,
  `Message` TEXT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  `EndDateUtc` DATETIME NULL,
  `ValidPoINTs` INT NULL,
  `UsedWithOrder` VARCHAR(36) NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ScheduleTask`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` TEXT NOT NULL,
  `Type` TEXT NOT NULL,
  `Seconds` INT NOT NULL,
  `Enabled` TINYINT(1) NOT NULL,
  `StopOnError` TINYINT(1) NOT NULL,
  `LastStartUtc` DATETIME NULL,
  `LastEndUtc` DATETIME NULL,
  `LastSuccessUtc` DATETIME NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `SearchTerm`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Keyword` TEXT NULL,
  `StoreId` INT NOT NULL,
  `Count` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Setting`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(200) NOT NULL,
  `Value` TEXT NOT NULL,
  `StoreId` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Shipment`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `OrderId` INT NOT NULL,
  `TrackingNumber` TEXT NULL,
  `TotalWeight` DECIMAL(18, 4) NULL,
  `ShippedDateUtc` DATETIME NULL,
  `DeliveryDateUtc` DATETIME NULL,
  `AdminComment` TEXT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ShipmentItem`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `ShipmentId` INT NOT NULL,
  `OrderItemId` INT NOT NULL,
  `Quantity` INT NOT NULL,
  `WarehouseId` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ShippingByWeightByTotalRecord`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `WeightFrom` DECIMAL(18, 2) NOT NULL,
  `WeightTo` DECIMAL(18, 2) NOT NULL,
  `OrderSubtotalFrom` DECIMAL(18, 2) NOT NULL,
  `OrderSubtotalTo` DECIMAL(18, 2) NOT NULL,
  `AdditionalFixedCost` DECIMAL(18, 2) NOT NULL,
  `PercentageRateOfSubtotal` DECIMAL(18, 2) NOT NULL,
  `RatePerWeightUnit` DECIMAL(18, 2) NOT NULL,
  `LowerWeightLimit` DECIMAL(18, 2) NOT NULL,
  `Zip` VARCHAR(400) NULL,
  `StoreId` INT NOT NULL,
  `WarehouseId` INT NOT NULL,
  `CountryId` INT NOT NULL,
  `StateProvinceId` INT NOT NULL,
  `ShippingMethodId` INT NOT NULL,
  `TransitDays` INT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ShippingMethod`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `Description` TEXT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ShippingMethodRestrictions`(
  `ShippingMethod_Id` INT NOT NULL,
  `Country_Id` INT NOT NULL,
  PRIMARY KEY (`ShippingMethod_Id`, `Country_Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ShoppingCartItem`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `CustomerId` INT NOT NULL,
  `ProductId` INT NOT NULL,
  `StoreId` INT NOT NULL,
  `ShoppingCartTypeId` INT NOT NULL,
  `AttributesTEXT` TEXT NULL,
  `CustomerEnteredPrice` DECIMAL(18, 4) NOT NULL,
  `Quantity` INT NOT NULL,
  `RentalStartDateUtc` DATETIME NULL,
  `RentalEndDateUtc` DATETIME NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  `UpdatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `SpecificationAttribute`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` TEXT NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `SpecificationAttributeOption`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` TEXT NOT NULL,
  `ColorSquaresRgb` VARCHAR(100) NULL,
  `SpecificationAttributeId` INT NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `StateProvince`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(100) NOT NULL,
  `Abbreviation` VARCHAR(100) NULL,
  `CountryId` INT NOT NULL,
  `Published` TINYINT(1) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `StockQuantityHistory`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `ProductId` INT NOT NULL,
  `QuantityAdjustment` INT NOT NULL,
  `StockQuantity` INT NOT NULL,
  `Message` TEXT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  `CombinationId` INT NULL,
  `WarehouseId` INT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Store`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `Url` VARCHAR(400) NOT NULL,
  `Hosts` VARCHAR(1000) NULL,
  `CompanyName` VARCHAR(1000) NULL,
  `CompanyAddress` VARCHAR(1000) NULL,
  `CompanyPhoneNumber` VARCHAR(1000) NULL,
  `CompanyVat` VARCHAR(1000) NULL,
  `SslEnabled` TINYINT(1) NOT NULL,
  `DefaultLanguageId` INT NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `StoreMapping`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `EntityName` VARCHAR(400) NOT NULL,
  `StoreId` INT NOT NULL,
  `EntityId` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `StorePickupPoint`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` TEXT NULL,
  `Description` TEXT NULL,
  `AddressId` INT NOT NULL,
  `PickupFee` DECIMAL(18, 4) NOT NULL,
  `OpeningHours` TEXT NULL,
  `DisplayOrder` INT NOT NULL,
  `StoreId` INT NOT NULL,
  `Latitude` DECIMAL(18, 4) NULL,
  `Longitude` DECIMAL(18, 4) NULL,
  `TransitDays` INT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `TaxCategory`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `TaxRate`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `StoreId` INT NOT NULL,
  `TaxCategoryId` INT NOT NULL,
  `CountryId` INT NOT NULL,
  `StateProvinceId` INT NOT NULL,
  `Zip` TEXT NULL,
  `Percentage` DECIMAL(18, 4) NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `TaxTransactionLog`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `StatusCode` INT NOT NULL,
  `Url` TEXT NULL,
  `RequestMessage` TEXT NULL,
  `ResponseMessage` TEXT NULL,
  `CustomerId` INT NOT NULL,
  `CreatedDateUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `TierPrice`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `CustomerRoleId` INT NULL,
  `ProductId` INT NOT NULL,
  `StoreId` INT NOT NULL,
  `Quantity` INT NOT NULL,
  `Price` DECIMAL(18, 4) NOT NULL,
  `StartDATETIMEUtc` DATETIME NULL,
  `EndDATETIMEUtc` DATETIME NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Topic`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `SystemName` TEXT NULL,
  `IncludeInSitemap` TINYINT(1) NOT NULL,
  `IncludeINTopMenu` TINYINT(1) NOT NULL,
  `IncludeInFooterColumn1` TINYINT(1) NOT NULL,
  `IncludeInFooterColumn2` TINYINT(1) NOT NULL,
  `IncludeInFooterColumn3` TINYINT(1) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  `AccessibleWhenStoreClosed` TINYINT(1) NOT NULL,
  `IsPasswordProtected` TINYINT(1) NOT NULL,
  `Password` TEXT NULL,
  `Title` TEXT NULL,
  `Body` TEXT NULL,
  `Published` TINYINT(1) NOT NULL,
  `TopicTemplateId` INT NOT NULL,
  `MetaKeywords` TEXT NULL,
  `MetaDescription` TEXT NULL,
  `MetaTitle` TEXT NULL,
  `SubjectToAcl` TINYINT(1) NOT NULL,
  `LimitedToStores` TINYINT(1) NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `TopicTemplate`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `ViewPath` VARCHAR(400) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `UrlRecord`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `EntityName` VARCHAR(400) NOT NULL,
  `Slug` VARCHAR(400) NOT NULL,
  `EntityId` INT NOT NULL,
  `IsActive` TINYINT(1) NOT NULL,
  `LanguageId` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Vendor`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `Email` VARCHAR(400) NULL,
  `MetaKeywords` VARCHAR(400) NULL,
  `MetaTitle` VARCHAR(400) NULL,
  `PageSizeOptions` VARCHAR(200) NULL,
  `Description` TEXT NULL,
  `PictureId` INT NOT NULL,
  `AddressId` INT NOT NULL,
  `AdminComment` TEXT NULL,
  `Active` TINYINT(1) NOT NULL,
  `Deleted` TINYINT(1) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  `MetaDescription` TEXT NULL,
  `PageSize` INT NOT NULL,
  `AllowCustomersToSelectPageSize` TINYINT(1) NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `VendorAttribute`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `IsRequired` TINYINT(1) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  `AttributeControlTypeId` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `VendorAttributeValue`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `VendorAttributeId` INT NOT NULL,
  `IsPreSelected` TINYINT(1) NOT NULL,
  `DisplayOrder` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `VendorNote`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Note` TEXT NOT NULL,
  `VendorId` INT NOT NULL,
  `CreatedOnUtc` DATETIME NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Warehouse`(
  `Id` INT AUTO_INCREMENT NOT NULL,
  `Name` VARCHAR(400) NOT NULL,
  `AdminComment` TEXT NULL,
  `AddressId` INT NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE `AclRecord` ADD CONSTRAINT `FK_AclRecord_CustomerRoleId_CustomerRole_Id` FOREIGN KEY (`CustomerRoleId`) REFERENCES `CustomerRole` (`Id`);
ALTER TABLE `ActivityLog` ADD CONSTRAINT `FK_ActivityLog_ActivityLogTypeId_ActivityLogType_Id` FOREIGN KEY (`ActivityLogTypeId`) REFERENCES `ActivityLogType` (`Id`);
ALTER TABLE `ActivityLog` ADD CONSTRAINT `FK_ActivityLog_CustomerId_Customer_Id` FOREIGN KEY (`CustomerId`) REFERENCES `Customer` (`Id`);
ALTER TABLE `Address` ADD CONSTRAINT `FK_Address_CountryId_Country_Id` FOREIGN KEY (`CountryId`) REFERENCES `Country` (`Id`);
ALTER TABLE `Address` ADD CONSTRAINT `FK_Address_StateProvinceId_StateProvince_Id` FOREIGN KEY (`StateProvinceId`) REFERENCES `StateProvince` (`Id`);
ALTER TABLE `AddressAttributeValue` ADD CONSTRAINT `FK_AddressAttributeValue_AddressAttributeId_AddressAttribute_Id` FOREIGN KEY (`AddressAttributeId`) REFERENCES `AddressAttribute` (`Id`);
ALTER TABLE `Affiliate` ADD CONSTRAINT `FK_Affiliate_AddressId_Address_Id` FOREIGN KEY (`AddressId`) REFERENCES `Address` (`Id`);
ALTER TABLE `BackInStockSubscription` ADD CONSTRAINT `FK_BackInStockSubscription_CustomerId_Customer_Id` FOREIGN KEY (`CustomerId`) REFERENCES `Customer` (`Id`);
ALTER TABLE `BackInStockSubscription` ADD CONSTRAINT `FK_BackInStockSubscription_ProductId_Product_Id` FOREIGN KEY (`ProductId`) REFERENCES `Product` (`Id`);
ALTER TABLE `BlogComment` ADD CONSTRAINT `FK_BlogComment_BlogPostId_BlogPost_Id` FOREIGN KEY (`BlogPostId`) REFERENCES `BlogPost` (`Id`);
ALTER TABLE `BlogComment` ADD CONSTRAINT `FK_BlogComment_CustomerId_Customer_Id` FOREIGN KEY (`CustomerId`) REFERENCES `Customer` (`Id`);
ALTER TABLE `BlogComment` ADD CONSTRAINT `FK_BlogComment_StoreId_Store_Id` FOREIGN KEY (`StoreId`) REFERENCES `Store` (`Id`);
ALTER TABLE `BlogPost` ADD CONSTRAINT `FK_BlogPost_LanguageId_Language_Id` FOREIGN KEY (`LanguageId`) REFERENCES `Language` (`Id`);
ALTER TABLE `CheckoutAttributeValue` ADD CONSTRAINT `FK_CheckoutAttrValue_CheckoutAttributeId_CheckoutAttr_Id` FOREIGN KEY (`CheckoutAttributeId`) REFERENCES `CheckoutAttribute` (`Id`);
ALTER TABLE `Customer` ADD CONSTRAINT `FK_Customer_BillingAddress_Id_Address_Id` FOREIGN KEY (`BillingAddress_Id`) REFERENCES `Address` (`Id`);
ALTER TABLE `Customer` ADD CONSTRAINT `FK_Customer_ShippingAddress_Id_Address_Id` FOREIGN KEY (`ShippingAddress_Id`) REFERENCES `Address` (`Id`);
ALTER TABLE `Customer_CustomerRole_Mapping` ADD CONSTRAINT `FK_Customer_CustomerRole_Mapping_Customer_Id_Customer_Id` FOREIGN KEY (`Customer_Id`) REFERENCES `Customer` (`Id`);
ALTER TABLE `Customer_CustomerRole_Mapping` ADD CONSTRAINT `FK_Customer_CustomerRole_Mapping_CustomerRole_Id_CustomerRole_Id` FOREIGN KEY (`CustomerRole_Id`) REFERENCES `CustomerRole` (`Id`);
ALTER TABLE `CustomerAddresses` ADD CONSTRAINT `FK_CustomerAddresses_Address_Id_Address_Id` FOREIGN KEY (`Address_Id`) REFERENCES `Address` (`Id`);
ALTER TABLE `CustomerAddresses` ADD CONSTRAINT `FK_CustomerAddresses_Customer_Id_Customer_Id` FOREIGN KEY (`Customer_Id`) REFERENCES `Customer` (`Id`);
ALTER TABLE `CustomerAttributeValue` ADD CONSTRAINT `FK_CustomerAttrValue_CustomerAttributeId_CustomerAttr_Id` FOREIGN KEY (`CustomerAttributeId`) REFERENCES `CustomerAttribute` (`Id`);
ALTER TABLE `CustomerPassword` ADD CONSTRAINT `FK_CustomerPassword_CustomerId_Customer_Id` FOREIGN KEY (`CustomerId`) REFERENCES `Customer` (`Id`);
ALTER TABLE `Discount_AppliedToCategories` ADD CONSTRAINT `FK_Discount_AppliedToCategories_Category_Id_Category_Id` FOREIGN KEY (`Category_Id`) REFERENCES `Category` (`Id`);
ALTER TABLE `Discount_AppliedToCategories` ADD CONSTRAINT `FK_Discount_AppliedToCategories_Discount_Id_Discount_Id` FOREIGN KEY (`Discount_Id`) REFERENCES `Discount` (`Id`);
ALTER TABLE `Discount_AppliedToManufacturers` ADD CONSTRAINT `FK_Discount_AppliedToManufacturers_Discount_Id_Discount_Id` FOREIGN KEY (`Discount_Id`) REFERENCES `Discount` (`Id`);
ALTER TABLE `Discount_AppliedToManufacturers` ADD CONSTRAINT `FK_Discount_AppliedToMfrs_Manufacturer_Id_Manufacturer_Id` FOREIGN KEY (`Manufacturer_Id`) REFERENCES `Manufacturer` (`Id`);
ALTER TABLE `Discount_AppliedToProducts` ADD CONSTRAINT `FK_Discount_AppliedToProducts_Discount_Id_Discount_Id` FOREIGN KEY (`Discount_Id`) REFERENCES `Discount` (`Id`);
ALTER TABLE `Discount_AppliedToProducts` ADD CONSTRAINT `FK_Discount_AppliedToProducts_Product_Id_Product_Id` FOREIGN KEY (`Product_Id`) REFERENCES `Product` (`Id`);
ALTER TABLE `DiscountRequirement` ADD CONSTRAINT `FK_DiscountRequirement_DiscountId_Discount_Id` FOREIGN KEY (`DiscountId`) REFERENCES `Discount` (`Id`);
ALTER TABLE `DiscountRequirement` ADD CONSTRAINT `FK_DiscountRequirement_ParentId_DiscountRequirement_Id` FOREIGN KEY (`ParentId`) REFERENCES `DiscountRequirement` (`Id`);
ALTER TABLE `DiscountUsageHistory` ADD CONSTRAINT `FK_DiscountUsageHistory_DiscountId_Discount_Id` FOREIGN KEY (`DiscountId`) REFERENCES `Discount` (`Id`);
ALTER TABLE `DiscountUsageHistory` ADD CONSTRAINT `FK_DiscountUsageHistory_OrderId_Order_Id` FOREIGN KEY (`OrderId`) REFERENCES `Order` (`Id`);
ALTER TABLE `ExternalAuthenticationRecord` ADD CONSTRAINT `FK_ExternalAuthenticationRecord_CustomerId_Customer_Id` FOREIGN KEY (`CustomerId`) REFERENCES `Customer` (`Id`);
ALTER TABLE `Forums_Forum` ADD CONSTRAINT `FK_Forums_Forum_ForumGroupId_Forums_Group_Id` FOREIGN KEY (`ForumGroupId`) REFERENCES `Forums_Group` (`Id`);
ALTER TABLE `Forums_Post` ADD CONSTRAINT `FK_Forums_Post_CustomerId_Customer_Id` FOREIGN KEY (`CustomerId`) REFERENCES `Customer` (`Id`);
ALTER TABLE `Forums_Post` ADD CONSTRAINT `FK_Forums_Post_TopicId_Forums_Topic_Id` FOREIGN KEY (`TopicId`) REFERENCES `Forums_Topic` (`Id`);
ALTER TABLE `Forums_PostVote` ADD CONSTRAINT `FK_Forums_PostVote_ForumPostId_Forums_Post_Id` FOREIGN KEY (`ForumPostId`) REFERENCES `Forums_Post` (`Id`);
ALTER TABLE `Forums_PrivateMessage` ADD CONSTRAINT `FK_Forums_PrivateMessage_FromCustomerId_Customer_Id` FOREIGN KEY (`FromCustomerId`) REFERENCES `Customer` (`Id`);
ALTER TABLE `Forums_PrivateMessage` ADD CONSTRAINT `FK_Forums_PrivateMessage_ToCustomerId_Customer_Id` FOREIGN KEY (`ToCustomerId`) REFERENCES `Customer` (`Id`);
ALTER TABLE `Forums_Subscription` ADD CONSTRAINT `FK_Forums_Subscription_CustomerId_Customer_Id` FOREIGN KEY (`CustomerId`) REFERENCES `Customer` (`Id`);
ALTER TABLE `Forums_Topic` ADD CONSTRAINT `FK_Forums_Topic_CustomerId_Customer_Id` FOREIGN KEY (`CustomerId`) REFERENCES `Customer` (`Id`);
ALTER TABLE `Forums_Topic` ADD CONSTRAINT `FK_Forums_Topic_ForumId_Forums_Forum_Id` FOREIGN KEY (`ForumId`) REFERENCES `Forums_Forum` (`Id`);
ALTER TABLE `GiftCard` ADD CONSTRAINT `FK_GiftCard_PurchasedWithOrderItemId_OrderItem_Id` FOREIGN KEY (`PurchasedWithOrderItemId`) REFERENCES `OrderItem` (`Id`);
ALTER TABLE `GiftCardUsageHistory` ADD CONSTRAINT `FK_GiftCardUsageHistory_GiftCardId_GiftCard_Id` FOREIGN KEY (`GiftCardId`) REFERENCES `GiftCard` (`Id`);
ALTER TABLE `GiftCardUsageHistory` ADD CONSTRAINT `FK_GiftCardUsageHistory_UsedWithOrderId_Order_Id` FOREIGN KEY (`UsedWithOrderId`) REFERENCES `Order` (`Id`);
ALTER TABLE `LocalizedProperty` ADD CONSTRAINT `FK_LocalizedProperty_LanguageId_Language_Id` FOREIGN KEY (`LanguageId`) REFERENCES `Language` (`Id`);
ALTER TABLE `Log` ADD CONSTRAINT `FK_Log_CustomerId_Customer_Id` FOREIGN KEY (`CustomerId`) REFERENCES `Customer` (`Id`);
ALTER TABLE `News` ADD CONSTRAINT `FK_News_LanguageId_Language_Id` FOREIGN KEY (`LanguageId`) REFERENCES `Language` (`Id`);
ALTER TABLE `NewsComment` ADD CONSTRAINT `FK_NewsComment_CustomerId_Customer_Id` FOREIGN KEY (`CustomerId`) REFERENCES `Customer` (`Id`);
ALTER TABLE `NewsComment` ADD CONSTRAINT `FK_NewsComment_NewsItemId_News_Id` FOREIGN KEY (`NewsItemId`) REFERENCES `News` (`Id`);
ALTER TABLE `NewsComment` ADD CONSTRAINT `FK_NewsComment_StoreId_Store_Id` FOREIGN KEY (`StoreId`) REFERENCES `Store` (`Id`);
ALTER TABLE `Order` ADD CONSTRAINT `FK_Order_BillingAddressId_Address_Id` FOREIGN KEY (`BillingAddressId`) REFERENCES `Address` (`Id`);
ALTER TABLE `Order` ADD CONSTRAINT `FK_Order_CustomerId_Customer_Id` FOREIGN KEY (`CustomerId`) REFERENCES `Customer` (`Id`);
ALTER TABLE `Order` ADD CONSTRAINT `FK_Order_PickupAddressId_Address_Id` FOREIGN KEY (`PickupAddressId`) REFERENCES `Address` (`Id`);
ALTER TABLE `Order` ADD CONSTRAINT `FK_Order_RewardPointsHistoryEntryId_RewardPointsHistory_Id` FOREIGN KEY (`RewardPointsHistoryEntryId`) REFERENCES `RewardPointsHistory` (`Id`);
ALTER TABLE `Order` ADD CONSTRAINT `FK_Order_ShippingAddressId_Address_Id` FOREIGN KEY (`ShippingAddressId`) REFERENCES `Address` (`Id`);
ALTER TABLE `OrderItem` ADD CONSTRAINT `FK_OrderItem_OrderId_Order_Id` FOREIGN KEY (`OrderId`) REFERENCES `Order` (`Id`);
ALTER TABLE `OrderItem` ADD CONSTRAINT `FK_OrderItem_ProductId_Product_Id` FOREIGN KEY (`ProductId`) REFERENCES `Product` (`Id`);
ALTER TABLE `OrderNote` ADD CONSTRAINT `FK_OrderNote_OrderId_Order_Id` FOREIGN KEY (`OrderId`) REFERENCES `Order` (`Id`);
ALTER TABLE `PermissionRecord_Role_Mapping` ADD CONSTRAINT `FK_PermissionRecord_Role_Mapping_CustomerRole_Id_CustomerRole_Id` FOREIGN KEY (`CustomerRole_Id`) REFERENCES `CustomerRole` (`Id`);
ALTER TABLE `PermissionRecord_Role_Mapping` ADD CONSTRAINT `FK_PermRecordRoleMap_PermissionRecord_Id_PermRecord_Id` FOREIGN KEY (`PermissionRecord_Id`) REFERENCES `PermissionRecord` (`Id`);
ALTER TABLE `PictureBinary` ADD CONSTRAINT `FK_PictureBinary_PictureId_Picture_Id` FOREIGN KEY (`PictureId`) REFERENCES `Picture` (`Id`);
ALTER TABLE `Poll` ADD CONSTRAINT `FK_Poll_LanguageId_Language_Id` FOREIGN KEY (`LanguageId`) REFERENCES `Language` (`Id`);
ALTER TABLE `PollAnswer` ADD CONSTRAINT `FK_PollAnswer_PollId_Poll_Id` FOREIGN KEY (`PollId`) REFERENCES `Poll` (`Id`);
ALTER TABLE `PollVotingRecord` ADD CONSTRAINT `FK_PollVotingRecord_CustomerId_Customer_Id` FOREIGN KEY (`CustomerId`) REFERENCES `Customer` (`Id`);
ALTER TABLE `PollVotingRecord` ADD CONSTRAINT `FK_PollVotingRecord_PollAnswerId_PollAnswer_Id` FOREIGN KEY (`PollAnswerId`) REFERENCES `PollAnswer` (`Id`);
ALTER TABLE `PredefinedProductAttributeValue` ADD CONSTRAINT `FK_PredefinedProdAttrValue_ProductAttributeId_ProdAttr_Id` FOREIGN KEY (`ProductAttributeId`) REFERENCES `ProductAttribute` (`Id`);
ALTER TABLE `Product_Category_Mapping` ADD CONSTRAINT `FK_Product_Category_Mapping_CategoryId_Category_Id` FOREIGN KEY (`CategoryId`) REFERENCES `Category` (`Id`);
ALTER TABLE `Product_Category_Mapping` ADD CONSTRAINT `FK_Product_Category_Mapping_ProductId_Product_Id` FOREIGN KEY (`ProductId`) REFERENCES `Product` (`Id`);
ALTER TABLE `Product_Manufacturer_Mapping` ADD CONSTRAINT `FK_Product_Manufacturer_Mapping_ManufacturerId_Manufacturer_Id` FOREIGN KEY (`ManufacturerId`) REFERENCES `Manufacturer` (`Id`);
ALTER TABLE `Product_Manufacturer_Mapping` ADD CONSTRAINT `FK_Product_Manufacturer_Mapping_ProductId_Product_Id` FOREIGN KEY (`ProductId`) REFERENCES `Product` (`Id`);
ALTER TABLE `Product_Picture_Mapping` ADD CONSTRAINT `FK_Product_Picture_Mapping_PictureId_Picture_Id` FOREIGN KEY (`PictureId`) REFERENCES `Picture` (`Id`);
ALTER TABLE `Product_Picture_Mapping` ADD CONSTRAINT `FK_Product_Picture_Mapping_ProductId_Product_Id` FOREIGN KEY (`ProductId`) REFERENCES `Product` (`Id`);
ALTER TABLE `Product_ProductAttribute_Mapping` ADD CONSTRAINT `FK_Product_ProdAttr_Mapping_ProductAttributeId_ProdAttr_Id` FOREIGN KEY (`ProductAttributeId`) REFERENCES `ProductAttribute` (`Id`);
ALTER TABLE `Product_ProductAttribute_Mapping` ADD CONSTRAINT `FK_Product_ProductAttribute_Mapping_ProductId_Product_Id` FOREIGN KEY (`ProductId`) REFERENCES `Product` (`Id`);
ALTER TABLE `Product_ProductTag_Mapping` ADD CONSTRAINT `FK_Product_ProductTag_Mapping_Product_Id_Product_Id` FOREIGN KEY (`Product_Id`) REFERENCES `Product` (`Id`);
ALTER TABLE `Product_ProductTag_Mapping` ADD CONSTRAINT `FK_Product_ProductTag_Mapping_ProductTag_Id_ProductTag_Id` FOREIGN KEY (`ProductTag_Id`) REFERENCES `ProductTag` (`Id`);
ALTER TABLE `Product_SpecificationAttribute_Mapping` ADD CONSTRAINT `FK_Product_SpecificationAttribute_Mapping_ProductId_Product_Id` FOREIGN KEY (`ProductId`) REFERENCES `Product` (`Id`);
ALTER TABLE `Product_SpecificationAttribute_Mapping` ADD CONSTRAINT `FK_ProdSpecAttrMap_SpecAttrOptionId_SpecAttrOption_Id` FOREIGN KEY (`SpecificationAttributeOptionId`) REFERENCES `SpecificationAttributeOption` (`Id`);
ALTER TABLE `ProductAttributeCombination` ADD CONSTRAINT `FK_ProductAttributeCombination_ProductId_Product_Id` FOREIGN KEY (`ProductId`) REFERENCES `Product` (`Id`);
ALTER TABLE `ProductAttributeValue` ADD CONSTRAINT `FK_ProductAttrValue_ProductAttrMappingId_ProdProdAttrMap_Id` FOREIGN KEY (`ProductAttributeMappingId`) REFERENCES `Product_ProductAttribute_Mapping` (`Id`);
ALTER TABLE `ProductReview` ADD CONSTRAINT `FK_ProductReview_CustomerId_Customer_Id` FOREIGN KEY (`CustomerId`) REFERENCES `Customer` (`Id`);
ALTER TABLE `ProductReview` ADD CONSTRAINT `FK_ProductReview_ProductId_Product_Id` FOREIGN KEY (`ProductId`) REFERENCES `Product` (`Id`);
ALTER TABLE `ProductReview` ADD CONSTRAINT `FK_ProductReview_StoreId_Store_Id` FOREIGN KEY (`StoreId`) REFERENCES `Store` (`Id`);
ALTER TABLE `ProductReview_ReviewType_Mapping` ADD CONSTRAINT `FK_ProdReviewTypeMap_ProductReviewId_ProductReview_Id` FOREIGN KEY (`ProductReviewId`) REFERENCES `ProductReview` (`Id`);
ALTER TABLE `ProductReview_ReviewType_Mapping` ADD CONSTRAINT `FK_ProductReview_ReviewType_Mapping_ReviewTypeId_ReviewType_Id` FOREIGN KEY (`ReviewTypeId`) REFERENCES `ReviewType` (`Id`);
ALTER TABLE `ProductReviewHelpfulness` ADD CONSTRAINT `FK_ProductReviewHelpfulness_ProductReviewId_ProductReview_Id` FOREIGN KEY (`ProductReviewId`) REFERENCES `ProductReview` (`Id`);
ALTER TABLE `ProductWarehouseInventory` ADD CONSTRAINT `FK_ProductWarehouseInventory_ProductId_Product_Id` FOREIGN KEY (`ProductId`) REFERENCES `Product` (`Id`);
ALTER TABLE `ProductWarehouseInventory` ADD CONSTRAINT `FK_ProductWarehouseInventory_WarehouseId_Warehouse_Id` FOREIGN KEY (`WarehouseId`) REFERENCES `Warehouse` (`Id`);
ALTER TABLE `QueuedEmail` ADD CONSTRAINT `FK_QueuedEmail_EmailAccountId_EmailAccount_Id` FOREIGN KEY (`EmailAccountId`) REFERENCES `EmailAccount` (`Id`);
ALTER TABLE `RecurringPayment` ADD CONSTRAINT `FK_RecurringPayment_InitialOrderId_Order_Id` FOREIGN KEY (`InitialOrderId`) REFERENCES `Order` (`Id`);
ALTER TABLE `RecurringPaymentHistory` ADD CONSTRAINT `FK_RecurringPaymentHistory_RecurringPaymentId_RecurPay_Id` FOREIGN KEY (`RecurringPaymentId`) REFERENCES `RecurringPayment` (`Id`);
ALTER TABLE `ReturnRequest` ADD CONSTRAINT `FK_ReturnRequest_CustomerId_Customer_Id` FOREIGN KEY (`CustomerId`) REFERENCES `Customer` (`Id`);
ALTER TABLE `RewardPointsHistory` ADD CONSTRAINT `FK_RewardPointsHistory_CustomerId_Customer_Id` FOREIGN KEY (`CustomerId`) REFERENCES `Customer` (`Id`);
ALTER TABLE `Shipment` ADD CONSTRAINT `FK_Shipment_OrderId_Order_Id` FOREIGN KEY (`OrderId`) REFERENCES `Order` (`Id`);
ALTER TABLE `ShipmentItem` ADD CONSTRAINT `FK_ShipmentItem_ShipmentId_Shipment_Id` FOREIGN KEY (`ShipmentId`) REFERENCES `Shipment` (`Id`);
ALTER TABLE `ShippingMethodRestrictions` ADD CONSTRAINT `FK_ShippingMethodRestrictions_Country_Id_Country_Id` FOREIGN KEY (`Country_Id`) REFERENCES `Country` (`Id`);
ALTER TABLE `ShippingMethodRestrictions` ADD CONSTRAINT `FK_ShippingMethodRestrictions_ShippingMethod_Id_ShipMeth_Id` FOREIGN KEY (`ShippingMethod_Id`) REFERENCES `ShippingMethod` (`Id`);
ALTER TABLE `ShoppingCartItem` ADD CONSTRAINT `FK_ShoppingCartItem_CustomerId_Customer_Id` FOREIGN KEY (`CustomerId`) REFERENCES `Customer` (`Id`);
ALTER TABLE `ShoppingCartItem` ADD CONSTRAINT `FK_ShoppingCartItem_ProductId_Product_Id` FOREIGN KEY (`ProductId`) REFERENCES `Product` (`Id`);
ALTER TABLE `SpecificationAttributeOption` ADD CONSTRAINT `FK_SpecAttrOption_SpecificationAttributeId_SpecAttr_Id` FOREIGN KEY (`SpecificationAttributeId`) REFERENCES `SpecificationAttribute` (`Id`);
ALTER TABLE `StockQuantityHistory` ADD CONSTRAINT `FK_StockQuantityHistory_ProductId_Product_Id` FOREIGN KEY (`ProductId`) REFERENCES `Product` (`Id`);
ALTER TABLE `StoreMapping` ADD CONSTRAINT `FK_StoreMapping_StoreId_Store_Id` FOREIGN KEY (`StoreId`) REFERENCES `Store` (`Id`);
ALTER TABLE `TierPrice` ADD CONSTRAINT `FK_TierPrice_CustomerRoleId_CustomerRole_Id` FOREIGN KEY (`CustomerRoleId`) REFERENCES `CustomerRole` (`Id`);
ALTER TABLE `TierPrice` ADD CONSTRAINT `FK_TierPrice_ProductId_Product_Id` FOREIGN KEY (`ProductId`) REFERENCES `Product` (`Id`);
ALTER TABLE `VendorAttributeValue` ADD CONSTRAINT `FK_VendorAttributeValue_VendorAttributeId_VendorAttribute_Id` FOREIGN KEY (`VendorAttributeId`) REFERENCES `VendorAttribute` (`Id`);
ALTER TABLE `VendorNote` ADD CONSTRAINT `FK_VendorNote_VendorId_Vendor_Id` FOREIGN KEY (`VendorId`) REFERENCES `Vendor` (`Id`);

SET FOREIGN_KEY_CHECKS = 1;
