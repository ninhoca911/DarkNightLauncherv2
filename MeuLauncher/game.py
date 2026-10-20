"""Instalação de versões / loaders e arranque do Minecraft."""
import subprocess
import sys

import minecraft_launcher_lib as mll

from config import MC_DIR

LOADERS = ["Vanilla", "Fabric", "Forge"]


def list_versions(include_snapshots=False):
    versions = mll.utils.get_version_list()
    return [v["id"] for v in versions if include_snapshots or v["type"] == "release"]


def _find_installed(version, loader):
    ids = [v["id"] for v in mll.utils.get_installed_versions(str(MC_DIR))]
    if loader == "Fabric":
        match = [i for i in ids if i.startswith("fabric-loader-") and i.endswith("-" + version)]
    elif loader == "Forge":
        match = [i for i in ids if "forge" in i.lower() and i.startswith(version)]
    else:
        match = [i for i in ids if i == version]
    return match[-1] if match else None


def install(version, loader, callback):
    """Instala a versão (e o loader) se ainda não existir. Devolve o id a lançar."""
    mc = str(MC_DIR)
    existing = _find_installed(version, loader)
    if existing:
        return existing

    if loader == "Vanilla":
        mll.install.install_minecraft_version(version, mc, callback=callback)
    elif loader == "Fabric":
        if not mll.fabric.is_minecraft_version_supported(version):
            raise RuntimeError(f"O Fabric não suporta a versão {version}.")
        mll.fabric.install_fabric(version, mc, callback=callback)
    elif loader == "Forge":
        forge_version = mll.forge.find_forge_version(version)
        if not forge_version:
            raise RuntimeError(f"Não existe Forge para a versão {version}.")
        mll.forge.install_forge_version(forge_version, mc, callback=callback)
    else:
        raise RuntimeError(f"Loader desconhecido: {loader}")

    installed = _find_installed(version, loader)
    if not installed:
        raise RuntimeError("A instalação terminou mas a versão não foi encontrada.")
    return installed


def _java_path(version_id):
    """Java que a Mojang instala com o jogo (assim o utilizador não precisa de instalar Java)."""
    try:
        import json
        vdir = MC_DIR / "versions"
        vid = version_id
        for _ in range(5):  # segue "inheritsFrom" (Fabric/Forge)
            data = json.loads((vdir / vid / f"{vid}.json").read_text(encoding="utf-8"))
            component = (data.get("javaVersion") or {}).get("component")
            if component:
                return mll.runtime.get_executable_path(component, str(MC_DIR))
            if not data.get("inheritsFrom"):
                break
            vid = data["inheritsFrom"]
    except Exception:
        pass
    return None


def launch(version_id, account, ram_mb):
    options = {
        "username": account["name"],
        "uuid": account["id"],
        "token": account["access_token"],
        "gameDirectory": str(MC_DIR),
        "jvmArguments": [f"-Xmx{ram_mb}M", "-Xms512M"],
    }
    java = _java_path(version_id)
    if java:
        options["executablePath"] = java
    command = mll.command.get_minecraft_command(version_id, str(MC_DIR), options)
    flags = 0x08000000 if sys.platform == "win32" else 0  # sem janela de consola
    return subprocess.Popen(command, cwd=str(MC_DIR), creationflags=flags)
