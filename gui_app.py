# -*- coding: utf-8 -*-
"""
全家便利商店包裹查詢 - Windows 視窗化應用程式
增強版：17 項功能完整實作
版本: 0.03
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Menu
import threading
import queue
import json
import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Callable
import yaml

# 第三方套件
try:
    from PIL import Image, ImageDraw
    import pystray
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

try:
    from openpyxl import Workbook
    HAS_EXCEL = True
except ImportError:
    HAS_EXCEL = False

# 導入查詢邏輯
from query_package import FamilyMartPackageQuery, VERSION

# 版本號
GUI_VERSION = "0.03"


class LocaleManager:
    """多語系管理器"""
    
    SUPPORTED_LOCALES = ['zh_TW', 'zh_CN', 'en']
    DEFAULT_LOCALE = 'zh_TW'
    
    def __init__(self, locale: str = None):
        self.locales_dir = self._get_locales_path()
        self.current_locale = locale or self.DEFAULT_LOCALE
        self.strings = {}
        self.load_locale(self.current_locale)
    
    def _get_locales_path(self) -> Path:
        """取得語系檔案目錄路徑"""
        # PyInstaller 打包後的臨時目錄
        if getattr(sys, 'frozen', False):
            # 首先嘗試 EXE 同目錄下的 locales
            exe_dir = Path(sys.executable).parent / 'locales'
            if exe_dir.exists():
                return exe_dir
            # 嘗試 PyInstaller 的 _MEIPASS 臨時目錄
            base_path = getattr(sys, '_MEIPASS', Path(sys.executable).parent)
            return Path(base_path) / 'locales'
        return Path(__file__).parent / 'locales'
    
    def load_locale(self, locale: str):
        """載入指定語系"""
        locale_file = self.locales_dir / f'{locale}.json'
        
        # 如果找不到，嘗試用底線版本
        if not locale_file.exists():
            locale_file = self.locales_dir / f'{locale.replace("-", "_")}.json'
        
        # 如果還是找不到，使用預設語系
        if not locale_file.exists():
            locale_file = self.locales_dir / f'{self.DEFAULT_LOCALE}.json'
        
        try:
            with open(locale_file, 'r', encoding='utf-8') as f:
                self.strings = json.load(f)
            self.current_locale = locale
        except Exception as e:
            print(f"Warning: Failed to load locale {locale}: {e}")
            self.strings = {}
    
    def get(self, key: str, **kwargs) -> str:
        """取得翻譯字串"""
        text = self.strings.get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        return text
    
    def __call__(self, key: str, **kwargs) -> str:
        return self.get(key, **kwargs)


class ThemeManager:
    """主題管理器"""
    
    THEMES = {
        'dark': {
            'BG_DARK': "#1a1a2e",
            'BG_SECONDARY': "#16213e",
            'BG_CARD': "#0f3460",
            'ACCENT': "#00d9ff",
            'ACCENT_HOVER': "#00b8d4",
            'SUCCESS': "#00e676",
            'WARNING': "#ffab00",
            'ERROR': "#ff5252",
            'TEXT_PRIMARY': "#ffffff",
            'TEXT_SECONDARY': "#b0b0b0",
            'BORDER': "#2a3f5f",
        },
        'light': {
            'BG_DARK': "#f5f5f5",
            'BG_SECONDARY': "#ffffff",
            'BG_CARD': "#e8e8e8",
            'ACCENT': "#0066cc",
            'ACCENT_HOVER': "#0052a3",
            'SUCCESS': "#28a745",
            'WARNING': "#ffc107",
            'ERROR': "#dc3545",
            'TEXT_PRIMARY': "#212529",
            'TEXT_SECONDARY': "#6c757d",
            'BORDER': "#dee2e6",
        }
    }
    
    def __init__(self, theme: str = 'dark'):
        self.current_theme = theme
        self.colors = self.THEMES.get(theme, self.THEMES['dark'])
    
    def set_theme(self, theme: str):
        self.current_theme = theme
        self.colors = self.THEMES.get(theme, self.THEMES['dark'])
    
    def get(self, key: str) -> str:
        return self.colors.get(key, '#000000')
    
    def apply_to_root(self, root, style: ttk.Style):
        """套用主題到根視窗"""
        c = self.colors
        root.configure(bg=c['BG_DARK'])
        
        style.theme_use('clam')
        
        # Frame
        style.configure('TFrame', background=c['BG_DARK'])
        style.configure('Card.TFrame', background=c['BG_CARD'])
        
        # LabelFrame
        style.configure('TLabelframe', background=c['BG_DARK'], foreground=c['TEXT_PRIMARY'])
        style.configure('TLabelframe.Label', 
                       background=c['BG_DARK'], 
                       foreground=c['ACCENT'],
                       font=('Microsoft JhengHei', 10, 'bold'))
        
        # Label
        style.configure('TLabel', 
                       background=c['BG_DARK'], 
                       foreground=c['TEXT_PRIMARY'],
                       font=('Microsoft JhengHei', 10))
        style.configure('Title.TLabel',
                       background=c['BG_DARK'],
                       foreground=c['ACCENT'],
                       font=('Microsoft JhengHei', 18, 'bold'))
        style.configure('Status.TLabel',
                       background=c['BG_SECONDARY'],
                       foreground=c['TEXT_SECONDARY'],
                       font=('Microsoft JhengHei', 9))
        
        # Entry
        style.configure('TEntry',
                       fieldbackground=c['BG_SECONDARY'],
                       foreground=c['TEXT_PRIMARY'],
                       insertcolor=c['ACCENT'])
        style.map('TEntry',
                 fieldbackground=[('focus', c['BG_CARD'])])
        
        # Button
        style.configure('Accent.TButton',
                       background=c['ACCENT'],
                       foreground=c['BG_DARK'] if self.current_theme == 'dark' else '#ffffff',
                       font=('Microsoft JhengHei', 11, 'bold'),
                       padding=(20, 10))
        style.map('Accent.TButton',
                 background=[('active', c['ACCENT_HOVER'])])
        
        style.configure('Secondary.TButton',
                       background=c['BG_CARD'],
                       foreground=c['TEXT_PRIMARY'],
                       font=('Microsoft JhengHei', 10),
                       padding=(15, 8))
        style.map('Secondary.TButton',
                 background=[('active', c['BG_SECONDARY'])])
        
        # Treeview
        style.configure('Treeview',
                       background=c['BG_SECONDARY'],
                       foreground=c['TEXT_PRIMARY'],
                       fieldbackground=c['BG_SECONDARY'],
                       font=('Microsoft JhengHei', 10),
                       rowheight=30)
        style.configure('Treeview.Heading',
                       background=c['BG_CARD'],
                       foreground=c['ACCENT'],
                       font=('Microsoft JhengHei', 10, 'bold'))
        style.map('Treeview',
                 background=[('selected', c['BG_CARD'])],
                 foreground=[('selected', c['ACCENT'])])
        
        # Progressbar
        style.configure('TProgressbar',
                       background=c['ACCENT'],
                       troughcolor=c['BG_SECONDARY'])
        
        # Combobox
        style.configure('TCombobox',
                       fieldbackground=c['BG_SECONDARY'],
                       background=c['BG_CARD'],
                       foreground=c['TEXT_PRIMARY'])
        
        # Checkbutton
        style.configure('TCheckbutton',
                       background=c['BG_DARK'],
                       foreground=c['TEXT_PRIMARY'])
        
        # Notebook
        style.configure('TNotebook', background=c['BG_DARK'])
        style.configure('TNotebook.Tab',
                       background=c['BG_CARD'],
                       foreground=c['TEXT_PRIMARY'],
                       padding=(15, 5))
        style.map('TNotebook.Tab',
                 background=[('selected', c['ACCENT'])],
                 foreground=[('selected', c['BG_DARK'] if self.current_theme == 'dark' else '#ffffff')])


class SettingsManager:
    """設定管理器"""
    
    DEFAULT_SETTINGS = {
        'theme': 'dark',
        'language': 'zh_TW',
        'max_retries': 5,
        'auto_refresh': False,
        'refresh_interval': 30,
        'window_x': None,
        'window_y': None,
        'window_width': 900,
        'window_height': 750,
    }
    
    def __init__(self):
        self.settings_file = self._get_settings_path()
        self.settings = self.load()
    
    def _get_settings_path(self) -> Path:
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent / 'settings.json'
        return Path(__file__).parent / 'settings.json'
    
    def load(self) -> dict:
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    return {**self.DEFAULT_SETTINGS, **saved}
            except Exception:
                pass
        return self.DEFAULT_SETTINGS.copy()
    
    def save(self):
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def get(self, key: str, default=None):
        return self.settings.get(key, default)
    
    def set(self, key: str, value):
        self.settings[key] = value
        self.save()


class HistoryManager:
    """歷史記錄管理器"""
    
    MAX_HISTORY = 100
    
    def __init__(self):
        self.history_file = self._get_history_path()
        self.history = self.load()
    
    def _get_history_path(self) -> Path:
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent / 'history.json'
        return Path(__file__).parent / 'history.json'
    
    def load(self) -> List[dict]:
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return []
    
    def save(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history[-self.MAX_HISTORY:], f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def add(self, result: dict):
        result['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.history.append(result)
        self.save()
    
    def clear(self):
        self.history = []
        self.save()


class LoadingAnimation:
    """載入動畫"""
    
    FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    
    def __init__(self, label: ttk.Label, base_text: str = ''):
        self.label = label
        self.base_text = base_text
        self.frame_index = 0
        self.running = False
        self.after_id = None
    
    def start(self, base_text: str = None):
        if base_text:
            self.base_text = base_text
        self.running = True
        self._animate()
    
    def stop(self):
        self.running = False
        if self.after_id:
            try:
                self.label.after_cancel(self.after_id)
            except Exception:
                pass
    
    def _animate(self):
        if not self.running:
            return
        frame = self.FRAMES[self.frame_index]
        self.label.config(text=f"{frame} {self.base_text}")
        self.frame_index = (self.frame_index + 1) % len(self.FRAMES)
        self.after_id = self.label.after(100, self._animate)


class ErrorDialog(tk.Toplevel):
    """自訂錯誤對話框"""
    
    def __init__(self, parent, title: str, message: str, detail: str = '', suggestion: str = '', theme: ThemeManager = None):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        
        c = theme.colors if theme else ThemeManager().colors
        self.configure(bg=c['BG_DARK'])
        
        # 圖示和訊息
        msg_frame = ttk.Frame(self, padding=20)
        msg_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(msg_frame, text="❌", font=('Segoe UI Emoji', 32)).pack()
        ttk.Label(msg_frame, text=message, wraplength=350, justify='center').pack(pady=10)
        
        if detail:
            detail_frame = ttk.LabelFrame(msg_frame, text="詳細資訊", padding=10)
            detail_frame.pack(fill=tk.X, pady=10)
            ttk.Label(detail_frame, text=detail, wraplength=330).pack()
        
        if suggestion:
            suggestion_frame = ttk.LabelFrame(msg_frame, text="建議", padding=10)
            suggestion_frame.pack(fill=tk.X, pady=10)
            ttk.Label(suggestion_frame, text=suggestion, wraplength=330).pack()
        
        ttk.Button(msg_frame, text="確定", command=self.destroy, style='Accent.TButton').pack(pady=10)
        
        self.geometry('400x300')
        self.resizable(False, False)
        
        # 置中
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f'+{x}+{y}')


class SettingsDialog(tk.Toplevel):
    """設定對話框"""
    
    def __init__(self, parent, settings: SettingsManager, locale: LocaleManager, 
                 theme: ThemeManager, on_save: Callable = None):
        super().__init__(parent)
        self.settings = settings
        self.locale = locale
        self.theme = theme
        self.on_save = on_save
        
        self.title(locale('settings_title'))
        self.transient(parent)
        self.grab_set()
        
        c = theme.colors
        self.configure(bg=c['BG_DARK'])
        
        self._create_widgets()
        
        self.geometry('400x350')
        self.resizable(False, False)
        
        # 置中
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f'+{x}+{y}')
    
    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 語言
        row1 = ttk.Frame(main_frame)
        row1.pack(fill=tk.X, pady=5)
        ttk.Label(row1, text=self.locale('language')).pack(side=tk.LEFT)
        self.lang_var = tk.StringVar(value=self.settings.get('language'))
        lang_combo = ttk.Combobox(row1, textvariable=self.lang_var, 
                                  values=['zh_TW', 'zh_CN', 'en'], state='readonly', width=15)
        lang_combo.pack(side=tk.RIGHT)
        
        # 主題
        row2 = ttk.Frame(main_frame)
        row2.pack(fill=tk.X, pady=5)
        ttk.Label(row2, text=self.locale('theme')).pack(side=tk.LEFT)
        self.theme_var = tk.StringVar(value=self.settings.get('theme'))
        theme_combo = ttk.Combobox(row2, textvariable=self.theme_var,
                                   values=['dark', 'light'], state='readonly', width=15)
        theme_combo.pack(side=tk.RIGHT)
        
        # 重試次數
        row3 = ttk.Frame(main_frame)
        row3.pack(fill=tk.X, pady=5)
        ttk.Label(row3, text=self.locale('max_retries')).pack(side=tk.LEFT)
        self.retry_var = tk.StringVar(value=str(self.settings.get('max_retries')))
        retry_spin = ttk.Spinbox(row3, from_=1, to=10, textvariable=self.retry_var, width=10)
        retry_spin.pack(side=tk.RIGHT)
        
        # 自動查詢
        row4 = ttk.Frame(main_frame)
        row4.pack(fill=tk.X, pady=5)
        self.auto_var = tk.BooleanVar(value=self.settings.get('auto_refresh'))
        ttk.Checkbutton(row4, text=self.locale('auto_refresh'), variable=self.auto_var).pack(side=tk.LEFT)
        
        # 間隔
        row5 = ttk.Frame(main_frame)
        row5.pack(fill=tk.X, pady=5)
        ttk.Label(row5, text=self.locale('refresh_interval')).pack(side=tk.LEFT)
        self.interval_var = tk.StringVar(value=str(self.settings.get('refresh_interval')))
        interval_spin = ttk.Spinbox(row5, from_=5, to=120, textvariable=self.interval_var, width=10)
        interval_spin.pack(side=tk.RIGHT)
        
        # 按鈕
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=20)
        ttk.Button(btn_frame, text=self.locale('save'), command=self._save, 
                   style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=self.locale('cancel'), command=self.destroy,
                   style='Secondary.TButton').pack(side=tk.LEFT)
    
    def _save(self):
        self.settings.set('language', self.lang_var.get())
        self.settings.set('theme', self.theme_var.get())
        self.settings.set('max_retries', int(self.retry_var.get()))
        self.settings.set('auto_refresh', self.auto_var.get())
        self.settings.set('refresh_interval', int(self.interval_var.get()))
        
        if self.on_save:
            self.on_save()
        self.destroy()


class PackageQueryApp:
    """全家包裹查詢 GUI 應用程式 - 增強版"""
    
    MAX_TRACKING_NUMBERS = 6
    CONFIG_FILE = "config.yaml"
    
    def __init__(self, root):
        self.root = root
        
        # 管理器初始化
        self.settings = SettingsManager()
        self.locale = LocaleManager(self.settings.get('language'))
        self.theme = ThemeManager(self.settings.get('theme'))
        self.history = HistoryManager()
        
        # 視窗設定
        self.root.title(self.locale('app_title'))
        self._restore_window_state()
        self.root.minsize(700, 600)
        
        # 訊息佇列
        self.message_queue = queue.Queue()
        
        # 狀態
        self.is_querying = False
        self.topmost = False
        self.auto_refresh_job = None
        self.tray_icon = None
        
        # 輸入欄位
        self.entry_fields = []
        
        # 所有結果（用於篩選）
        self.all_results = []
        
        # 套用樣式
        self.style = ttk.Style()
        self.theme.apply_to_root(root, self.style)
        
        # 建立介面
        self._create_widgets()
        
        # 綁定事件
        self._bind_events()
        
        # 載入設定
        self._load_config()
        
        # 開始檢查訊息佇列
        self._check_queue()
        
        # 啟動自動查詢
        if self.settings.get('auto_refresh'):
            self._start_auto_refresh()
        
        # 視窗關閉事件
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
    
    def _restore_window_state(self):
        """還原視窗狀態"""
        w = self.settings.get('window_width', 900)
        h = self.settings.get('window_height', 750)
        x = self.settings.get('window_x')
        y = self.settings.get('window_y')
        
        if x is not None and y is not None:
            self.root.geometry(f'{w}x{h}+{x}+{y}')
        else:
            self.root.geometry(f'{w}x{h}')
    
    def _save_window_state(self):
        """儲存視窗狀態"""
        self.settings.set('window_width', self.root.winfo_width())
        self.settings.set('window_height', self.root.winfo_height())
        self.settings.set('window_x', self.root.winfo_x())
        self.settings.set('window_y', self.root.winfo_y())
    
    def _create_widgets(self):
        """建立介面元件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 標題
        self._create_title(main_frame)
        
        # 輸入區
        self._create_input_section(main_frame)
        
        # 按鈕區
        self._create_button_section(main_frame)
        
        # 頁籤區
        self._create_notebook(main_frame)
        
        # 狀態列
        self._create_status_bar(main_frame)
    
    def _create_title(self, parent):
        """建立標題區"""
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(title_frame, text=self.locale('title_emoji'), 
                  style='Title.TLabel').pack(side=tk.LEFT)
        
        ttk.Label(title_frame, text=f"v{GUI_VERSION}", 
                  style='Status.TLabel').pack(side=tk.RIGHT)
    
    def _create_input_section(self, parent):
        """建立輸入區"""
        input_frame = ttk.LabelFrame(parent, text=f" {self.locale('package_numbers')} ", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 貼上剪貼簿按鈕
        paste_frame = ttk.Frame(input_frame)
        paste_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Button(paste_frame, text=self.locale('paste_clipboard'),
                   command=self._paste_from_clipboard,
                   style='Secondary.TButton').pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(paste_frame, text="📂 載入檔案",
                   command=self._load_file,
                   style='Secondary.TButton').pack(side=tk.LEFT)
        
        ttk.Label(paste_frame, text=self.locale('drag_drop_hint'),
                  style='Status.TLabel').pack(side=tk.RIGHT)
        
        # 輸入欄位 (2 列佈局)
        for row in range(3):
            row_frame = ttk.Frame(input_frame)
            row_frame.pack(fill=tk.X, pady=2)
            
            for col in range(2):
                idx = row * 2 + col
                if idx >= self.MAX_TRACKING_NUMBERS:
                    break
                
                cell_frame = ttk.Frame(row_frame)
                cell_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, 
                               padx=(0, 10) if col == 0 else 0)
                
                ttk.Label(cell_frame, 
                         text=f"{self.locale('package')} {idx+1}:", 
                         width=8).pack(side=tk.LEFT)
                
                entry = ttk.Entry(cell_frame, font=('Consolas', 11), width=20)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                self.entry_fields.append(entry)
    
    def _create_button_section(self, parent):
        """建立按鈕區"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=10)
        
        # 左側按鈕
        left_btns = ttk.Frame(button_frame)
        left_btns.pack(side=tk.LEFT)
        
        self.query_button = ttk.Button(left_btns, text=self.locale('start_query'),
                                        style='Accent.TButton', command=self._start_query)
        self.query_button.pack(side=tk.LEFT, padx=(0, 8))
        
        ttk.Button(left_btns, text=self.locale('clear'),
                   style='Secondary.TButton', command=self._clear_all).pack(side=tk.LEFT, padx=(0, 8))
        
        ttk.Button(left_btns, text=self.locale('copy'),
                   style='Secondary.TButton', command=self._copy_results).pack(side=tk.LEFT, padx=(0, 8))
        
        # 匯出下拉選單
        self.export_btn = ttk.Menubutton(left_btns, text=self.locale('export'),
                                          style='Secondary.TButton')
        export_menu = Menu(self.export_btn, tearoff=0)
        export_menu.add_command(label=self.locale('export_excel'), command=self._export_excel)
        export_menu.add_command(label=self.locale('export_csv'), command=self._export_csv)
        self.export_btn['menu'] = export_menu
        self.export_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        # 右側按鈕
        right_btns = ttk.Frame(button_frame)
        right_btns.pack(side=tk.RIGHT)
        
        self.pin_button = ttk.Button(right_btns, text=self.locale('pin'),
                                      style='Secondary.TButton', command=self._toggle_topmost)
        self.pin_button.pack(side=tk.LEFT, padx=(0, 8))
        
        ttk.Button(right_btns, text=self.locale('settings'),
                   style='Secondary.TButton', command=self._open_settings).pack(side=tk.LEFT)
        
        # 篩選區
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 狀態篩選
        ttk.Label(filter_frame, text="篩選:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_var = tk.StringVar(value='all')
        filter_values = [
            ('all', self.locale('filter_all')),
            ('available', self.locale('filter_available')),
            ('shipping', self.locale('filter_shipping')),
            ('not_found', self.locale('filter_not_found')),
        ]
        for val, text in filter_values:
            ttk.Radiobutton(filter_frame, text=text, value=val, 
                           variable=self.filter_var,
                           command=self._apply_filter).pack(side=tk.LEFT, padx=3)
        
        # 搜尋框
        ttk.Label(filter_frame, text="  |  ").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._apply_filter())
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.insert(0, self.locale('search_placeholder'))
        search_entry.bind('<FocusIn>', lambda e: search_entry.delete(0, tk.END) 
                          if search_entry.get() == self.locale('search_placeholder') else None)
    
    def _create_notebook(self, parent):
        """建立頁籤區"""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 查詢結果頁籤
        result_frame = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(result_frame, text=f" {self.locale('query_results')} ")
        self._create_result_tree(result_frame)
        
        # 歷史記錄頁籤
        history_frame = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(history_frame, text=f" {self.locale('history')} ")
        self._create_history_tree(history_frame)
    
    def _create_result_tree(self, parent):
        """建立結果表格"""
        columns = ('status_icon', 'tracking', 'order', 'status', 'time')
        self.result_tree = ttk.Treeview(parent, columns=columns, show='headings', height=10)
        
        self.result_tree.heading('status_icon', text='')
        self.result_tree.heading('tracking', text=self.locale('tracking_number'))
        self.result_tree.heading('order', text=self.locale('order_number'))
        self.result_tree.heading('status', text=self.locale('status'))
        self.result_tree.heading('time', text=self.locale('query_time'))
        
        self.result_tree.column('status_icon', width=40, anchor='center')
        self.result_tree.column('tracking', width=150, anchor='center')
        self.result_tree.column('order', width=130, anchor='center')
        self.result_tree.column('status', width=250, anchor='w')
        self.result_tree.column('time', width=90, anchor='center')
        
        # 顏色標籤
        self.result_tree.tag_configure('success', foreground=self.theme.get('SUCCESS'))
        self.result_tree.tag_configure('warning', foreground=self.theme.get('WARNING'))
        self.result_tree.tag_configure('error', foreground=self.theme.get('ERROR'))
        
        # 右鍵選單
        self.context_menu = Menu(self.result_tree, tearoff=0)
        self.context_menu.add_command(label=self.locale('context_copy'), command=self._copy_selected)
        self.context_menu.add_command(label=self.locale('context_requery'), command=self._requery_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label=self.locale('context_delete'), command=self._delete_selected)
        
        self.result_tree.bind('<Button-3>', self._show_context_menu)
        self.result_tree.bind('<Double-1>', self._on_double_click)
        
        # 捲軸
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_history_tree(self, parent):
        """建立歷史記錄表格"""
        # 清除按鈕
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(btn_frame, text=self.locale('clear_history'),
                   command=self._clear_history,
                   style='Secondary.TButton').pack(side=tk.RIGHT)
        
        columns = ('timestamp', 'tracking', 'status')
        self.history_tree = ttk.Treeview(parent, columns=columns, show='headings', height=10)
        
        self.history_tree.heading('timestamp', text=self.locale('query_time'))
        self.history_tree.heading('tracking', text=self.locale('tracking_number'))
        self.history_tree.heading('status', text=self.locale('status'))
        
        self.history_tree.column('timestamp', width=150, anchor='center')
        self.history_tree.column('tracking', width=180, anchor='center')
        self.history_tree.column('status', width=300, anchor='w')
        
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 載入歷史
        self._load_history()
    
    def _create_status_bar(self, parent):
        """建立狀態列"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X)
        
        self.status_var = tk.StringVar(value=self.locale('ready'))
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                       style='Status.TLabel', padding=8)
        self.status_label.pack(fill=tk.X)
        
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=300)
        self.progress.pack(fill=tk.X, pady=(5, 0))
        
        # 載入動畫
        self.loading = LoadingAnimation(self.status_label)
    
    def _bind_events(self):
        """綁定事件"""
        self.root.bind('<Return>', lambda e: self._start_query())
        self.root.bind('<Control-v>', self._on_paste)
        self.root.bind('<Control-V>', self._on_paste)
    
    def _load_file(self):
        """載入 TXT 檔案"""
        file_path = filedialog.askopenfilename(
            filetypes=[('Text Files', '*.txt'), ('All Files', '*.*')],
            title='選擇包裹編號檔案'
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f if line.strip()]
                
                for i, line in enumerate(lines[:self.MAX_TRACKING_NUMBERS]):
                    self.entry_fields[i].delete(0, tk.END)
                    self.entry_fields[i].insert(0, line)
                
                self.status_var.set(self.locale('file_loaded', count=min(len(lines), self.MAX_TRACKING_NUMBERS)))
            except Exception as e:
                self.status_var.set(f"載入失敗: {e}")
    
    def _paste_from_clipboard(self):
        """從剪貼簿貼上"""
        try:
            clipboard = self.root.clipboard_get()
            lines = [line.strip() for line in clipboard.split('\n') if line.strip()]
            
            for i, line in enumerate(lines[:self.MAX_TRACKING_NUMBERS]):
                self.entry_fields[i].delete(0, tk.END)
                self.entry_fields[i].insert(0, line)
            
            count = min(len(lines), self.MAX_TRACKING_NUMBERS)
            self.status_var.set(self.locale('pasted', count=count))
        except tk.TclError:
            pass
    
    def _on_paste(self, event):
        """處理 Ctrl+V"""
        try:
            clipboard = self.root.clipboard_get()
            lines = [line.strip() for line in clipboard.split('\n') if line.strip()]
            
            if len(lines) > 1:
                self._paste_from_clipboard()
                return 'break'
        except tk.TclError:
            pass
    
    def _get_status_icon(self, status: str) -> str:
        """取得狀態圖示"""
        status_lower = status.lower() if status else ''
        
        if any(kw in status_lower for kw in ['可取貨', '已取貨', '已領取', '完成', '已送達']):
            return '✅'
        elif any(kw in status_lower for kw in ['配送中', '運送中', '處理中', '已出貨', '到店']):
            return '⏳'
        elif any(kw in status_lower for kw in ['查無', '失敗', '異常', '退貨', '取消']):
            return '❌'
        return '📦'
    
    def _get_status_tag(self, status: str) -> str:
        """取得狀態標籤"""
        status_lower = status.lower() if status else ''
        
        if any(kw in status_lower for kw in ['可取貨', '已取貨', '已領取', '完成', '已送達']):
            return 'success'
        elif any(kw in status_lower for kw in ['查無', '失敗', '異常', '退貨', '取消']):
            return 'error'
        return 'warning'
    
    def _get_status_category(self, status: str) -> str:
        """取得狀態分類"""
        status_lower = status.lower() if status else ''
        
        if any(kw in status_lower for kw in ['可取貨', '已取貨', '已領取', '完成', '已送達']):
            return 'available'
        elif any(kw in status_lower for kw in ['配送中', '運送中', '處理中', '已出貨', '到店']):
            return 'shipping'
        elif any(kw in status_lower for kw in ['查無', '失敗', '異常']):
            return 'not_found'
        return 'shipping'
    
    def _apply_filter(self):
        """套用篩選"""
        # 確保 result_tree 已初始化
        if not hasattr(self, 'result_tree'):
            return
        
        # 清除表格
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        filter_val = self.filter_var.get()
        search_text = self.search_var.get().lower()
        if search_text == self.locale('search_placeholder').lower():
            search_text = ''
        
        for result in self.all_results:
            status = result.get('狀態', '')
            tracking = result.get('包裹編號', '')
            
            # 篩選
            if filter_val != 'all':
                category = self._get_status_category(status)
                if category != filter_val:
                    continue
            
            # 搜尋
            if search_text and search_text not in tracking.lower():
                continue
            
            # 加入表格
            icon = self._get_status_icon(status)
            tag = self._get_status_tag(status)
            self.result_tree.insert('', 'end', values=(
                icon,
                tracking,
                result.get('訂單編號', 'N/A'),
                status,
                result.get('查詢時間', datetime.now().strftime('%H:%M:%S'))
            ), tags=(tag,))
    
    def _show_context_menu(self, event):
        """顯示右鍵選單"""
        item = self.result_tree.identify_row(event.y)
        if item:
            self.result_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _copy_selected(self):
        """複製選中項目"""
        item = self.result_tree.selection()
        if item:
            values = self.result_tree.item(item[0], 'values')
            text = f"包裹編號: {values[1]}\n訂單編號: {values[2]}\n狀態: {values[3]}"
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status_var.set(self.locale('copied_package'))
    
    def _requery_selected(self):
        """重新查詢選中項目"""
        item = self.result_tree.selection()
        if item:
            values = self.result_tree.item(item[0], 'values')
            tracking = values[1]
            
            # 清空並設定
            for entry in self.entry_fields:
                entry.delete(0, tk.END)
            self.entry_fields[0].insert(0, tracking)
            
            self._start_query()
    
    def _delete_selected(self):
        """刪除選中項目"""
        item = self.result_tree.selection()
        if item:
            values = self.result_tree.item(item[0], 'values')
            tracking = values[1]
            
            # 從 all_results 移除
            self.all_results = [r for r in self.all_results if r.get('包裹編號') != tracking]
            self.result_tree.delete(item[0])
    
    def _on_double_click(self, event):
        """雙擊複製"""
        self._copy_selected()
    
    def _get_config_path(self) -> Path:
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent / self.CONFIG_FILE
        return Path(__file__).parent / self.CONFIG_FILE
    
    def _load_config(self):
        """載入設定檔"""
        config_path = self._get_config_path()
        
        if not config_path.exists():
            self.status_var.set(self.locale('config_not_found'))
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            tracking_numbers = config.get('tracking_numbers', [])
            
            for i, entry in enumerate(self.entry_fields):
                if i < len(tracking_numbers):
                    value = tracking_numbers[i]
                    if value and not str(value).startswith('YOUR_'):
                        entry.insert(0, value)
            
            self.status_var.set(self.locale('config_loaded'))
        except Exception as e:
            self.status_var.set(f"{self.locale('config_load_failed')}: {e}")
    
    def _save_config(self):
        """儲存設定檔"""
        config_path = self._get_config_path()
        
        config = {}
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
            except:
                pass
        
        tracking_numbers = self._get_tracking_numbers()
        config['tracking_numbers'] = tracking_numbers if tracking_numbers else ['']
        config['max_retries'] = self.settings.get('max_retries', 5)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            return True
        except Exception as e:
            self.status_var.set(f"{self.locale('config_save_failed')}: {e}")
            return False
    
    def _get_tracking_numbers(self) -> List[str]:
        """取得所有非空的包裹編號"""
        return [entry.get().strip() for entry in self.entry_fields if entry.get().strip()]
    
    def _start_query(self):
        """開始查詢"""
        if self.is_querying:
            messagebox.showwarning("提示", self.locale('query_in_progress'))
            return
        
        tracking_numbers = self._get_tracking_numbers()
        
        if not tracking_numbers:
            messagebox.showwarning("提示", self.locale('enter_tracking'))
            return
        
        self._save_config()
        
        self.is_querying = True
        self.query_button.config(state=tk.DISABLED)
        self.progress.start(10)
        self.loading.start(self.locale('querying'))
        
        # 清除結果
        self.all_results = []
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        thread = threading.Thread(
            target=self._query_worker,
            args=(tracking_numbers,),
            daemon=True
        )
        thread.start()
    
    def _query_worker(self, tracking_numbers: List[str]):
        """查詢工作執行緒"""
        try:
            max_retries = self.settings.get('max_retries', 5)
            query = FamilyMartPackageQuery(max_retries=max_retries)
            
            for i, tracking_no in enumerate(tracking_numbers, 1):
                self.message_queue.put(('status', 
                    self.locale('querying_batch', current=i, total=len(tracking_numbers), number=tracking_no)))
                
                result = None
                for retry in range(3):
                    try:
                        results = query._query_batch([tracking_no])
                        if results:
                            result = results[0]
                            break
                    except Exception as e:
                        if retry < 2:
                            self.message_queue.put(('status',
                                self.locale('retry', retry=retry+2, max=3, number=tracking_no)))
                        else:
                            result = {
                                '包裹編號': tracking_no,
                                '訂單編號': 'N/A',
                                '狀態': f"{self.locale('query_failed')}: {str(e)}"
                            }
                
                if result:
                    self.message_queue.put(('result', result))
                else:
                    self.message_queue.put(('result', {
                        '包裹編號': tracking_no,
                        '訂單編號': 'N/A',
                        '狀態': self.locale('no_result')
                    }))
            
            self.message_queue.put(('status', 
                f"{self.locale('query_complete')} ({datetime.now().strftime('%H:%M:%S')})"))
            
        except Exception as e:
            self.message_queue.put(('error', str(e)))
        
        finally:
            self.message_queue.put(('done', None))
    
    def _check_queue(self):
        """檢查訊息佇列"""
        try:
            while True:
                msg_type, msg_data = self.message_queue.get_nowait()
                
                if msg_type == 'status':
                    self.loading.base_text = msg_data
                elif msg_type == 'result':
                    msg_data['查詢時間'] = datetime.now().strftime('%H:%M:%S')
                    self.all_results.append(msg_data)
                    self._apply_filter()
                    
                    # 加入歷史
                    self.history.add(msg_data.copy())
                    self._load_history()
                    
                elif msg_type == 'error':
                    ErrorDialog(self.root, 
                               self.locale('error_title'),
                               self.locale('error_occurred'),
                               msg_data,
                               self.locale('error_unknown'),
                               self.theme)
                elif msg_type == 'done':
                    self.is_querying = False
                    self.query_button.config(state=tk.NORMAL)
                    self.progress.stop()
                    self.loading.stop()
                    self.status_var.set(self.locale('query_complete'))
                    
        except queue.Empty:
            pass
        
        self.root.after(100, self._check_queue)
    
    def _load_history(self):
        """載入歷史記錄"""
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        for record in reversed(self.history.history[-50:]):
            self.history_tree.insert('', 'end', values=(
                record.get('timestamp', ''),
                record.get('包裹編號', ''),
                record.get('狀態', '')
            ))
    
    def _clear_history(self):
        """清除歷史記錄"""
        self.history.clear()
        self._load_history()
        self.status_var.set(self.locale('history_cleared'))
    
    def _clear_all(self):
        """清除所有內容"""
        for entry in self.entry_fields:
            entry.delete(0, tk.END)
        self.all_results = []
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        self.status_var.set(self.locale('ready'))
        self._save_config()
    
    def _copy_results(self):
        """複製結果"""
        items = self.result_tree.get_children()
        if not items:
            messagebox.showinfo("提示", self.locale('no_results'))
            return
        
        lines = ["包裹編號\t訂單編號\t狀態"]
        for item in items:
            values = self.result_tree.item(item, 'values')
            lines.append(f"{values[1]}\t{values[2]}\t{values[3]}")
        
        self.root.clipboard_clear()
        self.root.clipboard_append('\n'.join(lines))
        self.status_var.set(self.locale('copied'))
    
    def _export_excel(self):
        """匯出 Excel"""
        if not HAS_EXCEL:
            messagebox.showerror("錯誤", "缺少 openpyxl 套件")
            return
        
        if not self.all_results:
            messagebox.showinfo("提示", self.locale('no_results'))
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension='.xlsx',
            filetypes=[('Excel 檔案', '*.xlsx')],
            initialfilename=f"package_query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        
        if file_path:
            try:
                wb = Workbook()
                ws = wb.active
                ws.title = "查詢結果"
                
                ws.append(['包裹編號', '訂單編號', '狀態', '查詢時間'])
                for result in self.all_results:
                    ws.append([
                        result.get('包裹編號', ''),
                        result.get('訂單編號', ''),
                        result.get('狀態', ''),
                        result.get('查詢時間', '')
                    ])
                
                wb.save(file_path)
                self.status_var.set(self.locale('export_success', path=file_path))
            except Exception as e:
                messagebox.showerror("錯誤", self.locale('export_failed', error=str(e)))
    
    def _export_csv(self):
        """匯出 CSV"""
        if not self.all_results:
            messagebox.showinfo("提示", self.locale('no_results'))
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV 檔案', '*.csv')],
            initialfilename=f"package_query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(['包裹編號', '訂單編號', '狀態', '查詢時間'])
                    for result in self.all_results:
                        writer.writerow([
                            result.get('包裹編號', ''),
                            result.get('訂單編號', ''),
                            result.get('狀態', ''),
                            result.get('查詢時間', '')
                        ])
                
                self.status_var.set(self.locale('export_success', path=file_path))
            except Exception as e:
                messagebox.showerror("錯誤", self.locale('export_failed', error=str(e)))
    
    def _toggle_topmost(self):
        """切換置頂"""
        self.topmost = not self.topmost
        self.root.attributes('-topmost', self.topmost)
        
        if self.topmost:
            self.pin_button.config(text=self.locale('unpin'))
            self.status_var.set(self.locale('pinned'))
        else:
            self.pin_button.config(text=self.locale('pin'))
            self.status_var.set(self.locale('unpinned'))
    
    def _open_settings(self):
        """開啟設定對話框"""
        SettingsDialog(self.root, self.settings, self.locale, self.theme, self._apply_settings)
    
    def _apply_settings(self):
        """套用設定"""
        # 重新載入語系
        self.locale.load_locale(self.settings.get('language'))
        
        # 重新套用主題
        self.theme.set_theme(self.settings.get('theme'))
        self.theme.apply_to_root(self.root, self.style)
        
        # 更新自動查詢
        if self.settings.get('auto_refresh'):
            self._start_auto_refresh()
        else:
            self._stop_auto_refresh()
        
        # 需要重啟才能完全套用
        messagebox.showinfo("提示", "部分設定需要重新啟動程式才會完全生效")
    
    def _start_auto_refresh(self):
        """啟動自動查詢"""
        interval_ms = self.settings.get('refresh_interval', 30) * 60 * 1000
        
        def auto_query():
            if self._get_tracking_numbers() and not self.is_querying:
                self._start_query()
            self.auto_refresh_job = self.root.after(interval_ms, auto_query)
        
        self.auto_refresh_job = self.root.after(interval_ms, auto_query)
    
    def _stop_auto_refresh(self):
        """停止自動查詢"""
        if self.auto_refresh_job:
            self.root.after_cancel(self.auto_refresh_job)
            self.auto_refresh_job = None
    
    def _on_close(self):
        """關閉視窗"""
        self._save_window_state()
        self._stop_auto_refresh()
        
        if self.tray_icon:
            self.tray_icon.stop()
        
        self.root.destroy()


def main():
    """主程式"""
    root = tk.Tk()
    
    try:
        root.iconbitmap('icon.ico')
    except:
        pass
    
    app = PackageQueryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
