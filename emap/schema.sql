CREATE TABLE IF NOT EXISTS ports (
    name VARCHAR(64) PRIMARY KEY,
    wire VARCHAR(64) NOT NULL,
    direction VARCHAR(16) NOT NULL
);

CREATE TABLE IF NOT EXISTS ay_cells (
    type VARCHAR(16),
    a VARCHAR(64),
    y VARCHAR(64) NOT NULL,
    PRIMARY KEY (type, a)
);

CREATE TABLE IF NOT EXISTS aby_cells (
    type VARCHAR(16),
    a VARCHAR(64),
    b VARCHAR(64),
    y VARCHAR(64) NOT NULL,
    PRIMARY KEY (type, a, b)
);

CREATE TABLE IF NOT EXISTS absy_cells (
    type VARCHAR(16),
    a VARCHAR(64),
    b VARCHAR(64),
    s VARCHAR(64),
    y VARCHAR(64) NOT NULL,
    PRIMARY KEY (type, a, b, s)
);

CREATE TABLE IF NOT EXISTS dffs (
    d VARCHAR(64),
    clk VARCHAR(64),
    q VARCHAR(64) NOT NULL,
    PRIMARY KEY (d, clk)
);

CREATE TABLE IF NOT EXISTS instances (
    id VARCHAR(64) PRIMARY KEY,
    module VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS instance_ports (
    instance VARCHAR(64),
    port VARCHAR(64),
    wire VARCHAR(64) NOT NULL,
    PRIMARY KEY (instance, port)
);

CREATE TABLE IF NOT EXISTS instance_params (
    instance VARCHAR(64),
    param VARCHAR(64),
    val VARCHAR(64) NOT NULL,
    PRIMARY KEY (instance, param)
);