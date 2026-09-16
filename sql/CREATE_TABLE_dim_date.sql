DROP TABLE IF EXISTS dim_date CASCADE;
CREATE TABLE dim_date (
    id                   BIGINT PRIMARY KEY,       -- Format: YYYYMMDD (e.g., 20260907)
    Date                 TIMESTAMPTZ NOT NULL UNIQUE,  -- Standard PostgreSQL DATE type
    year                 INT NOT NULL,          -- 2026, 2027...
    quarter              INT NOT NULL,          -- 1 to 4
    month                INT NOT NULL,          -- 1 to 12
    day_of_month         INT NOT NULL,          -- 1 to 31
    hour                 INT NOT NULL,          -- 0 to 23
    minute               INT NOT NULL           -- 0 to 59
    --epoch               BIGINT NOT NULL,       -- Unix timestamp
    --day_suffix          VARCHAR(4) NOT NULL,   -- st, nd, rd, th
    --day_name            VARCHAR(9) NOT NULL,   -- Monday, Tuesday...
    --day_of_week         INT NOT NULL,          -- 1 (Monday) to 7 (Sunday)
    --day_of_quarter      INT NOT NULL,          -- 1 to 92
    --day_of_year         INT NOT NULL,          -- 1 to 366
    --week_of_month       INT NOT NULL,          -- 1 to 5
    --week_of_year        INT NOT NULL,          -- 1 to 53 (ISO week)
    --month_name          VARCHAR(9) NOT NULL,   -- January, February...
    --month_name_short    CHAR(3) NOT NULL,      -- Jan, Feb, Mar...
    --first_day_of_week   DATE NOT NULL,
    --last_day_of_week    DATE NOT NULL,
    --first_day_of_month  DATE NOT NULL,
    --last_day_of_month   DATE NOT NULL,
    --is_weekend          BOOLEAN NOT NULL,      -- TRUE/FALSE
    --fiscal_quarter      INT NOT NULL,          -- Adjusted for corporate fiscal tracking
    --fiscal_year         INT NOT NULL
);

-- Add index on the actual date column for fast join performanceS
--CREATE INDEX idx_dim_date_actual ON dim_date("Date");
