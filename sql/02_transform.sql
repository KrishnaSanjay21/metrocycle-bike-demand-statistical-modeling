DROP TABLE IF EXISTS mart_hourly_demand;

CREATE TABLE mart_hourly_demand AS
SELECT
    instant AS observation_id,
    DATE(dteday) AS service_date,
    DATETIME(dteday || ' ' || printf('%02d:00:00', hr)) AS timestamp,
    hr AS hour,
    season AS season_code,
    CASE season
        WHEN 1 THEN 'Winter'
        WHEN 2 THEN 'Spring'
        WHEN 3 THEN 'Summer'
        WHEN 4 THEN 'Fall'
    END AS season,
    yr AS year_index,
    2011 + yr AS calendar_year,
    mnth AS month,
    holiday,
    weekday,
    workingday,
    weathersit AS weather_code,
    CASE weathersit
        WHEN 1 THEN 'Clear / partly cloudy'
        WHEN 2 THEN 'Mist / cloudy'
        WHEN 3 THEN 'Light rain or snow'
        WHEN 4 THEN 'Heavy weather'
    END AS weather,
    temp AS normalized_temperature,
    ROUND(temp * 47.0 - 8.0, 3) AS temp_c,
    atemp AS normalized_feels_like,
    ROUND(atemp * 66.0 - 16.0, 3) AS feels_like_c,
    ROUND(hum * 100.0, 2) AS humidity_pct,
    ROUND(windspeed * 67.0, 3) AS windspeed_scaled,
    casual AS casual_rentals,
    registered AS registered_rentals,
    cnt AS rental_count
FROM raw_hourly_bike;

CREATE UNIQUE INDEX idx_hourly_observation_id ON mart_hourly_demand(observation_id);
CREATE INDEX idx_hourly_timestamp ON mart_hourly_demand(timestamp);
CREATE INDEX idx_hourly_weather ON mart_hourly_demand(weather_code);

DROP TABLE IF EXISTS mart_daily_summary;

CREATE TABLE mart_daily_summary AS
SELECT
    service_date,
    calendar_year,
    month,
    season,
    MAX(holiday) AS holiday,
    MAX(workingday) AS workingday,
    SUM(rental_count) AS total_rentals,
    SUM(casual_rentals) AS casual_rentals,
    SUM(registered_rentals) AS registered_rentals,
    ROUND(AVG(temp_c), 2) AS avg_temp_c,
    ROUND(AVG(humidity_pct), 2) AS avg_humidity_pct,
    ROUND(AVG(windspeed_scaled), 2) AS avg_windspeed_scaled
FROM mart_hourly_demand
GROUP BY service_date, calendar_year, month, season;

CREATE UNIQUE INDEX idx_daily_service_date ON mart_daily_summary(service_date);

