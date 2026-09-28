# Data Dictionary

| Analytical field | Type | Definition |
|---|---|---|
| `observation_id` | integer | UCI record index; unique hourly observation identifier |
| `service_date` | date | Calendar date |
| `timestamp` | datetime | Date combined with hour |
| `hour` | integer | Hour of day, 0–23 |
| `season_code` | integer | 1 winter, 2 spring, 3 summer, 4 fall, per source coding |
| `season` | text | Human-readable season label |
| `year_index` | integer | 0 for 2011, 1 for 2012 |
| `calendar_year` | integer | Four-digit calendar year |
| `month` | integer | Month number, 1–12 |
| `holiday` | integer | Source holiday indicator |
| `weekday` | integer | Source weekday code, 0–6 |
| `workingday` | integer | 1 when day is neither weekend nor holiday |
| `weather_code` | integer | Source weather category, 1–4 |
| `weather` | text | Human-readable weather label |
| `normalized_temperature` | real | UCI normalized temperature |
| `temp_c` | real | Reconstructed Celsius value: normalized value × 47 − 8 |
| `normalized_feels_like` | real | UCI normalized apparent temperature |
| `feels_like_c` | real | Reconstructed Celsius value: normalized value × 66 − 16 |
| `humidity_pct` | real | Normalized humidity × 100 |
| `windspeed_scaled` | real | Normalized windspeed × 67; retained as source-scaled index |
| `casual_rentals` | integer | Casual-user count; reconciliation only, excluded from predictors |
| `registered_rentals` | integer | Registered-user count; reconciliation only, excluded from predictors |
| `rental_count` | integer | Total hourly rentals; modeling target |

Derived modeling features include sine/cosine encodings for hour and month plus `trend_days`, the elapsed days from the first timestamp.

