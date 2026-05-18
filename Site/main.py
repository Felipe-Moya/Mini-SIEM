import os
import secrets
from flask import Flask
from models import init_db

init_db()
app = Flask(__name__)
app.secret_key = os.getenv("SIEM_SECRET_KEY", secrets.token_hex(32))

from views import *

if __name__ == "__main__":
    app.run()