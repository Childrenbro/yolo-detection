# ui_login.py (完整替换)
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, 
                             QMessageBox, QApplication, QStackedWidget, QGridLayout, QFrame)
from PyQt6.QtCore import Qt
# 导入我们新增的 update_password 函数
from database import add_user, check_user, update_password

class LoginPage(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        login_button = QPushButton("Login")
        login_button.clicked.connect(self.login)
        layout.addWidget(QLabel("<h2>User Login</h2>"))
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(login_button)
        
    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if check_user(username, password):
            self.on_login_success()
        else:
            QMessageBox.warning(self, "Login failed", "Username or password is incorrect.")

class RegisterPage(QWidget):
    # 添加一个回调函数参数，用于注册成功后切换页面
    def __init__(self, switch_to_login_page_callback):
        super().__init__()
        self.switch_to_login_page = switch_to_login_page_callback
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Set Username")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Set Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm Password")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        register_button = QPushButton("Register")
        register_button.clicked.connect(self.register)
        layout.addWidget(QLabel("<h2>New User Registration</h2>"))
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.confirm_password_input)
        layout.addWidget(register_button)

    def register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if password != confirm_password:
            QMessageBox.warning(self, "Registration failed", "The two passwords do not match.")
            return
        
        success, message = add_user(username, password)
        if success:
            QMessageBox.information(self, "Success", message + "\nYou can now return to login.")
            # 优化：注册成功后，自动切换回登录页面
            self.switch_to_login_page()
        else:
            QMessageBox.warning(self, "Registration failed", message)

# --- 找回密码页面 ---
class ForgotPasswordPage(QWidget):
    def __init__(self, switch_to_login_page_callback):
        super().__init__()
        self.switch_to_login_page = switch_to_login_page_callback
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Please enter your username")
        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("Please enter new password")
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_new_password_input = QLineEdit()
        self.confirm_new_password_input.setPlaceholderText("Please confirm new password")
        self.confirm_new_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        reset_button = QPushButton("Reset Password")
        reset_button.clicked.connect(self.reset_password)

        layout.addWidget(QLabel("<h2>Forgot Password</h2>"))
        layout.addWidget(self.username_input)
        layout.addWidget(self.new_password_input)
        layout.addWidget(self.confirm_new_password_input)
        layout.addWidget(reset_button)

    def reset_password(self):
        username = self.username_input.text()
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_new_password_input.text()

        if not username or not new_password:
            QMessageBox.warning(self, "Reset failed", "Username and new password cannot be empty.")
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, "Reset failed", "The two entered passwords do not match.")
            return
        
        success, message = update_password(username, new_password)
        if success:
            QMessageBox.information(self, "Success", message + "\nPlease use your new password to log in.")
            # 重置成功后，自动切换回登录页面
            self.switch_to_login_page()
        else:
            QMessageBox.warning(self, "Reset failed", message)

class LoginWindow(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.setWindowTitle("Container Intelligent Damage Detection System - Login")
        self.setFixedSize(400, 480) # 稍微增加一点高度以容纳新按钮
        self.on_login_success = on_login_success

        main_layout = QVBoxLayout(self)
        self.stacked_widget = QStackedWidget()

        # 定义一个切换到登录页的通用动作
        go_to_login_action = lambda: self.stacked_widget.setCurrentWidget(self.login_page)

        # 创建所有页面
        self.login_page = LoginPage(self.on_login_success_internal)
        self.register_page = RegisterPage(go_to_login_action)
        self.forgot_password_page = ForgotPasswordPage(go_to_login_action)

        # 将所有页面添加到堆叠窗口
        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.register_page)
        self.stacked_widget.addWidget(self.forgot_password_page)

        main_layout.addWidget(self.stacked_widget)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)

        # 底部导航按钮
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        
        self.to_register_button = QPushButton("No account? Register")
        self.to_login_button = QPushButton("Already have an account? Login")
        self.to_forgot_password_button = QPushButton("Forgot password?") # 新增按钮

        self.to_register_button.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.register_page))
        self.to_login_button.clicked.connect(go_to_login_action)
        self.to_forgot_password_button.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.forgot_password_page))

        button_layout.addWidget(self.to_register_button)
        button_layout.addWidget(self.to_forgot_password_button) # 添加到布局
        button_layout.addWidget(self.to_login_button)
        main_layout.addWidget(button_container)

        self.setStyleSheet("""
            /* 登录窗口背景：使用纯色背景，避免依赖外部图片文件 */
            QWidget {
                background-color: #F5F7FA; /* 浅灰背景 */
            }

            /* 登录面板（输入框和按钮的容器，需确保有一个QFrame命名为login_frame） */
            #login_frame {
                background-color: rgba(245, 247, 250, 0.85); /* 浅灰半透明 */
                border-radius: 4px; /* 工业风小方角 */
                padding: 20px;
            }

            /* 用户名/密码输入框 */
            QLineEdit {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 5px;
            }

            /* 登录/注册/忘记密码按钮 */
            QPushButton {
                background-color: #333644; /* 深灰主色 */
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #FF7A00; /* 集装箱橙 hover色 */
            }

            /* 标题文字（需确保标签命名为title_label） */
            QLabel#title_label {
                color: #333644;
                font-size: 20px;
                font-weight: bold;
            }

            /* 副标题文字（需确保标签命名为sub_title_label） */
            QLabel#sub_title_label {
                color: #666;
                font-size: 12px;
            }
        """)

        




        # 默认显示登录页面
        self.stacked_widget.setCurrentWidget(self.login_page)

        

    def on_login_success_internal(self):
        self.close()
        self.on_login_success()