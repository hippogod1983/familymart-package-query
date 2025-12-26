# -*- coding: utf-8 -*-
"""
全家便利商店包裹查詢 - Windows 視窗化應用程式
現代化深色主題介面
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
from datetime import datetime
from pathlib import Path
import yaml
import sys

# 導入查詢邏輯
from query_package import FamilyMartPackageQuery


class ModernStyle:
    """現代化深色主題樣式"""
    
    # 顏色定義
    BG_DARK = "#1a1a2e"
    BG_SECONDARY = "#16213e"
    BG_CARD = "#0f3460"
    ACCENT = "#00d9ff"
    ACCENT_HOVER = "#00b8d4"
    SUCCESS = "#00e676"
    WARNING = "#ffab00"
    ERROR = "#ff5252"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#b0b0b0"
    BORDER = "#2a3f5f"
    
    @classmethod
    def apply(cls, root):
        """套用樣式到根視窗"""
        style = ttk.Style()
        
        # 設定主題
        style.theme_use('clam')
        
        # 全域背景
        root.configure(bg=cls.BG_DARK)
        
        # Frame 樣式
        style.configure('TFrame', background=cls.BG_DARK)
        style.configure('Card.TFrame', background=cls.BG_CARD)
        
        # LabelFrame 樣式
        style.configure('TLabelframe', background=cls.BG_DARK, foreground=cls.TEXT_PRIMARY)
        style.configure('TLabelframe.Label', 
                       background=cls.BG_DARK, 
                       foreground=cls.ACCENT,
                       font=('Microsoft JhengHei', 10, 'bold'))
        
        # Label 樣式
        style.configure('TLabel', 
                       background=cls.BG_DARK, 
                       foreground=cls.TEXT_PRIMARY,
                       font=('Microsoft JhengHei', 10))
        style.configure('Title.TLabel',
                       background=cls.BG_DARK,
                       foreground=cls.ACCENT,
                       font=('Microsoft JhengHei', 18, 'bold'))
        style.configure('Status.TLabel',
                       background=cls.BG_SECONDARY,
                       foreground=cls.TEXT_SECONDARY,
                       font=('Microsoft JhengHei', 9))
        
        # Entry 樣式
        style.configure('TEntry',
                       fieldbackground=cls.BG_SECONDARY,
                       foreground=cls.TEXT_PRIMARY,
                       insertcolor=cls.ACCENT,
                       bordercolor=cls.BORDER,
                       lightcolor=cls.BORDER,
                       darkcolor=cls.BORDER)
        style.map('TEntry',
                 fieldbackground=[('focus', cls.BG_CARD)],
                 bordercolor=[('focus', cls.ACCENT)])
        
        # Button 樣式
        style.configure('Accent.TButton',
                       background=cls.ACCENT,
                       foreground=cls.BG_DARK,
                       font=('Microsoft JhengHei', 11, 'bold'),
                       padding=(20, 10))
        style.map('Accent.TButton',
                 background=[('active', cls.ACCENT_HOVER), ('pressed', cls.ACCENT_HOVER)])
        
        style.configure('Secondary.TButton',
                       background=cls.BG_CARD,
                       foreground=cls.TEXT_PRIMARY,
                       font=('Microsoft JhengHei', 10),
                       padding=(15, 8))
        style.map('Secondary.TButton',
                 background=[('active', cls.BG_SECONDARY)])
        
        # Treeview 樣式
        style.configure('Treeview',
                       background=cls.BG_SECONDARY,
                       foreground=cls.TEXT_PRIMARY,
                       fieldbackground=cls.BG_SECONDARY,
                       bordercolor=cls.BORDER,
                       font=('Microsoft JhengHei', 10),
                       rowheight=30)
        style.configure('Treeview.Heading',
                       background=cls.BG_CARD,
                       foreground=cls.ACCENT,
                       font=('Microsoft JhengHei', 10, 'bold'))
        style.map('Treeview',
                 background=[('selected', cls.BG_CARD)],
                 foreground=[('selected', cls.ACCENT)])
        
        # Progressbar 樣式
        style.configure('TProgressbar',
                       background=cls.ACCENT,
                       troughcolor=cls.BG_SECONDARY,
                       bordercolor=cls.BORDER,
                       lightcolor=cls.ACCENT,
                       darkcolor=cls.ACCENT)
        
        return style


class PackageQueryApp:
    """全家包裹查詢 GUI 應用程式"""
    
    MAX_TRACKING_NUMBERS = 6
    CONFIG_FILE = "config.yaml"
    MAX_RETRY = 3
    
    def __init__(self, root):
        self.root = root
        self.root.title("全家便利商店包裹查詢")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        self.root.minsize(650, 550)
        
        # 訊息佇列
        self.message_queue = queue.Queue()
        
        # 查詢狀態
        self.is_querying = False
        
        # 輸入欄位列表
        self.entry_fields = []
        
        # 視窗置頂狀態
        self.topmost = False
        
        # 套用樣式
        self.style = ModernStyle.apply(root)
        
        # 建立介面
        self._create_widgets()
        
        # 綁定快捷鍵
        self._bind_shortcuts()
        
        # 從設定檔載入
        self._load_config()
        
        # 開始檢查訊息佇列
        self._check_queue()
    
    def _create_widgets(self):
        """建立介面元件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 標題
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(
            title_frame, 
            text="📦 全家便利商店包裹查詢",
            style='Title.TLabel'
        )
        title_label.pack()
        
        # 輸入區
        input_frame = ttk.LabelFrame(main_frame, text=" 包裹編號 ", padding="15")
        input_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 建立輸入欄位（2 列佈局）
        for row in range(3):
            row_frame = ttk.Frame(input_frame)
            row_frame.pack(fill=tk.X, pady=3)
            
            for col in range(2):
                idx = row * 2 + col
                if idx >= self.MAX_TRACKING_NUMBERS:
                    break
                    
                cell_frame = ttk.Frame(row_frame)
                cell_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10) if col == 0 else 0)
                
                label = ttk.Label(cell_frame, text=f"包裹 {idx+1}:", width=7)
                label.pack(side=tk.LEFT, padx=(0, 5))
                
                entry = ttk.Entry(cell_frame, font=('Consolas', 11), width=20)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                self.entry_fields.append(entry)
        
        # 按鈕區
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=15)
        
        self.query_button = ttk.Button(
            button_frame,
            text="🔍 開始查詢",
            style='Accent.TButton',
            command=self._start_query
        )
        self.query_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = ttk.Button(
            button_frame,
            text="🗑️ 清除",
            style='Secondary.TButton',
            command=self._clear_all
        )
        self.clear_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.copy_button = ttk.Button(
            button_frame,
            text="📋 複製",
            style='Secondary.TButton',
            command=self._copy_results
        )
        self.copy_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 視窗置頂按鈕
        self.topmost_button = ttk.Button(
            button_frame,
            text="📌 置頂",
            style='Secondary.TButton',
            command=self._toggle_topmost
        )
        self.topmost_button.pack(side=tk.LEFT)
        
        # 結果區
        result_frame = ttk.LabelFrame(main_frame, text=" 查詢結果 ", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 建立 Treeview 表格
        columns = ('tracking', 'order', 'status', 'time')
        self.result_tree = ttk.Treeview(
            result_frame, 
            columns=columns, 
            show='headings',
            height=8
        )
        
        # 設定欄位
        self.result_tree.heading('tracking', text='包裹編號')
        self.result_tree.heading('order', text='訂單編號')
        self.result_tree.heading('status', text='狀態')
        self.result_tree.heading('time', text='查詢時間')
        
        self.result_tree.column('tracking', width=150, anchor='center')
        self.result_tree.column('order', width=130, anchor='center')
        self.result_tree.column('status', width=220, anchor='w')
        self.result_tree.column('time', width=90, anchor='center')
        
        # 雙擊複製
        self.result_tree.bind('<Double-1>', self._on_double_click)
        
        # 捲軸
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 狀態與進度條
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X)
        
        self.status_var = tk.StringVar(value="就緒")
        status_bar = ttk.Label(
            bottom_frame,
            textvariable=self.status_var,
            style='Status.TLabel',
            padding=8
        )
        status_bar.pack(fill=tk.X)
        
        self.progress = ttk.Progressbar(
            bottom_frame,
            mode='indeterminate',
            length=300
        )
        self.progress.pack(fill=tk.X, pady=(5, 0))
        
        # 定義狀態 Tag 顏色
        self.result_tree.tag_configure('success', foreground=ModernStyle.SUCCESS)
        self.result_tree.tag_configure('warning', foreground=ModernStyle.WARNING)
        self.result_tree.tag_configure('error', foreground=ModernStyle.ERROR)
    
    def _get_status_tag(self, status_text):
        """根據狀態文字取得對應的 Tag"""
        status_text = status_text.lower() if status_text else ''
        
        success_keywords = ['可取貨', '已取貨', '已送達', '已領取', '完成']
        warning_keywords = ['配送中', '運送中', '處理中', '已出貨', '到店']
        error_keywords = ['查無', '失敗', '異常', '退貨', '取消']
        
        for keyword in success_keywords:
            if keyword in status_text:
                return 'success'
        
        for keyword in warning_keywords:
            if keyword in status_text:
                return 'warning'
                
        for keyword in error_keywords:
            if keyword in status_text:
                return 'error'
        
        return 'warning'  # 預設黃色
    
    def _get_config_path(self):
        """取得設定檔路徑"""
        if getattr(sys, 'frozen', False):
            app_dir = Path(sys.executable).parent
        else:
            app_dir = Path(__file__).parent
        return app_dir / self.CONFIG_FILE
    
    def _load_config(self):
        """從設定檔載入包裹編號"""
        config_path = self._get_config_path()
        
        if not config_path.exists():
            self.status_var.set("設定檔不存在，將建立新設定檔")
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            tracking_numbers = config.get('tracking_numbers', [])
            
            for i, entry in enumerate(self.entry_fields):
                if i < len(tracking_numbers):
                    value = tracking_numbers[i]
                    if value and not value.startswith('YOUR_'):
                        entry.insert(0, value)
            
            self.status_var.set("已從設定檔載入包裹編號")
            
        except Exception as e:
            self.status_var.set(f"載入設定檔失敗: {e}")
    
    def _save_config(self):
        """將包裹編號保存到設定檔"""
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
        
        if 'max_retries' not in config:
            config['max_retries'] = 5
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            return True
        except Exception as e:
            self.status_var.set(f"保存設定檔失敗: {e}")
            return False
    
    def _get_tracking_numbers(self):
        """取得所有非空的包裹編號"""
        numbers = []
        for entry in self.entry_fields:
            value = entry.get().strip()
            if value:
                numbers.append(value)
        return numbers
    
    def _start_query(self):
        """開始查詢"""
        if self.is_querying:
            messagebox.showwarning("提示", "查詢進行中，請稍候...")
            return
        
        tracking_numbers = self._get_tracking_numbers()
        
        if not tracking_numbers:
            messagebox.showwarning("提示", "請輸入至少一個包裹編號")
            return
        
        self._save_config()
        
        self.is_querying = True
        self.query_button.config(state=tk.DISABLED)
        self.progress.start(10)
        
        # 清除表格
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        self.status_var.set(f"開始查詢 {len(tracking_numbers)} 個包裹...")
        
        thread = threading.Thread(
            target=self._query_worker,
            args=(tracking_numbers,),
            daemon=True
        )
        thread.start()
    
    def _query_worker(self, tracking_numbers):
        """查詢工作執行緒"""
        try:
            query = FamilyMartPackageQuery(max_retries=5)
            
            for i, tracking_no in enumerate(tracking_numbers, 1):
                self.message_queue.put(('status', f"正在查詢 {i}/{len(tracking_numbers)}: {tracking_no}"))
                
                # 重試機制
                result = None
                for retry in range(self.MAX_RETRY):
                    try:
                        results = query._query_batch([tracking_no])
                        if results:
                            result = results[0]
                            break
                    except Exception as e:
                        if retry < self.MAX_RETRY - 1:
                            self.message_queue.put(('status', f"重試 {retry+2}/{self.MAX_RETRY}: {tracking_no}"))
                        else:
                            result = {
                                '包裹編號': tracking_no,
                                '訂單編號': 'N/A',
                                '狀態': f'❌ 查詢失敗: {str(e)}'
                            }
                
                if result:
                    self.message_queue.put(('result', result))
                else:
                    self.message_queue.put(('result', {
                        '包裹編號': tracking_no,
                        '訂單編號': 'N/A',
                        '狀態': '⚠️ 查無結果或驗證碼辨識失敗'
                    }))
            
            self.message_queue.put(('status', f"查詢完成！({datetime.now().strftime('%H:%M:%S')})"))
            
        except Exception as e:
            self.message_queue.put(('status', f"❌ 發生錯誤: {str(e)}"))
        
        finally:
            self.message_queue.put(('done', None))
    
    def _check_queue(self):
        """檢查訊息佇列"""
        try:
            while True:
                msg_type, msg_data = self.message_queue.get_nowait()
                
                if msg_type == 'status':
                    self.status_var.set(msg_data)
                elif msg_type == 'result':
                    tag = self._get_status_tag(msg_data.get('狀態', ''))
                    self.result_tree.insert('', 'end', values=(
                        msg_data.get('包裹編號', 'N/A'),
                        msg_data.get('訂單編號', 'N/A'),
                        msg_data.get('狀態', 'N/A'),
                        datetime.now().strftime('%H:%M:%S')
                    ), tags=(tag,))
                elif msg_type == 'done':
                    self.is_querying = False
                    self.query_button.config(state=tk.NORMAL)
                    self.progress.stop()
                    
        except queue.Empty:
            pass
        
        self.root.after(100, self._check_queue)
    
    def _clear_all(self):
        """清除所有內容"""
        for entry in self.entry_fields:
            entry.delete(0, tk.END)
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        self.status_var.set("就緒")
        self._save_config()
    
    def _copy_results(self):
        """複製結果到剪貼簿"""
        items = self.result_tree.get_children()
        if not items:
            messagebox.showinfo("提示", "沒有可複製的結果")
            return
        
        lines = ["包裹編號\t訂單編號\t狀態"]
        for item in items:
            values = self.result_tree.item(item, 'values')
            lines.append(f"{values[0]}\t{values[1]}\t{values[2]}")
        
        self.root.clipboard_clear()
        self.root.clipboard_append('\n'.join(lines))
        self.status_var.set("結果已複製到剪貼簿")
    
    def _bind_shortcuts(self):
        """綁定快捷鍵"""
        self.root.bind('<Return>', lambda e: self._start_query())
        self.root.bind('<Control-v>', self._on_paste)
        self.root.bind('<Control-V>', self._on_paste)
    
    def _on_paste(self, event):
        """處理 Ctrl+V 貼上多個編號"""
        try:
            clipboard = self.root.clipboard_get()
            lines = [line.strip() for line in clipboard.split('\n') if line.strip()]
            
            if len(lines) > 1:
                # 多行貼上：填入各個欄位
                for i, line in enumerate(lines):
                    if i < len(self.entry_fields):
                        self.entry_fields[i].delete(0, tk.END)
                        self.entry_fields[i].insert(0, line)
                self.status_var.set(f"已貼上 {min(len(lines), len(self.entry_fields))} 個包裹編號")
                return 'break'
        except:
            pass
    
    def _on_double_click(self, event):
        """雙擊表格列複製"""
        item = self.result_tree.selection()
        if item:
            values = self.result_tree.item(item[0], 'values')
            text = f"包裹編號: {values[0]}\n訂單編號: {values[1]}\n狀態: {values[2]}"
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status_var.set(f"已複製包裹 {values[0]} 的資訊")
    
    def _toggle_topmost(self):
        """切換視窗置頂"""
        self.topmost = not self.topmost
        self.root.attributes('-topmost', self.topmost)
        if self.topmost:
            self.topmost_button.configure(text="📌 取消置頂")
            self.status_var.set("視窗已置頂")
        else:
            self.topmost_button.configure(text="📌 置頂")
            self.status_var.set("已取消置頂")


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
