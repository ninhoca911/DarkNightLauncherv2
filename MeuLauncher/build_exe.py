"""Compila o launcher num único .exe (Windows) com o PyInstaller.

Uso local:  python build_exe.py
O resultado fica em dist/<APP_NAME>.exe
"""
import os
import subprocess
import sys
from pathlib import Path

import config

BASE = Path(__file__).resolve().parent
ASSETS = BASE / "assets"


def make_ico():
    for name in ("icon.png", "logo.png"):
        png = ASSETS / name
        if png.exists():
            from PIL import Image
            ico = ASSETS / "icon.ico"
            Image.open(png).convert("RGBA").save(
                ico, sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
            return ico
    return None


def main():
    ASSETS.mkdir(exist_ok=True)
    cmd = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
        "--onefile", "--windowed",
        "--name", config.APP_NAME,
        "--add-data", f"{ASSETS}{os.pathsep}assets",
    ]
    ico = make_ico()
    if ico:
        cmd += ["--icon", str(ico)]
    cmd.append(str(BASE / "launcher.py"))
    subprocess.run(cmd, check=True, cwd=BASE)
    print(f"\nPronto: dist/{config.APP_NAME}.exe")


if __name__ == "__main__":
    main()
