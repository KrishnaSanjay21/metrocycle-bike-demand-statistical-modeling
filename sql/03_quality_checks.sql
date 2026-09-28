INSERT INTO dq_results
SELECT
    'Source row count is positive',
    'Critical',
    CASE WHEN COUNT(*) > 0 THEN 0 ELSE 1 END,
    CASE WHEN COUNT(*) > 0 THEN 'PASS' ELSE 'FAIL' END,
    'The published hourly source must contain at least one record.'
FROM raw_hourly_bike;

INSERT INTO dq_results
SELECT
    'Observation identifiers are unique',
    'Critical',
    COUNT(*) - COUNT(DISTINCT instant),
    CASE WHEN COUNT(*) = COUNT(DISTINCT instant) THEN 'PASS' ELSE 'FAIL' END,
    'instant must uniquely identify an hourly observation.'
FROM raw_hourly_bike;

INSERT INTO dq_results
SELECT
    'Required fields are populated',
    'Critical',
    SUM(CASE WHEN dteday IS NULL OR hr IS NULL OR cnt IS NULL THEN 1 ELSE 0 END),
    CASE WHEN SUM(CASE WHEN dteday IS NULL OR hr IS NULL OR cnt IS NULL THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'Date, hour, and rental count cannot be null.'
FROM raw_hourly_bike;

INSERT INTO dq_results
SELECT
    'Rental counts reconcile',
    'Critical',
    SUM(CASE WHEN cnt != casual + registered THEN 1 ELSE 0 END),
    CASE WHEN SUM(CASE WHEN cnt != casual + registered THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'Total rentals must equal casual plus registered rentals.'
FROM raw_hourly_bike;

INSERT INTO dq_results
SELECT
    'Counts are non-negative',
    'Critical',
    SUM(CASE WHEN cnt < 0 OR casual < 0 OR registered < 0 THEN 1 ELSE 0 END),
    CASE WHEN SUM(CASE WHEN cnt < 0 OR casual < 0 OR registered < 0 THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'FAIL' END,
    'Count fields cannot contain negative values.'
FROM raw_hourly_bike;

INSERT INTO dq_results
SELECT
    'Categorical codes are valid',
    'Warning',
    SUM(CASE WHEN season NOT BETWEEN 1 AND 4 OR weathersit NOT BETWEEN 1 AND 4 OR hr NOT BETWEEN 0 AND 23 OR weekday NOT BETWEEN 0 AND 6 THEN 1 ELSE 0 END),
    CASE WHEN SUM(CASE WHEN season NOT BETWEEN 1 AND 4 OR weathersit NOT BETWEEN 1 AND 4 OR hr NOT BETWEEN 0 AND 23 OR weekday NOT BETWEEN 0 AND 6 THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'REVIEW' END,
    'Season, weather, hour, and weekday codes must remain in documented ranges.'
FROM raw_hourly_bike;

INSERT INTO dq_results
SELECT
    'Normalized weather measures are valid',
    'Warning',
    SUM(CASE WHEN temp NOT BETWEEN 0 AND 1 OR atemp NOT BETWEEN 0 AND 1 OR hum NOT BETWEEN 0 AND 1 OR windspeed NOT BETWEEN 0 AND 1 THEN 1 ELSE 0 END),
    CASE WHEN SUM(CASE WHEN temp NOT BETWEEN 0 AND 1 OR atemp NOT BETWEEN 0 AND 1 OR hum NOT BETWEEN 0 AND 1 OR windspeed NOT BETWEEN 0 AND 1 THEN 1 ELSE 0 END) = 0 THEN 'PASS' ELSE 'REVIEW' END,
    'Published normalized weather fields are expected to fall between zero and one.'
FROM raw_hourly_bike;

INSERT INTO dq_results
SELECT
    'Timestamp grain is unique',
    'Warning',
    COUNT(*) - COUNT(DISTINCT timestamp),
    CASE WHEN COUNT(*) = COUNT(DISTINCT timestamp) THEN 'PASS' ELSE 'REVIEW' END,
    'Each timestamp should appear once in the analytical mart.'
FROM mart_hourly_demand;

