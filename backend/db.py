import mysql.connector
from config import DB_CONFIG

def get_connection(database=None):
    cfg = DB_CONFIG.copy()
    if database:
        cfg["database"] = database
    return mysql.connector.connect(**cfg)

def get_schema_for_db(db_name: str):
    conn = get_connection(database=db_name)
    cur = conn.cursor()
    cur.execute("SHOW TABLES;")
    tables = [t[0] for t in cur.fetchall()]
    schema = {}
    for t in tables:
        cur.execute(f"DESCRIBE `{t}`;")
        cols = cur.fetchall()
        schema[t] = [
            {
                "Field": c[0],
                "Type": c[1],
                "Null": c[2],
                "Key": c[3],
                "Default": c[4],
                "Extra": c[5],
            }
            for c in cols
        ]
    cur.close()
    conn.close()
    return {"database": db_name, "tables": schema}
