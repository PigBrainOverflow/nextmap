CREATE IF NOT EXISTS ay_cells (
    type VARCHAR(16),
    a VARCHAR(64),
    y VARCHAR(64),
    PRIMARY KEY (type, a, y)
);

CREATE IF NOT EXISTS aby_cells (
    type VARCHAR(16),
    a VARCHAR(64),
    b VARCHAR(64),
    y VARCHAR(64),
    PRIMARY KEY (type, a, b, y)
);

CREATE IF NOT EXISTS absy_cells (
    type VARCHAR(16),
    a VARCHAR(64),
    b VARCHAR(64),
    s VARCHAR(64),
    y VARCHAR(64),
    PRIMARY KEY (type, a, b, s, y)
);