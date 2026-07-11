-- Refresh seed data dates so demo queries return results on any deployment date.
--
-- Spreads the 20 seed orders across the last 90 days relative to UTC_TIMESTAMP(),
-- giving ~7 orders this month, ~9 last month, and ~4 two months ago.
-- The (Id * 7 + 3) % 85 formula distributes rows without clustering.

UPDATE `Order`
SET CreatedOnUtc = DATE_SUB(UTC_TIMESTAMP(), INTERVAL ((Id * 7 + 3) % 85) DAY);

-- Keep Shipment dates consistent with their parent Order dates.
UPDATE `Shipment` sh
INNER JOIN `Order` o ON sh.OrderId = o.Id
SET sh.CreatedOnUtc = DATE_ADD(o.CreatedOnUtc, INTERVAL 1 DAY);
