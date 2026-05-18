import psycopg
import hashlib
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
        CREATE TABLE IF NOT EXISTS user_siem (
            id       SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            senha    TEXT NOT NULL
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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS config (
            chave TEXT PRIMARY KEY,
            valor TEXT
        )
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_user ON security_logs(username)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_data ON security_logs(data_hora)")

    conn.commit()
    conn.close()


def verificar_login(username, passwd_raw):
    conn = get_conn()
    cur  = conn.cursor()
    passwd_hash = hashlib.sha256(passwd_raw.encode()).hexdigest()
    cur.execute(
        "SELECT * FROM user_siem WHERE username = %s AND senha = %s",
        (username, passwd_hash)
    )
    user = cur.fetchone()
    conn.close()
    return user is not None


def get_logs_paginated(limit, offset, usuario="", evento="", sucesso=None, data_ini=None, data_fim=None):
    conn   = get_conn()
    cur    = conn.cursor()
    query  = "SELECT id, username, ip, evento, sucesso, data_hora FROM security_logs WHERE 1=1"
    params = []

    if usuario:
        query += " AND username ILIKE %s"
        params.append(f"%{usuario}%")
    if evento:
        query += " AND evento ILIKE %s"
        params.append(f"%{evento}%")
    if sucesso is not None:
        query += " AND sucesso = %s"
        params.append(sucesso)
    if data_ini:
        query += " AND data_hora >= %s"
        params.append(data_ini)
    if data_fim:
        query += " AND data_hora <= %s"
        params.append(data_fim)

    query += " ORDER BY data_hora DESC LIMIT %s OFFSET %s"
    params += [limit, offset]

    cur.execute(query, params)
    logs = cur.fetchall()
    conn.close()
    return logs


def get_stats():
    conn = get_conn()
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM security_logs")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM security_logs WHERE sucesso = 0")
    falhas = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM security_logs WHERE sucesso = 1 AND evento = 'login_sucesso'")
    logins_ok = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT ip) FROM security_logs")
    ips_unicos = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM security_logs WHERE evento LIKE 'conta_bloqueada%'")
    bloqueios = cur.fetchone()[0]

    conn.close()
    return {
        "total":      total,
        "falhas":     falhas,
        "logins_ok":  logins_ok,
        "ips_unicos": ips_unicos,
        "bloqueios":  bloqueios,
    }


def get_atividade_por_hora():
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        SELECT DATE_TRUNC('hour', data_hora) AS hora,
               COUNT(*) AS total
        FROM security_logs
        WHERE data_hora >= NOW() - INTERVAL '30 days'
        GROUP BY hora
        ORDER BY hora
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_alertas(intervalo="24 hours"):
    conn = get_conn()
    cur  = conn.cursor()

    # Monta o filtro de data
    if isinstance(intervalo, tuple):
        ini, fim = intervalo
        filtro_data = "data_hora BETWEEN %s AND %s"
        params_data = (ini, fim)
        filtro_ip   = "data_hora BETWEEN %s AND %s"
        params_ip   = (ini, fim)
    else:
        filtro_data = f"data_hora >= NOW() - INTERVAL '{intervalo}'"
        params_data = ()
        filtro_ip   = f"data_hora >= NOW() - INTERVAL '{intervalo}'"
        params_ip   = ()

    cur.execute(f"""
        SELECT id, username, ip, evento, sucesso, data_hora
        FROM security_logs
        WHERE evento = 'conta_bloqueada_perm'
          AND {filtro_data}
        ORDER BY data_hora DESC LIMIT 50
    """, params_data)
    perm = cur.fetchall()

    cur.execute(f"""
        SELECT id, username, ip, evento, sucesso, data_hora
        FROM security_logs
        WHERE evento = 'conta_bloqueada_temp'
          AND {filtro_data}
        ORDER BY data_hora DESC LIMIT 50
    """, params_data)
    temp = cur.fetchall()

    cur.execute(f"""
        SELECT ip, COUNT(*) as tentativas
        FROM security_logs
        WHERE sucesso = 0
          AND {filtro_ip}
        GROUP BY ip
        HAVING COUNT(*) >= 3
        ORDER BY tentativas DESC
    """, params_ip)
    ips_suspeitos = cur.fetchall()

    conn.close()
    return perm, temp, ips_suspeitos


def get_logs_desde(ultimo_id):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        SELECT id, username, ip, evento, sucesso, data_hora
        FROM security_logs
        WHERE id > %s
        ORDER BY data_hora DESC
    """, (ultimo_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_config(chave, padrao=None):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("SELECT valor FROM config WHERE chave = %s", (chave,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else padrao

def set_config(chave, valor):
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO config (chave, valor) VALUES (%s, %s)
        ON CONFLICT (chave) DO UPDATE SET valor = EXCLUDED.valor
    """, (chave, str(valor)))
    conn.commit()
    conn.close()

def salvar_estado(estado: dict):
    conn = get_conn()
    cur  = conn.cursor()
    for chave, valor in estado.items():
        cur.execute("""
            INSERT INTO config (chave, valor) VALUES (%s, %s)
            ON CONFLICT (chave) DO UPDATE SET valor = EXCLUDED.valor
        """, (chave, str(valor)))
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