DROP TABLE IF EXISTS fred_indicators CASCADE;
CREATE TABLE fred_indicators (
    id                          VARCHAR PRIMARY KEY,       -- format eg 0440e8e9-87f3-445f-9962-f2508ee2f167
    realtime_start              VARCHAR,
    realtime_end                VARCHAR,
    title                       VARCHAR,
    observation_start           VARCHAR,
    observation_end             VARCHAR,
    frequency                   VARCHAR,
    frequency_short             VARCHAR,
    units                       VARCHAR,
    units_short                 VARCHAR,
    seasonal_adjustment         VARCHAR,
    seasonal_adjustment_short   VARCHAR,
    last_updated                VARCHAR,
    popularity                  VARCHAR,
    notes                       VARCHAR
);