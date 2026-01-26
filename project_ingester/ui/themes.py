from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Theme:
    name: str
    colors: Dict[str, str]
    
    @property
    def main_window_style(self):
        return f"""
            QMainWindow, QWidget {{
                background-color: {self.colors['bg_main']};
                color: {self.colors['text_main']};
            }}
            QSplitter::handle {{
                background-color: {self.colors['border']};
            }}
            QStatusBar {{
                background-color: {self.colors['bg_panel']};
                color: {self.colors['text_dim']};
            }}
            QMenuBar {{
                background-color: {self.colors['bg_panel']};
                color: {self.colors['text_main']};
            }}
            QMenuBar::item:selected {{
                background-color: {self.colors['bg_hover']};
            }}
            QMenu {{
                background-color: {self.colors['bg_panel']};
                border: 1px solid {self.colors['border']};
            }}
            QMenu::item:selected {{
                background-color: {self.colors['accent']};
                color: {self.colors['text_inv']};
            }}
        """

    @property
    def property_panel_style(self):
        return f"""
            QLabel {{
                color: {self.colors['text_main']};
                font-family: 'Segoe UI', sans-serif;
            }}
            QLineEdit, QComboBox, QDateEdit, QSpinBox {{
                background-color: {self.colors['bg_input']};
                color: {self.colors['text_main']};
                border: 1px solid {self.colors['border']};
                padding: 5px;
                border-radius: 3px;
                selection-background-color: {self.colors['accent']};
            }}
            QLineEdit:focus, QComboBox:focus {{
                border: 1px solid {self.colors['accent']};
                background-color: {self.colors['bg_input_focus']};
            }}
            QPushButton {{
                background-color: {self.colors['btn_bg']};
                color: {self.colors['btn_text']};
                border: 1px solid {self.colors['btn_border']};
                border-radius: 3px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['btn_hover']};
            }}
            QTabWidget::pane {{
                border: 1px solid {self.colors['border']};
                background-color: {self.colors['bg_panel']};
            }}
            QTabBar::tab {{
                background: {self.colors['bg_header']};
                color: {self.colors['text_dim']};
                padding: 6px 12px;
                border: 1px solid {self.colors['border']};
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background: {self.colors['bg_panel']};
                color: {self.colors['text_main']};
                border-top: 2px solid {self.colors['accent']};
            }}
            QListWidget {{
                background-color: {self.colors['bg_input']};
                color: {self.colors['text_main']};
                border: 1px solid {self.colors['border']};
            }}
        """

    def get_header_style(self, border_color):
        return f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                color: {self.colors['text_header']};
                background-color: {self.colors['bg_header']};
                padding: 8px;
                border-bottom: 2px solid {border_color};
            }}
        """

    def get_node_style(self, state="base"):
        # state: base, hover, selected
        bg = self.colors['node_bg']
        border = self.colors['node_border']
        
        if state == "hover":
            bg = self.colors['node_bg_hover']
            border = self.colors['node_border_hover']
        elif state == "selected":
            bg = self.colors['node_bg_sel']
            border = self.colors['node_border_sel']
            
        return f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 4px;
            }}
            QLineEdit {{
                border: none;
                background: transparent;
                color: {self.colors['node_text']};
                font-weight: bold;
                font-size: 8px;
                padding-bottom: 1px;
            }}
            QPushButton {{
                background-color: {self.colors['node_btn_bg']}; 
                border: 1px solid {self.colors['node_btn_bg']};
                border-radius: 7px; /* dynamic in code usually, hardcoded here for template */
                color: {self.colors['node_btn_text']};
                font-weight: bold;
                font-size: 7px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['node_btn_hover']};
                border: 1px solid {self.colors['node_btn_hover']};
            }}
        """

# 1. Dark Theme (Visual Studio-like)
DARK_THEME = Theme(
    name="Dark",
    colors={
        'bg_main': '#1e1e1e',
        'bg_panel': '#252526',
        'bg_header': '#2d2d30',
        'bg_input': '#333333',
        'bg_input_focus': '#383838',
        'bg_hover': '#3e3e42',
        
        'text_main': '#f0f0f0',
        'text_dim': '#aaaaaa',
        'text_inv': '#ffffff',
        'text_header': '#ffffff',
        
        'accent': '#007acc',
        'border': '#3e3e42',
        
        'btn_bg': '#3e3e42',
        'btn_text': '#f0f0f0',
        'btn_border': '#555555',
        'btn_hover': '#4e4e52',
        
        'node_bg': '#333333',
        'node_border': '#555555',
        'node_bg_hover': '#444444',
        'node_border_hover': '#777777',
        'node_bg_sel': '#2c5f8a',
        'node_border_sel': '#4da6ff',
        'node_text': '#e0e0e0',
        
        'node_btn_bg': '#0d47a1',
        'node_btn_text': '#ffffff',
        'node_btn_hover': '#1976d2',
    }
)

# 2. Light Theme (Standard Qt)
LIGHT_THEME = Theme(
    name="Light",
    colors={
        'bg_main': '#f0f0f0',
        'bg_panel': '#ffffff',
        'bg_header': '#e1e1e1',
        'bg_input': '#ffffff',
        'bg_input_focus': '#ffffff',
        'bg_hover': '#e5f3ff',
        
        'text_main': '#333333',
        'text_dim': '#666666',
        'text_inv': '#ffffff',
        'text_header': '#333333',
        
        'accent': '#0078d7',
        'border': '#cccccc',
        
        'btn_bg': '#e1e1e1',
        'btn_text': '#333333',
        'btn_border': '#adadad',
        'btn_hover': '#e5f1fb',
        
        'node_bg': '#ffffff',
        'node_border': '#bbbbbb',
        'node_bg_hover': '#f5f5f5',
        'node_border_hover': '#999999',
        'node_bg_sel': '#cce8ff',
        'node_border_sel': '#0078d7',
        'node_text': '#333333',
        
        'node_btn_bg': '#0078d7',
        'node_btn_text': '#ffffff',
        'node_btn_hover': '#005a9e',
    }
)

# 3. Hydro Theme (Ocean/Teal)
HYDRO_THEME = Theme(
    name="Hydro",
    colors={
        'bg_main': '#1e2a36',
        'bg_panel': '#243442',
        'bg_header': '#2c4154',
        'bg_input': '#18222c',
        'bg_input_focus': '#18222c',
        'bg_hover': '#2f495f',
        
        'text_main': '#d1ecf1',
        'text_dim': '#8faac1',
        'text_inv': '#1e2a36',
        'text_header': '#ffffff',
        
        'accent': '#00e5ff',
        'border': '#375066',
        
        'btn_bg': '#2c4154',
        'btn_text': '#00e5ff',
        'btn_border': '#00e5ff',
        'btn_hover': '#375066',
        
        'node_bg': '#2c4154',
        'node_border': '#375066',
        'node_bg_hover': '#375066',
        'node_border_hover': '#00e5ff',
        'node_bg_sel': '#004c57',
        'node_border_sel': '#00e5ff',
        'node_text': '#d1ecf1',
        
        'node_btn_bg': '#00acc1',
        'node_btn_text': '#ffffff',
        'node_btn_hover': '#00e5ff',
    }
)

# 4. Cyberpunk Theme
CYBER_THEME = Theme(
    name="Cyberpunk",
    colors={
        'bg_main': '#0f0214',
        'bg_panel': '#1a0524',
        'bg_header': '#2d0a3d',
        'bg_input': '#15051f',
        'bg_input_focus': '#1a0524',
        'bg_hover': '#3d0d52',
        
        'text_main': '#ffe6fb',
        'text_dim': '#d67bc8',
        'text_inv': '#000000',
        'text_header': '#ff00cc',
        
        'accent': '#ff00cc',
        'border': '#52126b',
        
        'btn_bg': '#2d0a3d',
        'btn_text': '#00fffa',
        'btn_border': '#00fffa',
        'btn_hover': '#52126b',
        
        'node_bg': '#1a0524',
        'node_border': '#52126b',
        'node_bg_hover': '#2d0a3d',
        'node_border_hover': '#ff00cc',
        'node_bg_sel': '#3d0d52',
        'node_border_sel': '#00fffa',
        'node_text': '#ffe6fb',
        
        'node_btn_bg': '#b0008d',
        'node_btn_text': '#ffffff',
        'node_btn_hover': '#ff00cc',
    }
)

THEME_LIST = [DARK_THEME, LIGHT_THEME, HYDRO_THEME, CYBER_THEME]

def get_next_theme(current_name: str) -> Theme:
    for i, theme in enumerate(THEME_LIST):
        if theme.name == current_name:
            next_index = (i + 1) % len(THEME_LIST)
            return THEME_LIST[next_index]
    return DARK_THEME
