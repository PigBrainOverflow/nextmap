from ..db import NetlistDB


"""
dsp proposal rewrites
"""

def create_dsp_tables(db: NetlistDB, dsp_name: str = "dsp48e2", rules: dict):
    """
    Create tables for DSP proposals in the database.
    """
    for rule_name, rule in rules.items():
        # Create a table for each rule
        db.execute(f"""
            CREATE TABLE IF NOT EXISTS {dsp_name}_{rule_name} (
                type TEXT NOT NULL,
                a TEXT NOT NULL,
                b TEXT NOT NULL,
                y TEXT NOT NULL,
                params TEXT NOT NULL
            )
        """)
    db.commit()