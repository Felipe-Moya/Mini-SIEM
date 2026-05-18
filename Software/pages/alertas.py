from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QFrame,
    QPushButton, QHeaderView, QTabWidget,
    QComboBox, QDateEdit, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QDate, QSize, QUrl
from PySide6.QtGui import QColor, QPixmap, QPainter, QIcon
from PySide6.QtMultimedia import QSoundEffect
import os
from models import get_alertas, get_logs_desde, get_contas_bloqueadas, desbloquear_conta


ESTILO_TABELA = """
    QTableWidget {
        background-color: #1e1e2e;
        color: #cdd6f4;
        gridline-color: #313244;
        border: 1px solid #313244;
        border-radius: 8px;
    }
    QHeaderView::section {
        background-color: #181825;
        color: #a6adc8;
        padding: 6px;
        border: none;
        border-bottom: 1px solid #313244;
        font-weight: bold;
    }
    QTableWidget::item:alternate { background-color: #24273a; }
    QTableWidget::item:selected  { background-color: #313244; }
"""


class DatePickerWidget(QFrame):
    def __init__(self, date=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: #313244;
                border: 1px solid #45475a;
                border-radius: 5px;
            }
            QFrame:hover { border: 1px solid #89b4fa; }
        """)
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(0)

        self.date_edit = QDateEdit(date or QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setButtonSymbols(QDateEdit.ButtonSymbols.NoButtons)
        self.date_edit.setStyleSheet("""
            QDateEdit {
                background: transparent;
                color: #cdd6f4;
                border: none;
                padding: 4px 0px;
            }
        """)

        self.btn = QPushButton()
        self.btn.setFixedSize(28, 28)
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-left: 1px solid #45475a;
                border-radius: 0 5px 5px 0;
                padding: 2px;
            }
            QPushButton:hover { background: #45475a; }
        """)
        self.btn.clicked.connect(self.date_edit.setFocus)

        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setPen(QColor("#89b4fa"))
        painter.drawRect(0, 2, 15, 13)
        painter.drawLine(0, 6, 15, 6)
        painter.drawLine(4, 0, 4, 4)
        painter.drawLine(11, 0, 11, 4)
        painter.end()
        self.btn.setIcon(QIcon(pixmap))
        self.btn.setIconSize(QSize(14, 14))

        layout.addWidget(self.date_edit)
        layout.addWidget(self.btn)
        self.setLayout(layout)

    def date(self):
        return self.date_edit.date()

    def setDate(self, date):
        self.date_edit.setDate(date)


class AlertasPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #181825;")

        self.ultimo_id = 0
        self.som_ativo = True

        self.som = QSoundEffect()
        som_path = os.path.join(os.path.dirname(__file__), "..", "assets", "alerta.wav")
        if os.path.exists(som_path):
            self.som.setSource(QUrl.fromLocalFile(os.path.abspath(som_path)))
            self.som.setVolume(0.7)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # ── Cabeçalho ──────────────────────────────────────────────────────────
        header = QHBoxLayout()
        titulo = QLabel("Alertas de Segurança")
        titulo.setStyleSheet("color: #cdd6f4; font-size: 18px; font-weight: bold;")
        header.addWidget(titulo)
        header.addStretch()

        self.lbl_status = QLabel("● Monitorando")
        self.lbl_status.setStyleSheet("color: #a6e3a1; font-size: 12px;")
        header.addWidget(self.lbl_status)

        self.btn_som = QPushButton("Som: ON")
        self.btn_som.setCheckable(True)
        self.btn_som.setChecked(True)
        self.btn_som.setCursor(Qt.PointingHandCursor)
        self.btn_som.setStyleSheet("""
            QPushButton {
                background: #313244; color: #cdd6f4;
                border-radius: 5px; padding: 5px 12px; font-size: 12px;
            }
            QPushButton:hover { background: #45475a; }
        """)
        self.btn_som.clicked.connect(self._toggle_som)
        header.addWidget(self.btn_som)

        self.btn_atualizar = QPushButton("Atualizar")
        self.btn_atualizar.setCursor(Qt.PointingHandCursor)
        self.btn_atualizar.setStyleSheet("""
            QPushButton {
                background: #89b4fa; color: #1e1e2e;
                border-radius: 5px; padding: 5px 12px; font-weight: bold;
            }
            QPushButton:hover { background: #b4d0ff; }
        """)
        self.btn_atualizar.clicked.connect(self.atualizar)
        header.addWidget(self.btn_atualizar)
        main_layout.addLayout(header)

        # ── Filtros ────────────────────────────────────────────────────────────
        filtro_frame = QFrame()
        filtro_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e2e;
                border-radius: 8px;
                border: 1px solid #313244;
            }
        """)
        filtro_layout = QHBoxLayout()
        filtro_layout.setContentsMargins(12, 10, 12, 10)
        filtro_layout.setSpacing(10)

        filtro_layout.addWidget(self._label("Período:"))
        self.combo_periodo = QComboBox()
        self.combo_periodo.addItems(["Últimas 24h", "Últimos 7 dias", "Últimos 30 dias", "Personalizado"])
        self.combo_periodo.setCurrentIndex(2)
        self.combo_periodo.setStyleSheet("""
            QComboBox {
                background: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 5px;
                padding: 4px 8px; min-width: 140px;
            }
            QComboBox::drop-down { border: none; width: 0px; }
            QComboBox::down-arrow { width: 0px; height: 0px; }
            QComboBox QAbstractItemView {
                background: #313244; color: #cdd6f4;
                border: 1px solid #45475a;
                selection-background-color: #45475a;
            }
        """)
        self.combo_periodo.currentIndexChanged.connect(self._on_periodo_changed)
        filtro_layout.addWidget(self.combo_periodo)

        self.date_ini = DatePickerWidget(QDate.currentDate().addDays(-1))
        self.date_ini.setVisible(False)
        filtro_layout.addWidget(self.date_ini)

        self.date_fim = DatePickerWidget(QDate.currentDate())
        self.date_fim.setVisible(False)
        filtro_layout.addWidget(self.date_fim)

        self.btn_filtrar = QPushButton("Filtrar")
        self.btn_filtrar.setCursor(Qt.PointingHandCursor)
        self.btn_filtrar.setStyleSheet("""
            QPushButton {
                background: #89b4fa; color: #1e1e2e;
                border-radius: 5px; padding: 5px 16px; font-weight: bold;
            }
            QPushButton:hover { background: #b4d0ff; }
        """)
        self.btn_filtrar.clicked.connect(self.atualizar)
        filtro_layout.addWidget(self.btn_filtrar)
        filtro_layout.addStretch()

        filtro_frame.setLayout(filtro_layout)
        main_layout.addWidget(filtro_frame)

        # Banner
        self.banner = QLabel("")
        self.banner.setAlignment(Qt.AlignCenter)
        self.banner.setStyleSheet("""
            background: #f38ba8; color: #1e1e2e;
            font-weight: bold; font-size: 13px;
            border-radius: 6px; padding: 6px;
        """)
        self.banner.hide()
        main_layout.addWidget(self.banner)

        # ── Abas ───────────────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #313244;
                border-radius: 8px;
                background: #1e1e2e;
            }
            QTabBar::tab {
                background: #181825; color: #a6adc8;
                padding: 6px 18px; border-radius: 4px; margin-right: 4px;
            }
            QTabBar::tab:selected { background: #313244; color: #cdd6f4; }
        """)

        self.tabela_tempo_real = self._criar_tabela()
        self.tabela_perm       = self._criar_tabela()
        self.tabela_temp       = self._criar_tabela()
        self.tabela_ips        = self._criar_tabela_ips()
        self.tabela_desbloqueio = self._criar_tabela_desbloqueio()

        self.tabs.addTab(self._wrap(self.tabela_tempo_real),  "Tempo Real")
        self.tabs.addTab(self._wrap(self.tabela_perm),        "Bloqueios Permanentes")
        self.tabs.addTab(self._wrap(self.tabela_temp),        "Bloqueios Temporários")
        self.tabs.addTab(self._wrap(self.tabela_ips),         "IPs Suspeitos")
        self.tabs.addTab(self._wrap(self.tabela_desbloqueio), "Desbloquear Contas")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

        self.timer = QTimer()
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self._polling)
        self.timer.start()

        from models import get_config
        self.combo_periodo.setCurrentIndex(int(get_config("alertas_periodo", "2")))

        self.atualizar()

    def _label(self, texto):
        lbl = QLabel(texto)
        lbl.setStyleSheet("color: #a6adc8; font-size: 12px; border: none; background: transparent;")
        return lbl

    def _criar_tabela(self):
        t = QTableWidget()
        t.setColumnCount(6)
        t.setHorizontalHeaderLabels(["ID", "Usuário", "IP", "Evento", "Sucesso", "Data/Hora"])
        t.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectRows)
        t.verticalHeader().setVisible(False)
        t.setAlternatingRowColors(True)
        t.setStyleSheet(ESTILO_TABELA)
        return t

    def _criar_tabela_ips(self):
        t = QTableWidget()
        t.setColumnCount(2)
        t.setHorizontalHeaderLabels(["IP", "Tentativas"])
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectRows)
        t.verticalHeader().setVisible(False)
        t.setAlternatingRowColors(True)
        t.setStyleSheet(ESTILO_TABELA)
        return t

    def _criar_tabela_desbloqueio(self):
        t = QTableWidget()
        t.setColumnCount(5)
        t.setHorizontalHeaderLabels(["Usuário", "Nome", "Nível", "Bloqueado até", "Ação"])
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        t.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        t.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        t.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        t.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectRows)
        t.verticalHeader().setVisible(False)
        t.setAlternatingRowColors(True)
        t.setStyleSheet(ESTILO_TABELA)
        return t

    def _wrap(self, widget):
        w = QWidget()
        l = QVBoxLayout()
        l.setContentsMargins(8, 8, 8, 8)
        l.addWidget(widget)
        w.setLayout(l)
        return w

    def _preencher_tabela(self, tabela, rows):
        tabela.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if c == 4:
                    cor = "#a6e3a1" if str(val) == "1" else "#f38ba8"
                    item.setForeground(QColor(cor))
                    item.setText("✓" if str(val) == "1" else "✗")
                tabela.setItem(r, c, item)

    def _carregar_desbloqueio(self):
        contas = get_contas_bloqueadas()
        self.tabela_desbloqueio.setRowCount(len(contas))

        for r, (username, name, lock_level, blck_unt, perm_block) in enumerate(contas):
            # Usuário
            self.tabela_desbloqueio.setItem(r, 0, QTableWidgetItem(username))

            # Nome
            self.tabela_desbloqueio.setItem(r, 1, QTableWidgetItem(name or ""))

            # Nível
            if perm_block:
                nivel_item = QTableWidgetItem("PERMANENTE")
                nivel_item.setForeground(QColor("#f38ba8"))
            else:
                nivel_item = QTableWidgetItem(f"Nível {lock_level}")
                nivel_item.setForeground(QColor("#fab387"))
            nivel_item.setTextAlignment(Qt.AlignCenter)
            self.tabela_desbloqueio.setItem(r, 2, nivel_item)

            # Bloqueado até
            ate = blck_unt[:19] if blck_unt else ("Permanente" if perm_block else "-")
            ate_item = QTableWidgetItem(ate)
            ate_item.setTextAlignment(Qt.AlignCenter)
            self.tabela_desbloqueio.setItem(r, 3, ate_item)

            # Botão desbloquear
            btn = QPushButton("Desbloquear")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: #a6e3a1; color: #1e1e2e;
                    border-radius: 4px; padding: 4px 10px;
                    font-weight: bold; font-size: 12px;
                }
                QPushButton:hover { background: #c3f0c0; }
            """)
            btn.clicked.connect(lambda checked, u=username, p=bool(perm_block): self._confirmar_desbloqueio(u, p))
            self.tabela_desbloqueio.setCellWidget(r, 4, btn)

        self.tabela_desbloqueio.resizeRowsToContents()

    def _confirmar_desbloqueio(self, username, permanente):
        tipo = "permanente" if permanente else "temporário"
        msg = QMessageBox(self)
        msg.setWindowTitle("Confirmar desbloqueio")
        msg.setText(f"Desbloquear a conta '{username}'?\nBloqueio: {tipo}")
        msg.setIcon(QMessageBox.Warning)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.button(QMessageBox.Yes).setText("Sim")
        msg.button(QMessageBox.No).setText("Cancelar")
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #1e1e2e;
            }
            QMessageBox QLabel {
                color: #cdd6f4;
                background-color: transparent;
            }
            QMessageBox QLabel#qt_msgboxex_icon_label {
                background-color: transparent;
            }
            QPushButton {
                background: #313244; color: #cdd6f4;
                border-radius: 5px; padding: 5px 16px; min-width: 80px;
            }
            QPushButton:hover { background: #45475a; }
        """)

        if msg.exec() == QMessageBox.Yes:
            try:
                desbloquear_conta(username)
                self._mostrar_banner_verde(f"Conta '{username}' desbloqueada com sucesso!")
                self._carregar_desbloqueio()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao desbloquear: {e}")

    def _mostrar_banner_verde(self, texto):
        self.banner.setText(f"✓  {texto}")
        self.banner.setStyleSheet("""
            background: #a6e3a1; color: #1e1e2e;
            font-weight: bold; font-size: 13px;
            border-radius: 6px; padding: 6px;
        """)
        self.banner.show()
        QTimer.singleShot(5000, self.banner.hide)

    def _get_intervalo(self):
        idx = self.combo_periodo.currentIndex()
        if idx == 0:
            return "24 hours"
        elif idx == 1:
            return "7 days"
        elif idx == 2:
            return "30 days"
        else:
            ini = self.date_ini.date().toString("yyyy-MM-dd") + " 00:00:00"
            fim = self.date_fim.date().toString("yyyy-MM-dd") + " 23:59:59"
            return (ini, fim)

    def _on_periodo_changed(self, idx):
        personalizado = idx == 3
        self.date_ini.setVisible(personalizado)
        self.date_fim.setVisible(personalizado)

    def atualizar(self):
        intervalo = self._get_intervalo()
        perm, temp, ips = get_alertas(intervalo)
        self._preencher_tabela(self.tabela_perm, perm)
        self._preencher_tabela(self.tabela_temp, temp)

        self.tabela_ips.setRowCount(len(ips))
        for r, (ip, tentativas) in enumerate(ips):
            item_ip   = QTableWidgetItem(str(ip))
            item_tent = QTableWidgetItem(str(tentativas))
            item_tent.setForeground(QColor("#f38ba8"))
            item_tent.setTextAlignment(Qt.AlignCenter)
            self.tabela_ips.setItem(r, 0, item_ip)
            self.tabela_ips.setItem(r, 1, item_tent)

        self._carregar_desbloqueio()

        if perm:
            self.ultimo_id = max(self.ultimo_id, perm[0][0])
        if temp:
            self.ultimo_id = max(self.ultimo_id, temp[0][0])

    def _polling(self):
        novos = get_logs_desde(self.ultimo_id)
        if not novos:
            return
        self.ultimo_id = novos[0][0]
        suspeitos = [r for r in novos if "bloqueada" in str(r[3]) or "falha" in str(r[3])]
        if suspeitos:
            self._preencher_tabela(self.tabela_tempo_real, suspeitos)
            self._mostrar_banner(len(suspeitos))
            if self.som_ativo:
                self.som.play()
        self.atualizar()

    def _mostrar_banner(self, qtd):
        self.banner.setText(f"⚠  {qtd} novo(s) evento(s) suspeito(s) detectado(s)!")
        self.banner.setStyleSheet("""
            background: #f38ba8; color: #1e1e2e;
            font-weight: bold; font-size: 13px;
            border-radius: 6px; padding: 6px;
        """)
        self.banner.show()
        QTimer.singleShot(6000, self.banner.hide)

    def _toggle_som(self):
        self.som_ativo = self.btn_som.isChecked()
        self.btn_som.setText("Som: ON" if self.som_ativo else "Som: OFF")

    def parar_timer(self):
        self.timer.stop()