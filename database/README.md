# Docker Seed Data

The Docker database image copies these files into MySQL's
`/docker-entrypoint-initdb.d` directory, so seeding does not depend on Windows
host file sharing:

1. `schema.sql` creates the nopCommerce-compatible tables.
2. `mock_data.sql` inserts the demo e-commerce dataset.
3. `3_refresh_dates.sql` shifts order and shipment dates relative to the
   current deployment date so time-window questions keep returning data.

The compose database name is `aegis`, matching the local thesis benchmark
configuration.
