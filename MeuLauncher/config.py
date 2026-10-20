"""Configuração central do launcher. Muda aqui o nome, o client id, etc."""
import json
from pathlib import Path

APP_NAME = "MeuLauncher"

# ID da tua app registada no Azure (ver LEIAME.md, secção "Login Microsoft").
CLIENT_ID = "COLOCA-AQUI-O-TEU-AZURE-CLIENT-ID"

# Só contas pessoais Microsoft (as que têm Minecraft).
AUTHORITY = "https://login.microsoftonline.com/consumers"
SCOPES = ["XboxLive.signin"]  # o MSAL junta o offline_access sozinho

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"

ROOT = Path.home() / f".{APP_NAME.lower()}"
MC_DIR = ROOT / "minecraft"
MODS_DIR = MC_DIR / "mods"
CAPES_DIR = ROOT / "capes"
CONFIG_FILE = ROOT / "config.json"
CACHE_FILE = ROOT / "msal_cache.json"
SKIN_FILE = ROOT / "skin.png"

DEFAULTS = {
    "ram": 4096,
    "version": "",
    "loader": "Vanilla",
    "snapshots": False,
}


def resource(*parts):
    """Caminho para ficheiros incluídos (funciona também dentro do .exe do PyInstaller)."""
    import sys
    base = Path(getattr(sys, "_MEIPASS", BASE_DIR))
    return base.joinpath(*parts)


def ensure_dirs():
    for d in (ROOT, MC_DIR, MODS_DIR, CAPES_DIR):
        d.mkdir(parents=True, exist_ok=True)


def load():
    ensure_dirs()
    cfg = dict(DEFAULTS)
    try:
        cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
    except Exception:
        pass
    return cfg


def save(cfg):
    ensure_dirs()
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
