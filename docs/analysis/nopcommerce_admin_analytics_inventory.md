# nopCommerce Admin Analytics Inventory

Extracted from Admin views/factories in the local nopCommerce clone. Tier A are formal Reports pages; Tier B are dashboard widgets; Tier C are operational admin grids that expose analytics-like filtered/sorted business data.

## Tier A

- **BestCustomersByNumberOfOrders** — formal_report_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Report\BestCustomersByNumberOfOrders.cshtml`
- **BestCustomersByOrderTotal** — formal_report_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Report\BestCustomersByOrderTotal.cshtml`
- **Bestsellers** — formal_report_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Report\Bestsellers.cshtml`
- **CountrySales** — formal_report_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Report\CountrySales.cshtml`
- **LowStock** — formal_report_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Report\LowStock.cshtml`
- **NeverSold** — formal_report_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Report\NeverSold.cshtml`
- **RegisteredCustomers** — formal_report_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Report\RegisteredCustomers.cshtml`
- **SalesSummary** — formal_report_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Report\SalesSummary.cshtml`

## Tier B

- **_BestsellersBriefReportByAmount** — dashboard_widget_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Home\_BestsellersBriefReportByAmount.cshtml`
- **_BestsellersBriefReportByQuantity** — dashboard_widget_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Home\_BestsellersBriefReportByQuantity.cshtml`
- **_CustomerStatistics** — dashboard_widget_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Home\_CustomerStatistics.cshtml`
- **_LatestOrders** — dashboard_widget_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Home\_LatestOrders.cshtml`
- **_OrderAverageReport** — dashboard_widget_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Home\_OrderAverageReport.cshtml`
- **_OrderIncompleteReport** — dashboard_widget_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Home\_OrderIncompleteReport.cshtml`
- **_OrderStatistics** — dashboard_widget_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Home\_OrderStatistics.cshtml`
- **_PopularSearchTermsReport** — dashboard_widget_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Home\_PopularSearchTermsReport.cshtml`

## Tier C

- **Order/List** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Order\List.cshtml`
  - candidate: `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Factories\IOrderModelFactory.cs:23: Task<OrderSearchModel> PrepareOrderSearchModelAsync(OrderSearchModel searchModel);`
- **Order/ShipmentList** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Order\ShipmentList.cshtml`
  - candidate: `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Factories\IOrderModelFactory.cs:23: Task<OrderSearchModel> PrepareOrderSearchModelAsync(OrderSearchModel searchModel);`
- **Customer/List** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Customer\List.cshtml`
  - candidate: `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Factories\CustomerAttributeModelFactory.cs:72: public virtual Task<CustomerAttributeSearchModel> PrepareCustomerAttributeSearchModelAsync(CustomerAttributeSearchModel searchModel)`
- **Product/List** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Product\List.cshtml`
  - candidate: `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Factories\IProductAttributeModelFactory.cs:19: Task<ProductAttributeSearchModel> PrepareProductAttributeSearchModelAsync(ProductAttributeSearchModel searchModel);`
- **Product/_CreateOrUpdate.StockQuantityHistory** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Product\_CreateOrUpdate.StockQuantityHistory.cshtml`
  - candidate: `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Factories\IProductAttributeModelFactory.cs:19: Task<ProductAttributeSearchModel> PrepareProductAttributeSearchModelAsync(ProductAttributeSearchModel searchModel);`
- **ProductReview/List** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\ProductReview\List.cshtml`
  - candidate: `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Factories\IProductReviewModelFactory.cs:21: Task<ProductReviewSearchModel> PrepareProductReviewSearchModelAsync(ProductReviewSearchModel searchModel);`
- **ProductReview/_ProductReviewReviewTypeMappingList** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\ProductReview\_ProductReviewReviewTypeMappingList.cshtml`
  - candidate: `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Factories\IProductReviewModelFactory.cs:21: Task<ProductReviewSearchModel> PrepareProductReviewSearchModelAsync(ProductReviewSearchModel searchModel);`
- **ReturnRequest/List** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\ReturnRequest\List.cshtml`
  - candidate: `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Factories\IReturnRequestModelFactory.cs:19: Task<ReturnRequestSearchModel> PrepareReturnRequestSearchModelAsync(ReturnRequestSearchModel searchModel);`
- **ShoppingCart/CurrentCarts** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\ShoppingCart\CurrentCarts.cshtml`
  - candidate: `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Factories\IShoppingCartModelFactory.cs:19: Task<ShoppingCartSearchModel> PrepareShoppingCartSearchModelAsync(ShoppingCartSearchModel searchModel);`
- **OnlineCustomer/List** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\OnlineCustomer\List.cshtml`
- **ActivityLog/ActivityLogs** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\ActivityLog\ActivityLogs.cshtml`
  - candidate: `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Factories\ActivityLogModelFactory.cs:69: public virtual async Task<ActivityLogTypeSearchModel> PrepareActivityLogTypeSearchModelAsync(ActivityLogTypeSearchModel searchModel)`
- **Log/List** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Log\List.cshtml`
  - candidate: `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Factories\ActivityLogModelFactory.cs:69: public virtual async Task<ActivityLogTypeSearchModel> PrepareActivityLogTypeSearchModelAsync(ActivityLogTypeSearchModel searchModel)`
- **Discount/List** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Discount\List.cshtml`
  - candidate: `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Factories\DiscountModelFactory.cs:180: public virtual async Task<DiscountSearchModel> PrepareDiscountSearchModelAsync(DiscountSearchModel searchModel)`
- **Discount/_CreateOrUpdate.History** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Discount\_CreateOrUpdate.History.cshtml`
  - candidate: `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Factories\DiscountModelFactory.cs:180: public virtual async Task<DiscountSearchModel> PrepareDiscountSearchModelAsync(DiscountSearchModel searchModel)`
- **GiftCard/List** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\GiftCard\List.cshtml`
  - candidate: `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Factories\GiftCardModelFactory.cs:88: public virtual async Task<GiftCardSearchModel> PrepareGiftCardSearchModelAsync(GiftCardSearchModel searchModel)`
- **GiftCard/_CreateOrUpdate.History** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\GiftCard\_CreateOrUpdate.History.cshtml`
  - candidate: `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Factories\GiftCardModelFactory.cs:88: public virtual async Task<GiftCardSearchModel> PrepareGiftCardSearchModelAsync(GiftCardSearchModel searchModel)`
- **Affiliate/List** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Affiliate\List.cshtml`
  - candidate: `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Factories\AffiliateModelFactory.cs:78: protected virtual async Task<AffiliatedOrderSearchModel> PrepareAffiliatedOrderSearchModelAsync(AffiliatedOrderSearchModel searchModel, Affiliate affiliate)`
- **RecurringPayment/List** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\RecurringPayment\List.cshtml`
  - candidate: `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Factories\IRecurringPaymentModelFactory.cs:19: Task<RecurringPaymentSearchModel> PrepareRecurringPaymentSearchModelAsync(RecurringPaymentSearchModel searchModel);`
- **RecurringPayment/_CreateOrUpdate.History** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\RecurringPayment\_CreateOrUpdate.History.cshtml`
  - candidate: `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Factories\IRecurringPaymentModelFactory.cs:19: Task<RecurringPaymentSearchModel> PrepareRecurringPaymentSearchModelAsync(RecurringPaymentSearchModel searchModel);`
- **QueuedEmail/List** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\QueuedEmail\List.cshtml`
  - candidate: `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Factories\IQueuedEmailModelFactory.cs:19: Task<QueuedEmailSearchModel> PrepareQueuedEmailSearchModelAsync(QueuedEmailSearchModel searchModel);`
- **NewsLetterSubscription/List** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\NewsLetterSubscription\List.cshtml`
  - candidate: `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Factories\INewsletterSubscriptionModelFactory.cs:19: Task<NewsLetterSubscriptionSearchModel> PrepareNewsLetterSubscriptionSearchModelAsync(NewsLetterSubscriptionSearchModel searchModel);`
- **Campaign/List** — operational_grid_view; view `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Views\Campaign\List.cshtml`
  - candidate: `nopCommerce\src\Presentation\Nop.Web\Areas\Admin\Factories\CampaignModelFactory.cs:61: public virtual async Task<CampaignSearchModel> PrepareCampaignSearchModelAsync(CampaignSearchModel searchModel)`
