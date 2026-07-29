-- Refresh seed data dates so demo queries return results on any deployment date.
--
-- Spreads orders across the last 365 days relative to UTC_TIMESTAMP()
-- using (Id * 17 + 3) % 360 formula to distribute rows without clustering.

UPDATE `Order`
SET CreatedOnUtc = DATE_SUB(UTC_TIMESTAMP(), INTERVAL ((Id * 17 + 3) % 360) DAY),
    PaidDateUtc = CASE WHEN PaidDateUtc IS NOT NULL THEN DATE_SUB(UTC_TIMESTAMP(), INTERVAL ((Id * 17 + 3) % 360) DAY) ELSE NULL END;

-- Keep Shipment dates consistent with their parent Order dates.
UPDATE `Shipment` sh
INNER JOIN `Order` o ON sh.OrderId = o.Id
SET sh.CreatedOnUtc = DATE_ADD(o.CreatedOnUtc, INTERVAL 1 DAY),
    sh.ShippedDateUtc = DATE_ADD(o.CreatedOnUtc, INTERVAL 1 DAY),
    sh.DeliveryDateUtc = CASE WHEN sh.DeliveryDateUtc IS NOT NULL THEN DATE_ADD(o.CreatedOnUtc, INTERVAL 3 DAY) ELSE NULL END;

