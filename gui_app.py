# -*- coding: utf-8 -*-
"""
全家便利商店包裹查詢 - Windows 視窗化應用程式
使用 tkinter 建立圖形使用者介面
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import queue
from datetime import datetime

# 導入查詢邏輯
from query_package import FamilyMartPackageQuery


class PackageQueryApp:
    """全家包裹查詢 GUI 應用程式"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("全家便利商店包裹查詢")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # 設定最小視窗大小
        self.root.minsize(500, 400)
        
        # 訊息佇列（用於執行緒間通訊）
        self.message_queue = queue.Queue()
        
        # 查詢狀態
        self.is_querying = False
        
        # 設定樣式
        self._setup_styles()
        
        # 建立介面
        self._create_widgets()
        
        # 開始檢查訊息佇列
        self._check_queue()
    
    def _setup_styles(self):
        """設定 ttk 樣式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 自訂按鈕樣式
        style.configure('Query.TButton', 
                       font=('Microsoft JhengHei', 12, 'bold'),
                       padding=10)
        style.configure('Clear.TButton',
                       font=('Microsoft JhengHei', 10),
                       padding=5)
        
        # 自訂標籤樣式
        style.configure('Title.TLabel',
                       font=('Microsoft JhengHei', 16, 'bold'))
        style.configure('Status.TLabel',
                       font=('Microsoft JhengHei', 10))
    
    def _create_widgets(self):
        """建立介面元件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 標題
        title_label = ttk.Label(main_frame, 
                               text="📦 全家便利商店包裹查詢",
                               style='Title.TLabel')
        title_label.pack(pady=(0, 15))
        
        # 輸入區框架
        input_frame = ttk.LabelFrame(main_frame, text="包裹編號（每行一個）", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 輸入文字框
        self.input_text = scrolledtext.ScrolledText(
            input_frame, 
            height=5, 
            font=('Consolas', 11),
            wrap=tk.WORD
        )
        self.input_text.pack(fill=tk.X, expand=True)
        
        # 按鈕框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # 查詢按鈕
        self.query_button = ttk.Button(
            button_frame,
            text="🔍 開始查詢",
            style='Query.TButton',
            command=self._start_query
        )
        self.query_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 清除按鈕
        self.clear_button = ttk.Button(
            button_frame,
            text="🗑️ 清除",
            style='Clear.TButton',
            command=self._clear_all
        )
        self.clear_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 複製結果按鈕
        self.copy_button = ttk.Button(
            button_frame,
            text="📋 複製結果",
            style='Clear.TButton',
            command=self._copy_results
        )
        self.copy_button.pack(side=tk.LEFT)
        
        # 結果區框架
        result_frame = ttk.LabelFrame(main_frame, text="查詢結果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 結果文字框
        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            height=15,
            font=('Microsoft JhengHei', 10),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # 狀態列
        self.status_var = tk.StringVar(value="就緒")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            style='Status.TLabel',
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=5
        )
        status_bar.pack(fill=tk.X)
        
        # 進度條
        self.progress = ttk.Progressbar(
            main_frame,
            mode='indeterminate'
        )
        self.progress.pack(fill=tk.X, pady=(5, 0))
    
    def _start_query(self):
        """開始查詢"""
        if self.is_querying:
            messagebox.showwarning("提示", "查詢進行中，請稍候...")
            return
        
        # 取得包裹編號
        input_text = self.input_text.get("1.0", tk.END).strip()
        if not input_text:
            messagebox.showwarning("提示", "請輸入至少一個包裹編號")
            return
        
        # 解析包裹編號
        tracking_numbers = [
            line.strip() 
            for line in input_text.split('\n') 
            if line.strip()
        ]
        
        if not tracking_numbers:
            messagebox.showwarning("提示", "請輸入有效的包裹編號")
            return
        
        # 開始查詢
        self.is_querying = True
        self.query_button.config(state=tk.DISABLED)
        self.progress.start(10)
        
        # 清除之前的結果
        self._append_result("", clear=True)
        self._append_result(f"開始查詢 {len(tracking_numbers)} 個包裹...\n")
        self._append_result(f"查詢時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self._append_result("-" * 50 + "\n")
        
        # 在背景執行緒執行查詢
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
                self.message_queue.put(('status', f"正在查詢第 {i}/{len(tracking_numbers)} 個包裹: {tracking_no}"))
                self.message_queue.put(('result', f"\n🔍 查詢包裹: {tracking_no}\n"))
                
                try:
                    results = query._query_batch([tracking_no])
                    
                    if results:
                        for result in results:
                            self.message_queue.put(('result', f"  ✅ 包裹編號: {result.get('包裹編號', 'N/A')}\n"))
                            self.message_queue.put(('result', f"     訂單編號: {result.get('訂單編號', 'N/A')}\n"))
                            self.message_queue.put(('result', f"     狀態: {result.get('狀態', 'N/A')}\n"))
                    else:
                        self.message_queue.put(('result', f"  ⚠️ 查無結果或驗證碼辨識失敗\n"))
                        
                except Exception as e:
                    self.message_queue.put(('result', f"  ❌ 查詢失敗: {str(e)}\n"))
            
            self.message_queue.put(('result', "\n" + "=" * 50 + "\n"))
            self.message_queue.put(('result', "查詢完成！\n"))
            self.message_queue.put(('status', "查詢完成"))
            
        except Exception as e:
            self.message_queue.put(('result', f"\n❌ 發生錯誤: {str(e)}\n"))
            self.message_queue.put(('status', f"錯誤: {str(e)}"))
        
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
                    self._append_result(msg_data)
                elif msg_type == 'done':
                    self.is_querying = False
                    self.query_button.config(state=tk.NORMAL)
                    self.progress.stop()
                    
        except queue.Empty:
            pass
        
        # 每 100ms 檢查一次
        self.root.after(100, self._check_queue)
    
    def _append_result(self, text, clear=False):
        """附加文字到結果區"""
        self.result_text.config(state=tk.NORMAL)
        if clear:
            self.result_text.delete("1.0", tk.END)
        if text:
            self.result_text.insert(tk.END, text)
            self.result_text.see(tk.END)
        self.result_text.config(state=tk.DISABLED)
    
    def _clear_all(self):
        """清除所有內容"""
        self.input_text.delete("1.0", tk.END)
        self._append_result("", clear=True)
        self.status_var.set("就緒")
    
    def _copy_results(self):
        """複製結果到剪貼簿"""
        result = self.result_text.get("1.0", tk.END).strip()
        if result:
            self.root.clipboard_clear()
            self.root.clipboard_append(result)
            self.status_var.set("結果已複製到剪貼簿")
        else:
            messagebox.showinfo("提示", "沒有可複製的結果")


def main():
    """主程式"""
    root = tk.Tk()
    
    # 設定視窗圖示（如果有的話）
    try:
        root.iconbitmap('icon.ico')
    except:
        pass
    
    app = PackageQueryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
