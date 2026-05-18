import os

DB_CONFIG = {
    "host":     os.getenv("SIEM_DB_HOST",   "localhost"),
    "port":     int(os.getenv("SIEM_DB_PORT", "5432")),
    "dbname":   os.getenv("SIEM_DB_NAME",   "siem"),
    "user":     os.getenv("SIEM_DB_USER",   "siem_user"),
    "password": os.getenv("SIEM_DB_PASS",   "testes"),
}