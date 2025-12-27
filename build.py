#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全家包裹查詢 - EXE 編譯腳本
使用 PyInstaller + UPX 壓縮
"""

import subprocess
import sys
import shutil
from pathlib import Path


def check_dependencies():
    """檢查必要的編譯工具"""
    # 檢查 PyInstaller
    try:
        import PyInstaller
        print(f"✅ PyInstaller 已安裝: {PyInstaller.__version__}")
    except ImportError:
        print("❌ 缺少 PyInstaller，正在安裝...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
    
    # 檢查 UPX (可選)
    upx_path = shutil.which('upx')
    if upx_path:
        print(f"✅ UPX 已安裝: {upx_path}")
        return True
    else:
        print("⚠️ UPX 未安裝 (可選，用於壓縮 EXE)")
        print("   下載: https://github.com/upx/upx/releases")
        return False


def build():
    """編譯 EXE"""
    print("\n📦 開始編譯 (瘦身版)...")
    
    has_upx = check_dependencies()
    
    # 不需要的大型模組（明確排除以減少 EXE 大小）
    exclude_modules = [
        # 測試和開發工具
        'pytest', 'unittest', 'doctest',
        # 不需要的科學計算
        'matplotlib', 'scipy', 'pandas',
        # 不需要的 ML 框架
        'tensorflow', 'keras', 'torch', 'torchvision',
        # 不需要的網頁框架
        'flask', 'django', 'fastapi',
        # 不需要的 GUI 框架
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'wx',
        # 不需要的圖片處理
        'IPython', 'notebook', 'jupyter',
        # 其他
        'cryptography', 'paramiko', 'fabric',
    ]
    
    # PyInstaller 參數
    args = [
        sys.executable,
        '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--name=全家包裹查詢',
        '--add-data=locales;locales',
        '--add-data=config.yaml.example;.',
        # 關鍵：加入 ddddocr 的模型檔案
        '--collect-data=ddddocr',
        '--collect-data=onnxruntime',
        '--hidden-import=ddddocr',
        '--hidden-import=onnxruntime',
        '--clean',
        '--noconfirm',
    ]
    
    # 加入排除模組
    for mod in exclude_modules:
        args.append(f'--exclude-module={mod}')
    
    # 如果有 UPX，使用壓縮
    if has_upx:
        args.extend(['--upx-dir=.', '--upx-exclude=python*.dll'])
        print("📦 將使用 UPX 壓縮")
    
    # 如果有圖示
    icon_path = Path('icon.ico')
    if icon_path.exists():
        args.append(f'--icon={icon_path}')
    
    # 主程式
    args.append('gui_app.py')
    
    print(f"執行: {' '.join(args[:15])}...")  # 只顯示前 15 個參數
    
    result = subprocess.run(args)
    
    if result.returncode == 0:
        print("\n✅ 編譯成功！")
        print(f"   輸出: dist/全家包裹查詢.exe")
        
        # 顯示檔案大小
        exe_path = Path('dist/全家包裹查詢.exe')
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"   大小: {size_mb:.1f} MB")
    else:
        print("\n❌ 編譯失敗")
        return False
    
    return True


def clean():
    """清除編譯產生的檔案"""
    dirs_to_clean = ['build', '__pycache__']
    files_to_clean = ['*.spec']
    
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"🗑️ 已刪除: {dir_name}")
    
    for pattern in files_to_clean:
        for file in Path('.').glob(pattern):
            file.unlink()
            print(f"🗑️ 已刪除: {file}")
    
    print("✅ 清除完成")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='全家包裹查詢 EXE 編譯腳本')
    parser.add_argument('-c', '--clean', action='store_true', help='清除編譯產生的檔案')
    parser.add_argument('-b', '--build', action='store_true', help='編譯 EXE')
    
    args = parser.parse_args()
    
    if args.clean:
        clean()
    elif args.build:
        build()
    else:
        # 預設編譯
        build()
