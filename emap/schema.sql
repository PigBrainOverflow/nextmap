CREATE TABLE IF NOT EXISTS invs (
    a INTEGER,
    y INTEGER,
    PRIMARY KEY (a, y)
);

CREATE TABLE IF NOT EXISTS ands (
    a INTEGER,
    b INTEGER,
    y INTEGER,
    PRIMARY KEY (a, b, y)
);

CREATE TABLE IF NOT EXISTS wiresets (
    id INTEGER PRIMARY KEY,
    hash INTEGER
);
-- also create an index on hash for faster lookups
CREATE INDEX IF NOT EXISTS idx_wiresets_hash ON wiresets (hash);

CREATE TABLE IF NOT EXISTS wireset_members (
    wireset_id INTEGER,
    wire_id INTEGER,
    PRIMARY KEY (wireset_id, wire_id),
    FOREIGN KEY (wireset_id) REFERENCES wiresets(id)
);
-- also create an index on wire_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_wireset_members_wire_id ON wireset_members (wire_id);

CREATE TABLE IF NOT EXISTS luts (
    ins INTEGER PRIMARY KEY,
    out INTEGER,
    FOREIGN KEY (ins) REFERENCES wiresets(id)
);

CREATE TABLE IF NOT EXISTS as_outputs (
    sink INTEGER,
    name VARCHAR(16) PRIMARY KEY
)

CREATE TABLE IF NOT EXISTS from_inputs (
    source INTEGER,
    name VARCHAR(16) PRIMARY KEY
);