from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QMessageBox,
    QCheckBox
)
from PySide6.QtWidgets import QSizePolicy
from models import get_config, set_config
from PySide6.QtCore import Qt, QTimer
import psycopg
import hashlib
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config import DB_CONFIG


def get_conn():
    return psycopg.connect(**DB_CONFIG)


class SpinWidget(QFrame):
    def __init__(self, valor=5, minimo=3, maximo=60, parent=None):
        super().__init__(parent)
        self._min = minimo
        self._max = maximo

        self.setStyleSheet("""
            QFrame {
                background: #313244;
                border: 1px solid #45475a;
                border-radius: 5px;
            }
        """)
        self.setFixedHeight(34)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.btn_menos = QPushButton("−")
        self.btn_menos.setFixedSize(32, 32)
        self.btn_menos.setCursor(Qt.PointingHandCursor)
        self.btn_menos.setStyleSheet("""
            QPushButton {
                background: transparent; color: #a6adc8;
                border: none; border-radius: 5px 0 0 5px;
                font-size: 16px; font-weight: bold;
            }
            QPushButton:hover { background: #45475a; color: #cdd6f4; }
        """)
        self.btn_menos.clicked.connect(self._diminuir)

        self.input_valor = QLineEdit(str(valor))
        self.input_valor.setFixedWidth(40)
        self.input_valor.setAlignment(Qt.AlignCenter)
        self.input_valor.setStyleSheet("""
            QLineEdit {
                color: #cdd6f4;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-left: 1px solid #45475a;
                border-right: 1px solid #45475a;
                background: transparent;
                padding: 0;
            }
        """)
        self.input_valor.editingFinished.connect(self._validar_input)

        self.btn_mais = QPushButton("+")
        self.btn_mais.setFixedSize(32, 32)
        self.btn_mais.setCursor(Qt.PointingHandCursor)
        self.btn_mais.setStyleSheet("""
            QPushButton {
                background: transparent; color: #a6adc8;
                border: none; border-radius: 0 5px 5px 0;
                font-size: 16px; font-weight: bold;
            }
            QPushButton:hover { background: #45475a; color: #cdd6f4; }
        """)
        self.btn_mais.clicked.connect(self._aumentar)

        layout.addWidget(self.btn_menos)
        layout.addWidget(self.input_valor)
        layout.addWidget(self.btn_mais)
        self.setLayout(layout)

    def _diminuir(self):
        v = self.value()
        if v > self._min:
            self.input_valor.setText(str(v - 1))

    def _aumentar(self):
        v = self.value()
        if v < self._max:
            self.input_valor.setText(str(v + 1))

    def _validar_input(self):
        try:
            v = int(self.input_valor.text())
            v = max(self._min, min(self._max, v))
        except ValueError:
            v = self._min
        self.input_valor.setText(str(v))

    def value(self):
        try:
            return max(self._min, min(self._max, int(self.input_valor.text())))
        except ValueError:
            return self._min


class SecaoFrame(QFrame):
    def __init__(self, titulo):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e2e;
                border-radius: 10px;
                border: 1px solid #313244;
            }
        """)
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(18, 14, 18, 18)
        self._layout.setSpacing(12)

        lbl = QLabel(titulo)
        lbl.setStyleSheet("color: #89b4fa; font-size: 13px; font-weight: bold; border: none;")
        self._layout.addWidget(lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("border: 1px solid #313244;")
        self._layout.addWidget(sep)

        self.setLayout(self._layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

    def add(self, widget):
        self._layout.addWidget(widget)

    def add_layout(self, layout):
        self._layout.addLayout(layout)


class ConfigPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #181825;")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        titulo = QLabel("Configurações")
        titulo.setStyleSheet("color: #cdd6f4; font-size: 18px; font-weight: bold;")
        main_layout.addWidget(titulo)

        # ── Seção: Conta do Painel ─────────────────────────────────────────────
        sec_conta = SecaoFrame("Conta do Painel SIEM")
        sec_conta.setMinimumHeight(240)

        grid_conta = QGridLayout()
        grid_conta.setHorizontalSpacing(25)
        grid_conta.setVerticalSpacing(10)
        grid_conta.setColumnMinimumWidth(0, 120)
        grid_conta.setColumnStretch(1, 1)
        grid_conta.setRowMinimumHeight(0, 40)
        grid_conta.setRowMinimumHeight(1, 40)
        grid_conta.setRowMinimumHeight(2, 40)

        lbl_user = QLabel("Usuário:")
        lbl_user.setStyleSheet("color: #a6adc8; border: none;")
        self.input_novo_user = QLineEdit()
        self.input_novo_user.setPlaceholderText("Digite o usuário")
        self._estilizar_input(self.input_novo_user)
        grid_conta.addWidget(lbl_user, 0, 0)
        grid_conta.addWidget(self.input_novo_user, 0, 1)

        lbl_senha = QLabel("Senha:")
        lbl_senha.setStyleSheet("color: #a6adc8; border: none;")
        self.input_nova_senha = QLineEdit()
        self.input_nova_senha.setPlaceholderText("Digite a senha")
        self.input_nova_senha.setEchoMode(QLineEdit.Password)
        self._estilizar_input(self.input_nova_senha)
        grid_conta.addWidget(lbl_senha, 1, 0)
        grid_conta.addWidget(self.input_nova_senha, 1, 1)

        lbl_confirma = QLabel("Confirmar:")
        lbl_confirma.setStyleSheet("color: #a6adc8; border: none;")
        self.input_confirma = QLineEdit()
        self.input_confirma.setPlaceholderText("Confirme a senha")
        self.input_confirma.setEchoMode(QLineEdit.Password)
        self._estilizar_input(self.input_confirma)
        grid_conta.addWidget(lbl_confirma, 2, 0)
        grid_conta.addWidget(self.input_confirma, 2, 1)

        sec_conta.add_layout(grid_conta)

        btn_salvar_conta = self._btn_primario("Salvar conta")
        btn_salvar_conta.clicked.connect(self._salvar_conta)
        sec_conta.add(btn_salvar_conta)

        main_layout.addWidget(sec_conta)

        # ── Seção: Alertas ─────────────────────────────────────────────────────
        sec_alertas = SecaoFrame("Alertas")

        row_intervalo = QHBoxLayout()
        lbl_intervalo = QLabel("Intervalo de polling (s):")
        lbl_intervalo.setStyleSheet("color: #a6adc8; border: none;")
        lbl_intervalo.setFixedWidth(200)
        self.spin_intervalo = SpinWidget(valor=5, minimo=3, maximo=60)
        self.spin_intervalo.setFixedWidth(120)
        row_intervalo.addWidget(lbl_intervalo)
        row_intervalo.addWidget(self.spin_intervalo)
        row_intervalo.addStretch()
        sec_alertas.add_layout(row_intervalo)

        self.chk_som = QCheckBox("Habilitar som de alerta")
        self.chk_som.setChecked(True)
        self.chk_som.setStyleSheet("color: #a6adc8; border: none;")
        sec_alertas.add(self.chk_som)

        btn_salvar_alertas = self._btn_primario("Salvar configurações de alerta")
        btn_salvar_alertas.clicked.connect(self._salvar_alertas)
        sec_alertas.add(btn_salvar_alertas)

        main_layout.addWidget(sec_alertas)

        # ── Seção: Banco de Dados ──────────────────────────────────────────────
        sec_db = SecaoFrame("Banco de Dados")

        info_db = QLabel(
            f"Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}\n"
            f"Banco: {DB_CONFIG['dbname']}\n"
            f"Usuário: {DB_CONFIG['user']}"
        )
        info_db.setStyleSheet("color: #a6adc8; font-size: 12px; border: none;")
        sec_db.add(info_db)

        btn_testar = self._btn_secundario("Testar conexão")
        btn_testar.clicked.connect(self._testar_conexao)
        sec_db.add(btn_testar)

        main_layout.addWidget(sec_db)
        main_layout.addStretch()

        self.setLayout(main_layout)

        # ── Carrega configurações salvas ───────────────────────────────────────
        self.spin_intervalo.input_valor.setText(get_config("polling_intervalo", "5"))
        self.chk_som.setChecked(get_config("som_ativo", "true") == "true")

        # Limpa campos de conta após renderizar (evita autocomplete do Windows)
        QTimer.singleShot(200, self._limpar_campos_conta)

    def _limpar_campos_conta(self):
        self.input_novo_user.clear()
        self.input_nova_senha.clear()
        self.input_confirma.clear()

    def _estilizar_input(self, widget):
        widget.setMinimumHeight(34)
        widget.setMaximumHeight(34)
        widget.setStyleSheet("""
            QLineEdit {
                background: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 13px;
            }
            QLineEdit:focus { border: 1px solid #89b4fa; }
        """)

    def _btn_primario(self, texto):
        btn = QPushButton(texto)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(36)
        btn.setStyleSheet("""
            QPushButton {
                background: #89b4fa; color: #1e1e2e;
                border-radius: 5px; padding: 7px 20px; font-weight: bold;
            }
            QPushButton:hover { background: #b4d0ff; }
        """)
        return btn

    def _btn_secundario(self, texto):
        btn = QPushButton(texto)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background: #45475a; color: #cdd6f4;
                border-radius: 5px; padding: 7px 20px;
            }
            QPushButton:hover { background: #585b70; }
        """)
        return btn

    def _msg(self, tipo, texto):
        msg = QMessageBox(self)
        msg.setWindowTitle("SIEM")
        msg.setText(texto)
        msg.setIcon(QMessageBox.Information if tipo == "ok" else QMessageBox.Warning)
        msg.exec()

    def _salvar_conta(self):
        usuario  = self.input_novo_user.text().strip()
        senha    = self.input_nova_senha.text()
        confirma = self.input_confirma.text()

        if not usuario or not senha:
            self._msg("erro", "Preencha usuário e senha.")
            return
        if senha != confirma:
            self._msg("erro", "As senhas não coincidem.")
            return

        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        try:
            conn = get_conn()
            cur  = conn.cursor()
            cur.execute("""
                INSERT INTO user_siem (username, senha)
                VALUES (%s, %s)
                ON CONFLICT (username) DO UPDATE SET senha = EXCLUDED.senha
            """, (usuario, senha_hash))
            conn.commit()
            conn.close()
            self._msg("ok", f"Conta '{usuario}' salva com sucesso!")
            self._limpar_campos_conta()
        except Exception as e:
            self._msg("erro", f"Erro ao salvar: {e}")

    def _salvar_alertas(self):
        intervalo = self.spin_intervalo.value()
        som = self.chk_som.isChecked()
        set_config("polling_intervalo", intervalo)
        set_config("som_ativo", str(som).lower())
        self._msg("ok", f"Configurações salvas!\nPolling: {intervalo}s | Som: {'ON' if som else 'OFF'}")

    def _testar_conexao(self):
        try:
            conn = get_conn()
            conn.close()
            self._msg("ok", "Conexão com o PostgreSQL estabelecida com sucesso!")
        except Exception as e:
            self._msg("erro", f"Falha na conexão:\n{e}")