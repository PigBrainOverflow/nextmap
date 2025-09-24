CREATE TABLE IF NOT EXISTS ay_cells (
    type INTEGER,
    a INTEGER,
    y INTEGER,
    PRIMARY KEY (type, a, y)
);

CREATE TABLE IF NOT EXISTS aby_cells (
    type INTEGER,
    a INTEGER,
    b INTEGER,
    y INTEGER,
    PRIMARY KEY (type, a, b, y)
);

CREATE TABLE IF NOT EXISTS muxes (
    a INTEGER,
    b INTEGER,
    s INTEGER,
    y INTEGER,
    PRIMARY KEY (a, b, s, y)
);

-- We may not need those tables
CREATE TABLE IF NOT EXISTS wirevecs (
    id INTEGER PRIMARY KEY,
    hash INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_wirevecs_hash ON wirevecs (hash);

CREATE TABLE IF NOT EXISTS wirevec_members (
    wirevec INTEGER,
    idx INTEGER,
    wire INTEGER NOT NULL,
    PRIMARY KEY (wirevec, idx),
    FOREIGN KEY (wirevec) REFERENCES wirevecs(id)
);
CREATE INDEX IF NOT EXISTS idx_wirevec_members_wire ON wirevec_members (wire);

CREATE TABLE IF NOT EXISTS as_outputs (
    sink INTEGER NOT NULL,
    name VARCHAR(16) PRIMARY KEY,
    FOREIGN KEY (sink) REFERENCES wirevecs(id)
);

CREATE TABLE IF NOT EXISTS from_inputs (
    source INTEGER NOT NULL,
    name VARCHAR(16) PRIMARY KEY,
    FOREIGN KEY (source) REFERENCES wirevecs(id)
);

CREATE TABLE IF NOT EXISTS arith_aby_cells (
    type INTEGER,
    a INTEGER,
    b INTEGER,
    y_width INTEGER,
    y INTEGER,
    PRIMARY KEY (type, a, b, y_width, y)
);
