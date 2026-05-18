from main import app
from models import (
    ver_user, cria_user, update_guess,
    blck_user, update_lock_level,
    perm_block_user, reset_temp_block,
    registrar_log
)

from flask import render_template, request, redirect, url_for, flash, session
import hashlib
from datetime import datetime, timedelta


@app.route("/")
def index():
    if "user_name" in session:
        return render_template("index.html", logged_in=True, user_name=session["user_name"])
    else:
        return render_template("index.html", logged_in=False)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        ip = request.remote_addr or "unknown"
        user = request.form.get("user")
        passwd_raw = request.form.get("passwd")

        if not user or not passwd_raw:
            flash("Preencha todos os campos!")
            return redirect("/login")

        existing_user = ver_user(user)

        if not existing_user:
            registrar_log(user, ip, "usuario_inexistente", 0)
            flash("Usuário não existe!")
            return redirect("/login")

        user_id = existing_user[0]
        user_name = existing_user[1]
        stored_passwd = existing_user[2]
        guess = existing_user[3]
        blck_unt = existing_user[4]
        lock_level = existing_user[5]
        perm_block = existing_user[6]

        # BLOQUEIO PERMANENTE
        if perm_block == 1:
            registrar_log(user, ip, "conta_bloqueada_perm", 0)
            flash("Conta permanentemente bloqueada. Contate o administrador.")
            return redirect(url_for("login"))

        # BLOQUEIO TEMPORÁRIO
        if blck_unt:
            try:
                unblck_time = datetime.fromisoformat(blck_unt)
            except ValueError:
                reset_temp_block(user_id)
                unblck_time = None

            if unblck_time and datetime.now() < unblck_time:
                restante = unblck_time - datetime.now()
                minutos = restante.seconds // 60
                segundos = restante.seconds % 60
                flash(f"Conta bloqueada! Tente novamente em {minutos}m {segundos}s.")
                return redirect(url_for("login"))
            else:
                reset_temp_block(user_id)
                guess = 0
                registrar_log(user, ip, "desbloqueio_automatico", 1)

        # DEFINIR LIMITE DE TENTATIVAS
        if lock_level == 0:
            max_attempts = 3
        elif lock_level == 1:
            max_attempts = 3
        else:
            max_attempts = 2

        # VALIDAR SENHA
        passwd = hashlib.sha256(passwd_raw.encode()).hexdigest()

        if passwd == stored_passwd:
            session["user"] = user
            session["user_name"] = user_name
            update_guess(user_id, 0)
            registrar_log(user, ip, "login_sucesso", 1)
            return redirect(url_for("index"))

        # SENHA ERRADA
        guess += 1
        update_guess(user_id, guess)
        registrar_log(user, ip, f"login_falha_tentativa_{guess}", 0)

        if guess >= max_attempts:

            # PRIMEIRO BLOQUEIO
            if lock_level == 0:
                tempo = 15
                update_lock_level(user_id, 1)

            # SEGUNDO BLOQUEIO
            elif lock_level == 1:
                tempo = 60
                update_lock_level(user_id, 2)

            # TERCEIRO → PERMANENTE
            else:
                perm_block_user(user_id)
                registrar_log(user, ip, "conta_bloqueada_perm", 0)
                flash("Conta permanentemente bloqueada. Contate o administrador.")
                return redirect(url_for("login"))

            block_until = datetime.now() + timedelta(minutes=tempo)
            blck_user(user_id, block_until.isoformat())
            registrar_log(user, ip, "conta_bloqueada_temp", 0)
            flash(f"Conta bloqueada por {tempo} minutos!")
            return redirect(url_for("login"))

        flash(f"Senha incorreta! Tentativas restantes: {max_attempts - guess}")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    ip = request.remote_addr or "unknown"
    user = session.get("user")

    if user:
        registrar_log(user, ip, "logout", 1)

    session.clear()
    flash("Você saiu da sua conta.")
    return redirect(url_for("index"))


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        name = request.form.get("name")
        user = request.form.get("user")
        passwd_raw = request.form.get("passwd")

        if not user or not passwd_raw or not name:
            flash("Preencha todos os campos!")
            return redirect("/cadastro")

        passwd = hashlib.sha256(passwd_raw.encode()).hexdigest()

        if ver_user(user):
            flash("Usuário já existe!")
            return redirect("/cadastro")

        cria_user(name, user, passwd)
        flash("Usuário criado com sucesso!")
        return redirect("/login")

    return render_template("cadastro.html")