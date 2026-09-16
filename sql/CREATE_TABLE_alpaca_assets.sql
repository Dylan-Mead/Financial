DROP TABLE IF EXISTS alpaca_assets CASCADE;
CREATE TABLE alpaca_assets (
    id                   CHAR(36) PRIMARY KEY,       -- format eg 0440e8e9-87f3-445f-9962-f2508ee2f167
    class                VARCHAR(255),
    exchange             VARCHAR(255),
    symbol               VARCHAR(255),
    name                 VARCHAR(255),
    status               VARCHAR(255),
    tradable             BOOLEAN,
    marginable           BOOLEAN,
    maintenance_margin_requirement INT,
    margin_requirement_long VARCHAR(255),
    margin_requirement_short VARCHAR(255),
    shortable            BOOLEAN,
    easy_to_borrow       BOOLEAN,
    borrow_status        VARCHAR(255),
    fractionable         BOOLEAN,
    attributes           JSONB,
    min_order_size       VARCHAR(255),
    min_trade_increment  VARCHAR(255),
    price_increment      VARCHAR(255)
);