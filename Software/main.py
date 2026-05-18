import sys
from PySide6.QtWidgets import QApplication
from models import init_db
from views import LoginWindow

init_db()

app = QApplication(sys.argv)
app.setStyle("Fusion")

window = LoginWindow()
window.show()

sys.exit(app.exec())