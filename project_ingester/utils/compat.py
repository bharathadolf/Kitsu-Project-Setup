# ============================================================================
# PySide Compatibility
# ============================================================================
try:
    from PySide6 import QtWidgets, QtCore, QtGui
    from PySide6.QtCore import Qt, Signal, Slot, QSize, QPoint, QObject
    from PySide6.QtGui import QPainter, QPainterPath, QPen, QColor, QAction
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
        QPushButton, QLabel, QLineEdit, QSplitter, QFrame, QScrollArea,
        QFormLayout, QComboBox, QSpinBox, QTextEdit, QCheckBox
    )
    QT_VERSION = 6
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui
    from PySide2.QtCore import Qt, Signal, Slot, QSize, QPoint, QObject
    from PySide2.QtGui import QPainter, QPainterPath, QPen, QColor
    from PySide2.QtWidgets import (
        QAction, QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
        QPushButton, QLabel, QLineEdit, QSplitter, QFrame, QScrollArea,
        QFormLayout, QComboBox, QSpinBox, QTextEdit, QCheckBox
    )
    QT_VERSION = 2

Signal = QtCore.Signal
