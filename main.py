# main.py
import sys
from PyQt6.QtWidgets import QApplication
from ui_login import LoginWindow
from ui_main_window import MainWindow
class AppController:
    def __init__(self):
        self.login_window = None
        self.main_window = None
    def show_login(self):
        self.login_window = LoginWindow(on_login_success=self.show_main_window)
        self.login_window.show()
    def show_main_window(self):
        self.main_window = MainWindow()
        self.main_window.show()
        if self.login_window:
            self.login_window.close()
if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = AppController()
    controller.show_login()
    sys.exit(app.exec())