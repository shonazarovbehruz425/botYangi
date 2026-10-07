import json
import sqlite3
import psycopg2
from psycopg2.extras import execute_batch
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aiosqlite
import asyncio

BACKUP_FILE = r"C:\botYangi-main\database_backup_20261007_043844.js"
SQLITE_DB = "buyukhayot.db"
POSTGRES_URL = "postgresql://neondb_owner:npg_WXPYN6JAhL0n@ep-shiny-morning-b4du6ohv-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require"

def load_backup_data():
    print(f"[1] Reading backup file: {BACKUP_FILE}")
    with open(BACKUP_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    prefix = "const BUYUK_HAYOT_DATABASE = "
    start = text.find(prefix) + len(prefix)
    end = text.rfind("};") + 1
    data = json.loads(text[start:end])
    print(f"    - Found {len(data.get('users', []))} users")
    print(f"    - Found {len(data.get('payment_logs', []))} payments")
    print(f"    - Found {len(data.get('activity_logs', []))} activity logs")
    print(f"    - Found {len(data.get('user_replacements', []))} replacements")
    return data

def migrate_to_sqlite(data):
    print(f"\n[2] Migrating into local SQLite: {SQLITE_DB}...")
    from database.db import Database
    db = Database(SQLITE_DB)
    asyncio.run(db.init_db())

    conn = sqlite3.connect(SQLITE_DB)
    cur = conn.cursor()

    # 1. Users
    users = data.get("users", [])
    if users:
        cols = list(users[0].keys())
        cols_str = ", ".join(cols)
        placeholders = ", ".join(["?"] * len(cols))
        rows = [[u.get(c, "") for c in cols] for u in users]
        cur.executemany(f"INSERT OR REPLACE INTO users ({cols_str}) VALUES ({placeholders})", rows)
        print(f"    [+] SQLite: {len(users)} users inserted/updated")

    # 2. Payments
    payments = data.get("payment_logs", [])
    if payments:
        cols = list(payments[0].keys())
        cols_str = ", ".join(cols)
        placeholders = ", ".join(["?"] * len(cols))
        rows = [[p.get(c, "") for c in cols] for p in payments]
        cur.executemany(f"INSERT OR REPLACE INTO payment_logs ({cols_str}) VALUES ({placeholders})", rows)
        print(f"    [+] SQLite: {len(payments)} payments inserted/updated")

    # 3. Activity logs
    activities = data.get("activity_logs", [])
    if activities:
        cols = list(activities[0].keys())
        cols_str = ", ".join(cols)
        placeholders = ", ".join(["?"] * len(cols))
        rows = [[a.get(c, "") for c in cols] for a in activities]
        cur.executemany(f"INSERT OR REPLACE INTO activity_logs ({cols_str}) VALUES ({placeholders})", rows)
        print(f"    [+] SQLite: {len(activities)} activity logs inserted/updated")

    # 4. User replacements
    replacements = data.get("user_replacements", [])
    if replacements:
        cols = list(replacements[0].keys())
        cols_str = ", ".join(cols)
        placeholders = ", ".join(["?"] * len(cols))
        rows = [[r.get(c, "") for c in cols] for r in replacements]
        cur.executemany(f"INSERT OR REPLACE INTO user_replacements ({cols_str}) VALUES ({placeholders})", rows)
        print(f"    [+] SQLite: {len(replacements)} replacements inserted/updated")

    conn.commit()
    conn.close()

def migrate_to_postgres(data):
    print(f"\n[3] Migrating into Neon.tech PostgreSQL...")
    conn = psycopg2.connect(POSTGRES_URL)
    cur = conn.cursor()

    # 1. Users
    users = data.get("users", [])
    if users:
        cols = list(users[0].keys())
        cols_str = ", ".join(cols)
        placeholders = ", ".join(["%s"] * len(cols))
        update_set = ", ".join([f"{c} = EXCLUDED.{c}" for c in cols if c != "user_id"])
        query = f"""
            INSERT INTO users ({cols_str}) 
            VALUES ({placeholders}) 
            ON CONFLICT (user_id) DO UPDATE SET {update_set}
        """
        rows = [[u.get(c, "") for c in cols] for u in users]
        execute_batch(cur, query, rows)
        print(f"    [+] Neon.tech: {len(users)} users inserted/updated")

    # 2. Payments
    payments = data.get("payment_logs", [])
    if payments:
        cols = list(payments[0].keys())
        cols_str = ", ".join(cols)
        placeholders = ", ".join(["%s"] * len(cols))
        update_set = ", ".join([f"{c} = EXCLUDED.{c}" for c in cols if c != "id"])
        query = f"""
            INSERT INTO payment_logs ({cols_str}) 
            VALUES ({placeholders}) 
            ON CONFLICT (id) DO UPDATE SET {update_set}
        """
        rows = [[p.get(c, "") for c in cols] for p in payments]
        execute_batch(cur, query, rows)
        # Update sequence
        cur.execute("SELECT setval('payment_logs_id_seq', (SELECT COALESCE(MAX(id), 1) FROM payment_logs));")
        print(f"    [+] Neon.tech: {len(payments)} payments inserted/updated")

    # 3. Activity logs
    activities = data.get("activity_logs", [])
    if activities:
        cols = list(activities[0].keys())
        cols_str = ", ".join(cols)
        placeholders = ", ".join(["%s"] * len(cols))
        update_set = ", ".join([f"{c} = EXCLUDED.{c}" for c in cols if c != "id"])
        query = f"""
            INSERT INTO activity_logs ({cols_str}) 
            VALUES ({placeholders}) 
            ON CONFLICT (id) DO UPDATE SET {update_set}
        """
        rows = [[a.get(c, "") for c in cols] for a in activities]
        execute_batch(cur, query, rows)
        # Update sequence
        cur.execute("SELECT setval('activity_logs_id_seq', (SELECT COALESCE(MAX(id), 1) FROM activity_logs));")
        print(f"    [+] Neon.tech: {len(activities)} activity logs inserted/updated")

    # 4. User replacements
    replacements = data.get("user_replacements", [])
    if replacements:
        cols = list(replacements[0].keys())
        cols_str = ", ".join(cols)
        placeholders = ", ".join(["%s"] * len(cols))
        update_set = ", ".join([f"{c} = EXCLUDED.{c}" for c in cols if c != "old_user_id"])
        query = f"""
            INSERT INTO user_replacements ({cols_str}) 
            VALUES ({placeholders}) 
            ON CONFLICT (old_user_id) DO UPDATE SET {update_set}
        """
        rows = [[r.get(c, "") for c in cols] for r in replacements]
        execute_batch(cur, query, rows)
        print(f"    [+] Neon.tech: {len(replacements)} replacements inserted/updated")

    conn.commit()

    # Verify counts in Neon.tech
    print("\n[4] Verification of Neon.tech PostgreSQL Database:")
    for tbl in ["users", "payment_logs", "activity_logs", "user_replacements", "level_settings"]:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        cnt = cur.fetchone()[0]
        print(f"    -> Table '{tbl}': {cnt} rows")

    cur.close()
    conn.close()

if __name__ == "__main__":
    data = load_backup_data()
    migrate_to_sqlite(data)
    migrate_to_postgres(data)
    print("\n[FINISH] Migration to both SQLite and Neon.tech PostgreSQL completed successfully!")
