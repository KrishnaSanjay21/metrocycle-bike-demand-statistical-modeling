DROP TABLE IF EXISTS raw_hourly_bike;

CREATE TABLE raw_hourly_bike (
    instant INTEGER NOT NULL,
    dteday TEXT NOT NULL,
    season INTEGER NOT NULL,
    yr INTEGER NOT NULL,
    mnth INTEGER NOT NULL,
    hr INTEGER NOT NULL,
    holiday INTEGER NOT NULL,
    weekday INTEGER NOT NULL,
    workingday INTEGER NOT NULL,
    weathersit INTEGER NOT NULL,
    temp REAL NOT NULL,
    atemp REAL NOT NULL,
    hum REAL NOT NULL,
    windspeed REAL NOT NULL,
    casual INTEGER NOT NULL,
    registered INTEGER NOT NULL,
    cnt INTEGER NOT NULL
);

DROP TABLE IF EXISTS dq_results;

CREATE TABLE dq_results (
    check_name TEXT NOT NULL,
    severity TEXT NOT NULL,
    failed_rows INTEGER NOT NULL,
    status TEXT NOT NULL,
    rule_description TEXT NOT NULL
);

