from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit,
    QPushButton, QVBoxLayout,
    QGridLayout, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from models import verificar_login
from dashboard import Dashboard


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SIEM - Login")
        self.setFixedSize(380, 240)
        self.setStyleSheet("background-color: #181825;")

        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setFixedSize(320, 200)
        card.setStyleSheet("""
            QFrame {
                background-color: #1e1e2e;
                border-radius: 12px;
                border: 1px solid #313244;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        titulo = QLabel("🛡 Mini SIEM")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("color: #89b4fa; font-size: 18px; font-weight: bold; border: none;")
        layout.addWidget(titulo)

        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Usuário")
        self._estilizar_input(self.input_user)
        layout.addWidget(self.input_user)

        self.input_senha = QLineEdit()
        self.input_senha.setPlaceholderText("Senha")
        self.input_senha.setEchoMode(QLineEdit.Password)
        self._estilizar_input(self.input_senha)
        self.input_senha.returnPressed.connect(self.fazer_login)
        layout.addWidget(self.input_senha)

        btn_login = QPushButton("Entrar")
        btn_login.setFixedHeight(38)
        btn_login.setCursor(Qt.PointingHandCursor)
        btn_login.setStyleSheet("""
            QPushButton {
                background: #89b4fa;
                color: #1e1e2e;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background: #b4d0ff; }
        """)
        btn_login.clicked.connect(self.fazer_login)
        layout.addWidget(btn_login)

        card.setLayout(layout)
        outer.addWidget(card, alignment=Qt.AlignCenter)
        self.setLayout(outer)

    def _estilizar_input(self, widget):
        widget.setFixedHeight(36)
        widget.setStyleSheet("""
            QLineEdit {
                background: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 13px;
            }
            QLineEdit:focus { border: 1px solid #89b4fa; }
        """)

    def fazer_login(self):
        username = self.input_user.text().strip()
        senha    = self.input_senha.text()

        if not username or not senha:
            QMessageBox.warning(self, "Atenção", "Preencha usuário e senha.")
            return

        if verificar_login(username, senha):
            self.dashboard = Dashboard(self, username)
            self.dashboard.show()
            self.hide()
        else:
            QMessageBox.warning(self, "Erro", "Usuário ou senha inválidos.")
            self.input_senha.clear()
            self.input_senha.setFocus()