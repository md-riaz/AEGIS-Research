FROM mysql:8.0

COPY schema.sql /docker-entrypoint-initdb.d/1_schema.sql
COPY mock_data.sql /docker-entrypoint-initdb.d/2_mock_data.sql
COPY 3_refresh_dates.sql /docker-entrypoint-initdb.d/3_refresh_dates.sql
