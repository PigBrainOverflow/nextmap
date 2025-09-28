# EMAP Database Schema Management

## Overview

EMAP supports both SQLite and PostgreSQL backends with automatic schema conversion. **You only need to maintain the SQLite schema** - the PostgreSQL schema is automatically generated.

## Files

- `schema_sqlite.sql` - **Main schema file** (edit this one)
- `schema_postgres.sql` - Auto-generated (do not edit manually)
- `schema_converter.py` - Conversion tool
- `Makefile` - Build automation

## Usage

### For Development

Just use the database normally:

```python
import emap

# SQLite (uses schema_sqlite.sql)
db = emap.NetlistDB('emap/schema.sql', 'mydb.db', backend='sqlite')

# PostgreSQL (auto-generates schema_postgres.sql if needed)
db = emap.NetlistDB('emap/schema.sql', backend='postgres')
```

The PostgreSQL schema will be automatically generated the first time you use PostgreSQL backend.

### Manual Schema Management

If you need to manually regenerate schemas:

```bash
# Regenerate PostgreSQL schema
make schema-postgres

# Remove generated schema
make clean-schema

# Show help
make help
```

Or use the converter directly:

```bash
python3 emap/schema_converter.py emap/schema_sqlite.sql
```

## Making Schema Changes

1. **Edit only `schema_sqlite.sql`**
2. **PostgreSQL schema will be auto-regenerated** when needed
3. **Commit both files** to git (PostgreSQL schema is tracked for consistency)

## Schema Differences

The converter automatically handles these SQLite → PostgreSQL conversions:

| SQLite                          | PostgreSQL                     |
|---------------------------------|--------------------------------|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `SERIAL PRIMARY KEY`          |
| `hash INTEGER NOT NULL`         | `hash BIGINT NOT NULL`         |
| `params JSON`                   | `params JSONB`                 |
| `-- ON DELETE CASCADE`          | `ON DELETE CASCADE`            |

## Backend Routing

The system automatically selects the correct schema:

- **SQLite backend** → uses `schema_sqlite.sql`
- **PostgreSQL backend** → uses `schema_postgres.sql` (auto-generated if missing)

This ensures each backend gets optimized SQL syntax without translation overhead.