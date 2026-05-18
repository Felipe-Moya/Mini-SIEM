from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout,
    QStackedWidget, QFrame
)
from PySide6.QtCore import Qt

from pages.home          import HomePage
from pages.logs          import LogsPage
from pages.alertas       import AlertasPage
from pages.configuracoes import ConfigPage
from models import get_config

MENU_ITEMS = [
    "Visão Geral",
    "Logs",
    "Alertas",
    "Configurações",
]

ESTILO_BTN_MENU = """
    QPushButton {{
        text-align: left;
        padding: 10px 16px;
        border: none;
        border-radius: 8px;
        color: {cor};
        background: {bg};
        font-size: 13px;
    }}
    QPushButton:hover {{
        background: #313244;
        color: #cdd6f4;
    }}
"""


class MenuButton(QPushButton):
    def __init__(self, texto):
        super().__init__(f"  {texto}")
        self.setCheckable(True)
        self.setFixedHeight(42)
        self.setCursor(Qt.PointingHandCursor)
        self._atualizar_estilo(False)

    def _atualizar_estilo(self, ativo):
        if ativo:
            self.setStyleSheet(ESTILO_BTN_MENU.format(
                cor="#cdd6f4", bg="#313244"
            ))
        else:
            self.setStyleSheet(ESTILO_BTN_MENU.format(
                cor="#a6adc8", bg="transparent"
            ))

    def setChecked(self, val):
        super().setChecked(val)
        self._atualizar_estilo(val)


class Dashboard(QWidget):
    def __init__(self, login_window, username):
        super().__init__()

        self.login_window = login_window
        self.username     = username
        self._botoes      = []

        self.setWindowTitle("SIEM - Dashboard")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet("background-color: #11111b;")

        # ── Sidebar ────────────────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #181825;
                border-right: 1px solid #313244;
            }
        """)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(10, 16, 10, 16)
        sidebar_layout.setSpacing(4)

        lbl_logo = QLabel("🛡 Mini SIEM")
        lbl_logo.setStyleSheet("""
            color: #89b4fa;
            font-size: 16px;
            font-weight: bold;
            padding: 8px 8px 16px 8px;
        """)
        sidebar_layout.addWidget(lbl_logo)

        for texto in MENU_ITEMS:
            btn = MenuButton(texto)
            btn.clicked.connect(lambda checked, t=texto: self._navegar(t))
            self._botoes.append((texto, btn))
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        lbl_user = QLabel(f"👤 {self.username}")
        lbl_user.setStyleSheet("""
            color: #a6adc8;
            font-size: 11px;
            padding: 8px;
            border-top: 1px solid #313244;
        """)
        sidebar_layout.addWidget(lbl_user)

        btn_logout = QPushButton("  Sair")
        btn_logout.setFixedHeight(38)
        btn_logout.setCursor(Qt.PointingHandCursor)
        btn_logout.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #f38ba8;
                border: 1px solid #f38ba8;
                border-radius: 6px;
                text-align: left;
                padding: 0 16px;
                font-size: 13px;
            }
            QPushButton:hover { background: #f38ba822; }
        """)
        btn_logout.clicked.connect(self.logout)
        sidebar_layout.addWidget(btn_logout)

        sidebar.setLayout(sidebar_layout)

        # ── Área central ───────────────────────────────────────────────────────
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #181825;")

        self.page_home    = HomePage()
        self.page_logs    = LogsPage()
        self.page_alertas = AlertasPage()
        self.page_config  = ConfigPage()

        self.stack.addWidget(self.page_home)
        self.stack.addWidget(self.page_logs)
        self.stack.addWidget(self.page_alertas)
        self.stack.addWidget(self.page_config)

        root = QHBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(sidebar)
        root.addWidget(self.stack)

        self.setLayout(root)
        self._navegar("Visão Geral")

        # Restaura última página visitada
        ultima = int(get_config("ultima_pagina", "0"))
        paginas = ["Visão Geral", "Logs", "Alertas", "Configurações"]
        self._navegar(paginas[ultima])

    def _navegar(self, nome):
        mapa = {
            "Visão Geral":   0,
            "Logs":          1,
            "Alertas":       2,
            "Configurações": 3,
        }
        idx = mapa.get(nome, 0)
        self.stack.setCurrentIndex(idx)

        for texto, btn in self._botoes:
            btn.setChecked(texto == nome)

        paginas = [self.page_home, self.page_logs, self.page_alertas, self.page_config]
        pagina = paginas[idx]
        if hasattr(pagina, "atualizar"):
            pagina.atualizar()

    def _salvar_estado(self):
        from models import salvar_estado

        estado = {}
        estado["ultima_pagina"]     = str(self.stack.currentIndex())
        estado["logs_usuario"]      = self.page_logs.input_usuario.text()
        estado["logs_evento"]       = self.page_logs.input_evento.text()
        estado["logs_resultado"]    = str(self.page_logs.combo_sucesso.currentIndex())
        estado["logs_data_ini"]     = self.page_logs.date_ini.date().toString("yyyy-MM-dd")
        estado["logs_data_fim"]     = self.page_logs.date_fim.date().toString("yyyy-MM-dd")
        estado["alertas_periodo"]   = str(self.page_alertas.combo_periodo.currentIndex())
        estado["polling_intervalo"] = str(self.page_config.spin_intervalo.value())
        estado["som_ativo"]         = str(self.page_config.chk_som.isChecked()).lower()

        salvar_estado(estado)

    def logout(self):
        self._salvar_estado()
        if hasattr(self.page_alertas, "parar_timer"):
            self.page_alertas.parar_timer()
        self.close()
        self.login_window.show()

    def closeEvent(self, event):
        self._salvar_estado()
        if hasattr(self.page_alertas, "parar_timer"):
            self.page_alertas.parar_timer()
        event.accept()