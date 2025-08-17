from flask import Flask, request, jsonify
from db import get_connection, get_schema_for_db
import mysql.connector
from decimal import Decimal
from datetime import date, datetime, time

app = Flask(__name__)

def _to_jsonable(val):
    if isinstance(val, (date, datetime, time, Decimal)):
        return str(val)
    return val

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})

@app.route("/list_dbs", methods=["GET"])
def list_dbs():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SHOW DATABASES;")
    dbs = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(dbs)

@app.route("/schema", methods=["GET"])
def schema():
    db = request.args.get("db")
    if not db:
        return jsonify({"error": "db query param required"}), 400
    return jsonify(get_schema_for_db(db))

@app.route("/columns", methods=["GET"])
def columns():
    db = request.args.get("db")
    table = request.args.get("table")
    if not (db and table):
        return jsonify({"error": "db and table query params required"}), 400
    conn = get_connection(database=db)
    cur = conn.cursor()
    cur.execute(f"DESCRIBE `{table}`;")
    cols = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(cols)

@app.route("/execute", methods=["POST"])
def execute():
    payload = request.get_json(force=True)
    query = payload.get("query")
    db = payload.get("db")
    if not query:
        return jsonify({"success": False, "error": "query is required"}), 400
    if not db:
        return jsonify({"success": False, "error": "db is required"}), 400

    conn = get_connection(database=db)
    cur = conn.cursor()
    try:
        cur.execute(query)
        # SELECT-like queries have cursor.description
        if cur.description:
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            data = [dict(zip(cols, (_to_jsonable(v) for v in row))) for row in rows]
            result = {"success": True, "type": "resultset", "data": data, "columns": cols}
        else:
            affected = cur.rowcount
            conn.commit()
            result = {"success": True, "type": "ok", "rows_affected": affected}
        return jsonify(result)
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"success": False, "error": f"{e.errno} {e.msg}"}), 400
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    # Dev mode
    app.run(host="127.0.0.1", port=5000, debug=True)
