from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QComboBox, QDateEdit,
    QHeaderView, QFrame
)
from PySide6.QtCore import Qt, QDate, QSize, QTimer
from PySide6.QtGui import QColor, QPixmap, QPainter, QIcon
from models import get_config

CORES_EVENTO = {
    "login_sucesso":          "#a6e3a1",
    "logout":                 "#89dceb",
    "conta_bloqueada_perm":   "#f38ba8",
    "conta_bloqueada_temp":   "#fab387",
    "desbloqueio_automatico": "#f9e2af",
}


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


class LogsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #181825;")

        self.current_page  = 0
        self.logs_per_page = 20

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        titulo = QLabel("Logs de Segurança")
        titulo.setStyleSheet("color: #cdd6f4; font-size: 18px; font-weight: bold;")
        main_layout.addWidget(titulo)

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

        self.input_usuario = QLineEdit()
        self._estilizar_input(self.input_usuario, "Usuário")
        filtro_layout.addWidget(self.input_usuario)

        self.input_evento = QLineEdit()
        self._estilizar_input(self.input_evento, "Evento")
        filtro_layout.addWidget(self.input_evento)

        self.combo_sucesso = QComboBox()
        self.combo_sucesso.addItems(["Todos", "Sucesso", "Falha"])
        self.combo_sucesso.setStyleSheet("""
            QComboBox {
                background: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 5px;
                padding: 4px 8px; min-width: 90px;
            }
            QComboBox::drop-down { border: none; width: 0px; }
            QComboBox::down-arrow { width: 0px; height: 0px; }
            QComboBox QAbstractItemView {
                background: #313244; color: #cdd6f4;
                border: 1px solid #45475a;
                selection-background-color: #45475a;
            }
        """)
        filtro_layout.addWidget(self.combo_sucesso)

        self.date_ini = DatePickerWidget(QDate.currentDate().addDays(-30))
        filtro_layout.addWidget(self.date_ini)

        self.date_fim = DatePickerWidget(QDate.currentDate())
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
        self.btn_filtrar.clicked.connect(self._aplicar_filtro)
        filtro_layout.addWidget(self.btn_filtrar)

        self.btn_limpar = QPushButton("Limpar")
        self.btn_limpar.setCursor(Qt.PointingHandCursor)
        self.btn_limpar.setStyleSheet("""
            QPushButton {
                background: #45475a; color: #cdd6f4;
                border-radius: 5px; padding: 5px 16px;
            }
            QPushButton:hover { background: #585b70; }
        """)
        self.btn_limpar.clicked.connect(self._limpar_filtros)
        filtro_layout.addWidget(self.btn_limpar)

        filtro_frame.setLayout(filtro_layout)
        main_layout.addWidget(filtro_frame)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6)
        self.tabela.setHorizontalHeaderLabels(["ID", "Usuário", "IP", "Evento", "Sucesso", "Data/Hora"])
        self.tabela.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tabela.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setStyleSheet("""
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
        """)
        main_layout.addWidget(self.tabela)

        nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton("← Anterior")
        self.btn_next = QPushButton("Próxima →")
        self.label_pagina = QLabel("Página 1")
        self.label_pagina.setStyleSheet("color: #a6adc8;")
        self.label_pagina.setAlignment(Qt.AlignCenter)

        for btn in (self.btn_prev, self.btn_next):
            btn.setStyleSheet("""
                QPushButton {
                    background: #313244; color: #cdd6f4;
                    border-radius: 5px; padding: 5px 20px;
                }
                QPushButton:hover    { background: #45475a; }
                QPushButton:disabled { background: #1e1e2e; color: #585b70; }
            """)
            btn.setCursor(Qt.PointingHandCursor)

        self.btn_prev.clicked.connect(self._prev_page)
        self.btn_next.clicked.connect(self._next_page)

        nav_layout.addWidget(self.btn_prev)
        nav_layout.addStretch()
        nav_layout.addWidget(self.label_pagina)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_next)

        main_layout.addLayout(nav_layout)
        self.setLayout(main_layout)

        # Carrega filtros salvos
        self.input_usuario.setText(get_config("logs_usuario", ""))
        self.input_evento.setText(get_config("logs_evento", ""))
        self.combo_sucesso.setCurrentIndex(int(get_config("logs_resultado", "0")))
        ini = get_config("logs_data_ini", "")
        fim = get_config("logs_data_fim", "")
        if ini:
            self.date_ini.setDate(QDate.fromString(ini, "yyyy-MM-dd"))
        if fim:
            self.date_fim.setDate(QDate.fromString(fim, "yyyy-MM-dd"))

        self._carregar()

    def _estilizar_input(self, widget, placeholder=""):
        widget.setPlaceholderText(placeholder)
        widget.setStyleSheet("""
            QLineEdit {
                background: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 5px;
                padding: 4px 8px;
            }
            QLineEdit:focus { border: 1px solid #89b4fa; }
        """)

    def _aplicar_filtro(self):
        self.current_page = 0
        self._carregar()

    def _limpar_filtros(self):
        self.input_usuario.clear()
        self.input_evento.clear()
        self.combo_sucesso.setCurrentIndex(0)
        self.date_ini.setDate(QDate.currentDate().addDays(-30))
        self.date_fim.setDate(QDate.currentDate())
        self.current_page = 0
        self._carregar()

    def _get_filtros(self):
        usuario  = self.input_usuario.text().strip()
        evento   = self.input_evento.text().strip()
        idx      = self.combo_sucesso.currentIndex()
        sucesso  = None if idx == 0 else (1 if idx == 1 else 0)
        data_ini = self.date_ini.date().toString("yyyy-MM-dd") + " 00:00:00"
        data_fim = self.date_fim.date().toString("yyyy-MM-dd") + " 23:59:59"
        return usuario, evento, sucesso, data_ini, data_fim

    def _carregar(self):
        from models import get_logs_paginated
        usuario, evento, sucesso, data_ini, data_fim = self._get_filtros()
        offset = self.current_page * self.logs_per_page

        logs = get_logs_paginated(
            self.logs_per_page, offset,
            usuario=usuario, evento=evento,
            sucesso=sucesso, data_ini=data_ini, data_fim=data_fim
        )

        self.tabela.setRowCount(len(logs))

        for row_idx, row_data in enumerate(logs):
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                if col_idx in (0, 4):
                    item.setTextAlignment(Qt.AlignCenter)
                else:
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)

                if col_idx == 3:
                    cor = "#cdd6f4"
                    for chave, c in CORES_EVENTO.items():
                        if chave in str(value):
                            cor = c
                            break
                    item.setForeground(QColor(cor))

                if col_idx == 4:
                    cor = "#a6e3a1" if str(value) == "1" else "#f38ba8"
                    item.setForeground(QColor(cor))
                    item.setText("✓" if str(value) == "1" else "✗")

                self.tabela.setItem(row_idx, col_idx, item)

        self.label_pagina.setText(f"Página {self.current_page + 1}")
        self.btn_prev.setEnabled(self.current_page > 0)
        self.btn_next.setEnabled(len(logs) == self.logs_per_page)

    def _next_page(self):
        from models import get_logs_paginated
        self.current_page += 1
        usuario, evento, sucesso, data_ini, data_fim = self._get_filtros()
        logs = get_logs_paginated(
            self.logs_per_page, self.current_page * self.logs_per_page,
            usuario=usuario, evento=evento,
            sucesso=sucesso, data_ini=data_ini, data_fim=data_fim
        )
        if not logs:
            self.current_page -= 1
            return
        self._carregar()

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._carregar()

    def atualizar(self):
        self._carregar()