from datetime import datetime
from ..utils.compat import *

class ConsoleWidget(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Monospace';
                font-size: 11px;
                border: 1px solid #3e3e3e;
                border-radius: 3px;
            }
        """)

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        level_colors = {
            "INFO": "#4fc3f7",
            "WARNING": "#ffb74d",
            "ERROR": "#f44336",
            "SUCCESS": "#4caf50"
        }
        color = level_colors.get(level, "#d4d4d4")
        html_message = f"""
        <div style="margin: 2px 0;">
            <span style="color: #888;">[{timestamp}]</span>
            <span style="color: {color}; font-weight: bold;"> [{level}]</span>
            <span style="color: #d4d4d4; white-space: pre-wrap;"> {message}</span>
        </div>
        """
        self.append(html_message)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        
    def clear(self):
        self.setPlainText("")
