from PySide6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QFrame,
    QVBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QBrush
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QDateTimeAxis, QValueAxis
from PySide6.QtCore import QDateTime
from models import get_stats, get_atividade_por_hora


class CardWidget(QFrame):
    def __init__(self, titulo, valor="0", cor_valor="#ffffff"):
        super().__init__()
        self.setObjectName("card")
        self.setStyleSheet("""
            QFrame#card {
                background-color: #1e1e2e;
                border-radius: 10px;
                border: 1px solid #313244;
            }
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(100)

        layout = QVBoxLayout()
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setAlignment(Qt.AlignCenter)

        self.label_titulo = QLabel(titulo)
        self.label_titulo.setAlignment(Qt.AlignCenter)
        self.label_titulo.setStyleSheet("color: #a6adc8; font-size: 12px; border: none; background: transparent;")

        self.label_valor = QLabel(valor)
        self.label_valor.setAlignment(Qt.AlignCenter)
        self.label_valor.setStyleSheet(f"color: {cor_valor}; font-size: 28px; font-weight: bold; border: none; background: transparent;")

        layout.addWidget(self.label_titulo)
        layout.addWidget(self.label_valor)
        self.setLayout(layout)

    def set_valor(self, valor):
        self.label_valor.setText(str(valor))


class GraficoAtividade(QChartView):
    def __init__(self):
        super().__init__()
        self.setRenderHint(QPainter.Antialiasing)
        self.setMinimumHeight(220)
        self.atualizar()

    def atualizar(self):
        dados = get_atividade_por_hora()

        series = QLineSeries()
        series.setColor(QColor("#89b4fa"))

        for hora, total in dados:
            dt = QDateTime.fromString(str(hora)[:19], "yyyy-MM-dd HH:mm:ss")
            series.append(dt.toMSecsSinceEpoch(), total)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Atividade nos últimos 30 dias")
        chart.setBackgroundBrush(QBrush(QColor("#1e1e2e")))
        chart.setTitleBrush(QBrush(QColor("#cdd6f4")))
        chart.legend().hide()

        axis_x = QDateTimeAxis()
        axis_x.setFormat("HH:mm")
        axis_x.setTitleText("Hora")
        axis_x.setLabelsColor(QColor("#a6adc8"))
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setTitleText("Eventos")
        axis_y.setLabelsColor(QColor("#a6adc8"))
        axis_y.setLabelFormat("%d")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        self.setChart(chart)
        self.setStyleSheet("background: #1e1e2e; border-radius: 10px;")


class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #181825;")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        titulo = QLabel("Visão Geral")
        titulo.setStyleSheet("color: #cdd6f4; font-size: 18px; font-weight: bold;")
        main_layout.addWidget(titulo)

        grid = QGridLayout()
        grid.setSpacing(12)

        self.card_eventos   = CardWidget("Total de Eventos",     "0", "#89b4fa")
        self.card_falhas    = CardWidget("Falhas de Login",      "0", "#f38ba8")
        self.card_logins    = CardWidget("Logins bem-sucedidos", "0", "#a6e3a1")
        self.card_ips       = CardWidget("IPs únicos",           "0", "#fab387")
        self.card_bloqueios = CardWidget("Contas bloqueadas",    "0", "#f9e2af")

        grid.addWidget(self.card_eventos,   0, 0)
        grid.addWidget(self.card_falhas,    0, 1)
        grid.addWidget(self.card_logins,    0, 2)
        grid.addWidget(self.card_ips,       1, 0)
        grid.addWidget(self.card_bloqueios, 1, 1)

        main_layout.addLayout(grid)

        self.grafico = GraficoAtividade()
        main_layout.addWidget(self.grafico)
        main_layout.addStretch()

        self.setLayout(main_layout)
        self.atualizar()

    def atualizar(self):
        stats = get_stats()
        self.card_eventos.set_valor(stats["total"])
        self.card_falhas.set_valor(stats["falhas"])
        self.card_logins.set_valor(stats["logins_ok"])
        self.card_ips.set_valor(stats["ips_unicos"])
        self.card_bloqueios.set_valor(stats["bloqueios"])
        self.grafico.atualizar()