"""Cria um ícone no ambiente de trabalho que abre o launcher com um clique.

Uso:  python criar_atalho.py
Se existir assets/logo.png (ou assets/icon.png), é usado como ícone.
"""
import subprocess
import sys
from pathlib import Path

import config

BASE = Path(__file__).resolve().parent
NAME = config.APP_NAME


def make_icon():
    """Converte o PNG do logo para .ico (Windows). Devolve o caminho ou None."""
    for candidate in ("icon.png", "logo.png"):
        png = BASE / "assets" / candidate
        if png.exists():
            try:
                from PIL import Image
                ico = BASE / "assets" / "icon.ico"
                Image.open(png).convert("RGBA").save(
                    ico, sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
                return ico
            except Exception as exc:  # noqa: BLE001
                print("Aviso: não consegui criar o .ico:", exc)
    return None


def desktop_dir():
    home = Path.home()
    for name in ("Desktop", "Ambiente de Trabalho", "Área de Trabalho"):
        if (home / name).exists():
            return home / name
    return home / "Desktop"


def windows():
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    target = pythonw if pythonw.exists() else Path(sys.executable)
    icon = make_icon()
    shortcut = desktop_dir() / f"{NAME}.lnk"
    script = (
        "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}');"
        "$s.TargetPath='{target}';"
        "$s.Arguments='\"{main}\"';"
        "$s.WorkingDirectory='{wd}';"
        "{icon}"
        "$s.Save()"
    ).format(
        lnk=shortcut, target=target, main=BASE / "launcher.py", wd=BASE,
        icon=f"$s.IconLocation='{icon}';" if icon else "",
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", script], check=True)
    print("Atalho criado em:", shortcut)


def linux():
    icon = BASE / "assets" / "icon.png"
    if not icon.exists():
        icon = BASE / "assets" / "logo.png"
    entry = desktop_dir() / f"{NAME}.desktop"
    entry.parent.mkdir(parents=True, exist_ok=True)
    entry.write_text(
        "[Desktop Entry]\nType=Application\n"
        f"Name={NAME}\nExec={sys.executable} {BASE / 'launcher.py'}\n"
        f"Path={BASE}\nIcon={icon if icon.exists() else 'applications-games'}\nTerminal=false\n",
        encoding="utf-8",
    )
    entry.chmod(0o755)
    print("Atalho criado em:", entry)


if __name__ == "__main__":
    if sys.platform == "win32":
        windows()
    elif sys.platform.startswith("linux"):
        linux()
    else:
        print("No macOS, usa o PyInstaller (ver LEIAME.md) para criar uma .app.")
