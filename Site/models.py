import psycopg
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import DB_CONFIG


def get_conn():
    return psycopg.connect(**DB_CONFIG)


def init_db():
    conn = get_conn()
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         SERIAL PRIMARY KEY,
            name       TEXT,
            "user"     TEXT UNIQUE,
            passwd     TEXT,
            guess      INTEGER DEFAULT 0,
            blck_unt   TEXT,
            lock_level INTEGER DEFAULT 0,
            perm_block INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS security_logs (
            id        SERIAL PRIMARY KEY,
            username  TEXT,
            ip        TEXT,
            evento    TEXT,
            sucesso   INTEGER NOT NULL,
            data_hora TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_user ON security_logs(username)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_data ON security_logs(data_hora)")

    conn.commit()
    conn.close()


def registrar_log(user, ip, evento, sucesso):
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO security_logs (username, ip, evento, sucesso)
            VALUES (%s, %s, %s, %s)
        """, (user, ip, evento, sucesso))
        conn.commit()
    except Exception as e:
        print("Erro ao registrar log:", e)
    finally:
        conn.close()


def ver_user(user):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        SELECT id, name, passwd, guess, blck_unt, lock_level, perm_block
        FROM users WHERE "user" = %s
    """, (user,))
    row = cur.fetchone()
    conn.close()
    return row


def cria_user(name, user, passwd):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO users (name, "user", passwd)
        VALUES (%s, %s, %s)
    """, (name, user, passwd))
    conn.commit()
    conn.close()


def update_guess(user_id, new_value):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("UPDATE users SET guess = %s WHERE id = %s", (new_value, user_id))
    conn.commit()
    conn.close()


def blck_user(user_id, dthr):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("UPDATE users SET blck_unt = %s WHERE id = %s", (dthr, user_id))
    conn.commit()
    conn.close()


def update_lock_level(user_id, level):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("UPDATE users SET lock_level = %s WHERE id = %s", (level, user_id))
    conn.commit()
    conn.close()


def perm_block_user(user_id):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("UPDATE users SET perm_block = 1 WHERE id = %s", (user_id,))
    conn.commit()
    conn.close()


def reset_temp_block(user_id):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        UPDATE users
        SET guess = 0,
            blck_unt = NULL
        WHERE id = %s
    """, (user_id,))
    conn.commit()
    conn.close()

def desbloquear_conta(username):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        UPDATE users
        SET perm_block = 0,
            lock_level = 0,
            guess      = 0,
            blck_unt   = NULL
        WHERE "user" = %s
    """, (username,))
    conn.commit()
    conn.close()

def get_contas_bloqueadas():
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        SELECT "user", name, lock_level, blck_unt, perm_block
        FROM users
        WHERE perm_block = 1 OR blck_unt IS NOT NULL
        ORDER BY perm_block DESC, "user"
    """)
    rows = cur.fetchall()
    conn.close()
    return rows