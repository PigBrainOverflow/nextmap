# Makefile for EMAP schema management
#
# Targets:
#   schema-postgres  Generate PostgreSQL schema from SQLite schema
#   clean-schema     Remove generated PostgreSQL schema
#   help            Show this help

SCHEMA_DIR = .
SQLITE_SCHEMA = $(SCHEMA_DIR)/schema_sqlite.sql
POSTGRES_SCHEMA = $(SCHEMA_DIR)/schema_postgres.sql
CONVERTER = $(SCHEMA_DIR)/schema_converter.py

.PHONY: help schema-postgres clean-schema

help:
	@echo "EMAP Schema Management"
	@echo "====================="
	@echo ""
	@echo "Available targets:"
	@echo "  schema-postgres  Generate PostgreSQL schema from SQLite schema"
	@echo "  clean-schema     Remove generated PostgreSQL schema"
	@echo "  help            Show this help"
	@echo ""
	@echo "The PostgreSQL schema is auto-generated from the SQLite schema."
	@echo "Only edit $(SQLITE_SCHEMA) - the PostgreSQL schema will be regenerated automatically."

schema-postgres: $(POSTGRES_SCHEMA)

$(POSTGRES_SCHEMA): $(SQLITE_SCHEMA) $(CONVERTER)
	@echo "Regenerating PostgreSQL schema from SQLite schema..."
	python3 $(CONVERTER) $(SQLITE_SCHEMA)
	@echo "✅ PostgreSQL schema updated"

clean-schema:
	@echo "Removing generated PostgreSQL schema..."
	rm -f $(POSTGRES_SCHEMA)
	@echo "✅ Generated schema removed"