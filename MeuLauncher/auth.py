"""Login Microsoft pelo browser (MSAL) + cadeia Xbox Live -> Minecraft.

O MSAL abre o browser predefinido do sistema, o utilizador faz login lá e o
resultado volta ao launcher por um endereço local (http://localhost). Os tokens
ficam em cache no disco, por isso o login só é pedido uma vez.
"""
import msal
import requests

import config

TIMEOUT = 20


class AuthError(Exception):
    """Erro de login com mensagem pronta a mostrar ao utilizador."""


# ---------- MSAL ----------
def _app():
    config.ensure_dirs()
    cache = msal.SerializableTokenCache()
    if config.CACHE_FILE.exists():
        try:
            cache.deserialize(config.CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    app = msal.PublicClientApplication(
        config.CLIENT_ID, authority=config.AUTHORITY, token_cache=cache)
    return app, cache


def _save(cache):
    if cache.has_state_changed:
        config.CACHE_FILE.write_text(cache.serialize(), encoding="utf-8")


_SUCCESS_PAGE = (
    "<html><body style='font-family:Segoe UI,sans-serif;background:#1b0a38;color:#fff;"
    "text-align:center;padding-top:20vh'><h1>Login concluído</h1>"
    "<p>Já podes fechar esta janela e voltar ao launcher.</p></body></html>")
_ERROR_PAGE = (
    "<html><body style='font-family:Segoe UI,sans-serif;background:#1b0a38;color:#fff;"
    "text-align:center;padding-top:20vh'><h1>O login falhou</h1>"
    "<p>{description}</p></body></html>")


def _ms_token(interactive):
    app, cache = _app()
    result = None
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(config.SCOPES, account=accounts[0])
    if (not result or "access_token" not in result) and interactive:
        result = app.acquire_token_interactive(
            config.SCOPES,
            prompt="select_account",
            timeout=300,
            success_template=_SUCCESS_PAGE,
            error_template=_ERROR_PAGE,
        )
    _save(cache)
    if not result or "access_token" not in result:
        if interactive:
            detail = (result or {}).get("error_description") or "Login cancelado ou sem resposta."
            raise AuthError(detail.splitlines()[0])
        return None
    return result["access_token"]


# ---------- Xbox Live / Minecraft ----------
_XSTS_ERRORS = {
    2148916233: "Esta conta Microsoft não tem conta Xbox. Entra em minecraft.net uma vez para a criar.",
    2148916235: "O Xbox Live não está disponível no teu país.",
    2148916236: "Esta conta precisa de verificação de adulto (Xbox).",
    2148916237: "Esta conta precisa de verificação de adulto (Xbox).",
    2148916238: "Conta de menor: tem de ser adicionada a uma família Microsoft.",
}


def _post(url, payload, what):
    try:
        r = requests.post(url, json=payload, timeout=TIMEOUT,
                          headers={"Accept": "application/json"})
    except requests.RequestException as exc:
        raise AuthError(f"Sem ligação ({what}): {exc}") from exc
    return r


def _minecraft_login(ms_token):
    r = _post("https://user.auth.xboxlive.com/user/authenticate", {
        "Properties": {"AuthMethod": "RPS", "SiteName": "user.auth.xboxlive.com",
                       "RpsTicket": f"d={ms_token}"},
        "RelyingParty": "http://auth.xboxlive.com", "TokenType": "JWT"}, "Xbox Live")
    if r.status_code != 200:
        raise AuthError(f"Xbox Live recusou o login ({r.status_code}).")
    xbl = r.json()
    xbl_token = xbl["Token"]
    uhs = xbl["DisplayClaims"]["xui"][0]["uhs"]

    r = _post("https://xsts.auth.xboxlive.com/xsts/authorize", {
        "Properties": {"SandboxId": "RETAIL", "UserTokens": [xbl_token]},
        "RelyingParty": "rp://api.minecraftservices.com/", "TokenType": "JWT"}, "XSTS")
    if r.status_code != 200:
        try:
            code = int(r.json().get("XErr", 0))
        except Exception:
            code = 0
        raise AuthError(_XSTS_ERRORS.get(code, f"XSTS recusou o login ({r.status_code})."))
    xsts_token = r.json()["Token"]

    r = _post("https://api.minecraftservices.com/authentication/login_with_xbox",
              {"identityToken": f"XBL3.0 x={uhs};{xsts_token}"}, "Minecraft")
    if r.status_code != 200:
        raise AuthError(
            f"A API do Minecraft recusou o login ({r.status_code}). "
            "Se a app Azure é nova, falta a aprovação da Mojang (ver LEIAME.md).")
    mc_token = r.json()["access_token"]

    try:
        r = requests.get("https://api.minecraftservices.com/minecraft/profile",
                         headers={"Authorization": f"Bearer {mc_token}"}, timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise AuthError(f"Sem ligação (perfil): {exc}") from exc
    if r.status_code == 404:
        raise AuthError("Esta conta Microsoft não tem o Minecraft Java Edition.")
    if r.status_code != 200:
        raise AuthError(f"Não consegui ler o perfil ({r.status_code}).")
    profile = r.json()

    skins = profile.get("skins") or []
    active = next((s for s in skins if s.get("state") == "ACTIVE"), skins[0] if skins else {})
    return {
        "name": profile["name"],
        "id": profile["id"],
        "access_token": mc_token,
        "skin_url": active.get("url"),
        "skin_variant": (active.get("variant") or "CLASSIC").upper(),
        "capes": profile.get("capes") or [],
    }


# ---------- API pública ----------
def login():
    """Abre o browser para o login e devolve a conta Minecraft."""
    if config.CLIENT_ID.startswith("COLOCA"):
        raise AuthError("Falta o CLIENT_ID do Azure em config.py (ver LEIAME.md).")
    token = _ms_token(interactive=True)
    return _minecraft_login(token)


def restore():
    """Tenta entrar sem browser com a sessão guardada. Devolve a conta ou None."""
    if config.CLIENT_ID.startswith("COLOCA") or not config.CACHE_FILE.exists():
        return None
    try:
        token = _ms_token(interactive=False)
        return _minecraft_login(token) if token else None
    except Exception:
        return None


def logout():
    try:
        app, cache = _app()
        for acc in app.get_accounts():
            app.remove_account(acc)
    except Exception:
        pass
    config.CACHE_FILE.unlink(missing_ok=True)
    config.SKIN_FILE.unlink(missing_ok=True)
