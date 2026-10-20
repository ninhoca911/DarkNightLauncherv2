"""Interface do launcher (PySide6). Executa com: python launcher.py"""
import math
import os
import random
import shutil
import sys
from pathlib import Path

import requests
from PySide6.QtCore import QPointF, QRectF, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import (
    QBrush, QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QListWidget, QMessageBox, QProgressBar, QPushButton, QSlider, QStackedWidget,
    QVBoxLayout, QWidget,
)

import auth
import config
import game
import skin

RADIUS = 28
STYLE = """
* { font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 13px; color: #efe9ff; }
QLabel { background: transparent; }
#sidebar { background: rgba(12, 4, 28, 150); border-radius: 22px; }
#logo { font-size: 19px; font-weight: 800; letter-spacing: 1px; }
#nav { text-align: left; padding: 12px 18px; border: none; border-radius: 16px;
       background: transparent; color: #b8a6e6; font-size: 14px; }
#nav:hover { background: rgba(255, 255, 255, 18); }
#nav:checked { background: rgba(155, 92, 255, 120); color: #ffffff; }
#title { font-size: 24px; font-weight: 800; }
#muted { color: #b8a6e6; }
#name { font-size: 18px; font-weight: 700; }
#card { background: rgba(12, 4, 28, 130); border-radius: 22px; }
QComboBox { background: rgba(255, 255, 255, 22); border: none; border-radius: 14px;
            padding: 8px 14px; min-height: 20px; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView { background: #24104a; border: none; outline: none;
            selection-background-color: #7c4dff; border-radius: 10px; padding: 4px; }
QListWidget { background: rgba(12, 4, 28, 130); border: none; border-radius: 18px; padding: 8px; }
QListWidget::item { padding: 8px; border-radius: 10px; }
QListWidget::item:selected { background: rgba(155, 92, 255, 120); }
QPushButton { background: rgba(255, 255, 255, 24); border: none; border-radius: 16px; padding: 10px 18px; }
QPushButton:hover { background: rgba(255, 255, 255, 44); }
QPushButton:disabled { color: #7c6aa8; background: rgba(255, 255, 255, 10); }
#primary { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cff, stop:1 #c04dff);
           color: white; font-size: 17px; font-weight: 800; border-radius: 28px;
           padding: 0 56px; min-height: 56px; letter-spacing: 1px; }
#primary:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9d75ff, stop:1 #d070ff); }
#primary:disabled { background: rgba(255, 255, 255, 25); color: #9c8ac8; }
#winbtn { background: rgba(255, 255, 255, 22); border-radius: 15px; padding: 0; font-size: 14px; }
#winbtn:hover { background: rgba(255, 255, 255, 50); }
#closebtn { background: rgba(255, 255, 255, 22); border-radius: 15px; padding: 0; font-size: 14px; }
#closebtn:hover { background: #ff4d6d; }
#drop { border: 2px dashed rgba(190, 150, 255, 120); border-radius: 20px; padding: 26px; color: #b8a6e6; }
QProgressBar { background: rgba(255, 255, 255, 25); border: none; border-radius: 4px; max-height: 8px; }
QProgressBar::chunk { background: #b07cff; border-radius: 4px; }
QSlider::groove:horizontal { height: 6px; background: rgba(255, 255, 255, 40); border-radius: 3px; }
QSlider::handle:horizontal { background: #c9a6ff; width: 18px; margin: -6px 0; border-radius: 9px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 6px; background: rgba(255, 255, 255, 30); }
QCheckBox::indicator:checked { background: #9d6bff; }
QMessageBox { background: #1b0a38; }
"""


# ---------------------------------------------------------------- fundo animado
class Streak:
    """Uma estrela cadente (preta ou branca) que cai na diagonal."""

    def __init__(self, w, h, scatter=True):
        self.reset(w, h, scatter)

    def reset(self, w, h, scatter=False):
        self.white = random.random() < 0.55
        self.speed = random.uniform(160, 380)
        self.length = random.uniform(50, 150)
        self.width = random.uniform(1.4, 3.2)
        self.alpha = random.randint(150, 235)
        angle = math.radians(random.uniform(18, 30))
        self.dx, self.dy = -math.sin(angle), math.cos(angle)  # cai para baixo e para a esquerda
        self.x = random.uniform(0, w + h * 0.5)
        self.y = random.uniform(-h, h) if scatter else random.uniform(-self.length * 2, -10)


class Shell(QWidget):
    """Janela arredondada com fundo roxo e estrelas cadentes."""

    TOP = 54  # altura da zona de arrastar

    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.streaks = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def _tick(self):
        dt = 0.016
        w, h = self.width(), self.height()
        if not self.streaks:
            self.streaks = [Streak(w, h) for _ in range(34)]
        for s in self.streaks:
            s.x += s.dx * s.speed * dt
            s.y += s.dy * s.speed * dt
            if s.y - s.length > h or s.x + s.length < 0:
                s.reset(w, h)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.position().y() < self.TOP:
            handle = self.window().windowHandle()
            if handle:
                handle.startSystemMove()
        super().mousePressEvent(event)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, RADIUS, RADIUS)
        p.setClipPath(path)

        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0.0, QColor("#2a0f5c"))
        grad.setColorAt(0.55, QColor("#4a1d96"))
        grad.setColorAt(1.0, QColor("#6d2bc9"))
        p.fillRect(rect, QBrush(grad))

        glow = QRadialGradient(QPointF(rect.width() * 0.62, rect.height() * 0.55), rect.width() * 0.5)
        glow.setColorAt(0.0, QColor(190, 120, 255, 70))
        glow.setColorAt(1.0, QColor(190, 120, 255, 0))
        p.fillRect(rect, QBrush(glow))

        for s in self.streaks:
            tail = QPointF(s.x - s.dx * s.length, s.y - s.dy * s.length)
            head = QPointF(s.x, s.y)
            base = QColor(255, 255, 255) if s.white else QColor(0, 0, 0)
            g = QLinearGradient(tail, head)
            clear = QColor(base)
            clear.setAlpha(0)
            solid = QColor(base)
            solid.setAlpha(s.alpha)
            g.setColorAt(0.0, clear)
            g.setColorAt(1.0, solid)
            p.setPen(QPen(QBrush(g), s.width, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(tail, head)
            p.setPen(Qt.NoPen)
            p.setBrush(solid)
            p.drawEllipse(head, s.width * 0.7, s.width * 0.7)

        p.setClipping(False)
        p.setPen(QPen(QColor(255, 255, 255, 40), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(rect.adjusted(0.75, 0.75, -0.75, -0.75), RADIUS, RADIUS)


class SkinView(QWidget):
    """Mostra a skin com um brilho roxo por baixo e uma ligeira flutuação."""

    def __init__(self):
        super().__init__()
        self.pix = skin.placeholder()
        self.setMinimumSize(220, 300)
        self._t = 0.0
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(33)

    def set_pixmap(self, pix):
        self.pix = pix or skin.placeholder()
        self.update()

    def _tick(self):
        self._t += 0.033
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        # brilho no chão
        glow = QRadialGradient(QPointF(w / 2, h - 18), w * 0.42)
        glow.setColorAt(0.0, QColor(200, 140, 255, 150))
        glow.setColorAt(1.0, QColor(200, 140, 255, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(QPointF(w / 2, h - 18), w * 0.42, 16)
        # boneco, escalado sem suavização para manter os pixeis
        target_h = h - 40
        scale = max(1, int(target_h // self.pix.height()))
        if scale < 1:
            scale = 1
        scaled = self.pix.scaled(self.pix.width() * scale, self.pix.height() * scale,
                                 Qt.KeepAspectRatio, Qt.FastTransformation)
        bob = math.sin(self._t * 2.0) * 4
        x = (w - scaled.width()) / 2
        y = h - 30 - scaled.height() + bob
        p.drawPixmap(int(x), int(y), scaled)


# ---------------------------------------------------------------- utilitários
class DropZone(QLabel):
    """Área onde se arrastam ficheiros."""
    dropped = Signal(list)

    def __init__(self, text, extensions):
        super().__init__(text)
        self.extensions = tuple(e.lower() for e in extensions)
        self.setObjectName("drop")
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [u.toLocalFile() for u in event.mimeData().urls()]
        paths = [p for p in paths if p.lower().endswith(self.extensions)]
        if paths:
            self.dropped.emit(paths)


class Task(QThread):
    """Corre uma função num thread. Os callbacks voltam ao thread principal via `call`."""
    call = Signal(object)

    def __init__(self, fn, on_ok=None, on_fail=None, on_status=None, on_progress=None):
        super().__init__()
        self.fn, self.on_ok, self.on_fail = fn, on_ok, on_fail
        self.on_status, self.on_progress = on_status, on_progress
        self._value = 0
        self._max = 0

    def _emit(self, func, *args):
        if func:
            self.call.emit(lambda: func(*args))

    def _progress(self, value=None, maximum=None):
        if value is not None:
            self._value = value
        if maximum is not None:
            self._max = maximum
        self._emit(self.on_progress, self._value, self._max)

    def run(self):
        callback = {
            "setStatus": lambda text: self._emit(self.on_status, text),
            "setProgress": lambda v: self._progress(value=v),
            "setMax": lambda m: self._progress(maximum=m),
        }
        try:
            result = self.fn(callback)
        except Exception as exc:  # noqa: BLE001
            self._emit(self.on_fail, str(exc) or exc.__class__.__name__)
            return
        self._emit(self.on_ok, result)


# ---------------------------------------------------------------- janela principal
class MainWindow(Shell):
    def __init__(self):
        super().__init__()
        self.cfg = config.load()
        self.account = None
        self._tasks = []

        self.setWindowTitle(config.APP_NAME)
        self.setFixedSize(1060, 680)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        icon = config.resource("assets", "icon.png")
        if icon.exists():
            self.setWindowIcon(QIcon(str(icon)))

        outer = QHBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(16)
        outer.addWidget(self._build_sidebar())

        right = QVBoxLayout()
        right.setSpacing(0)
        right.addLayout(self._build_window_buttons())
        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_home_page())
        self.pages.addWidget(self._build_mods_page())
        self.pages.addWidget(self._build_cosmetics_page())
        self.pages.addWidget(self._build_settings_page())
        right.addWidget(self.pages, 1)
        outer.addLayout(right, 1)

        self._load_versions()
        self._refresh_mods()
        self._refresh_cape_preview()
        self._restore_session()

    # ---------- execução em segundo plano ----------
    @Slot(object)
    def _invoke(self, func):
        func()

    def run_task(self, fn, on_ok=None, on_fail=None, on_status=None, on_progress=None):
        task = Task(fn, on_ok, on_fail, on_status, on_progress)
        task.call.connect(self._invoke)
        task.finished.connect(lambda: self._tasks.remove(task) if task in self._tasks else None)
        self._tasks.append(task)
        task.start()

    # ---------- peças comuns ----------
    def _title(self, text, sub=None):
        box = QVBoxLayout()
        box.setContentsMargins(0, 6, 0, 10)
        t = QLabel(text)
        t.setObjectName("title")
        box.addWidget(t)
        if sub:
            s = QLabel(sub)
            s.setObjectName("muted")
            s.setWordWrap(True)
            box.addWidget(s)
        return box

    def _build_window_buttons(self):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 4, 0)
        row.addStretch(1)
        mini = QPushButton("–")
        mini.setObjectName("winbtn")
        mini.setFixedSize(30, 30)
        mini.clicked.connect(self.showMinimized)
        close = QPushButton("✕")
        close.setObjectName("closebtn")
        close.setFixedSize(30, 30)
        close.clicked.connect(self.close)
        row.addWidget(mini)
        row.addWidget(close)
        return row

    def _build_sidebar(self):
        bar = QFrame()
        bar.setObjectName("sidebar")
        bar.setFixedWidth(214)
        lay = QVBoxLayout(bar)
        lay.setContentsMargins(12, 8, 12, 14)
        lay.setSpacing(4)

        logo_path = config.resource("assets", "logo.png")
        if logo_path.exists():
            logo = QLabel()
            logo.setPixmap(QPixmap(str(logo_path)).scaledToWidth(150, Qt.SmoothTransformation))
            logo.setAlignment(Qt.AlignCenter)
            logo.setContentsMargins(0, 18, 0, 18)
        else:
            logo = QLabel(config.APP_NAME.upper())
            logo.setObjectName("logo")
            logo.setAlignment(Qt.AlignCenter)
            logo.setContentsMargins(0, 22, 0, 22)
        lay.addWidget(logo)

        self.nav_buttons = []
        for index, name in enumerate(["Início", "Mods", "Cosméticos", "Definições"]):
            btn = QPushButton(name)
            btn.setObjectName("nav")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _=False, i=index: self._go(i))
            lay.addWidget(btn)
            self.nav_buttons.append(btn)
        self.nav_buttons[0].setChecked(True)
        lay.addStretch(1)

        self.account_label = QLabel("Sem sessão iniciada")
        self.account_label.setObjectName("muted")
        self.account_label.setWordWrap(True)
        self.account_label.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.account_label)
        self.login_btn = QPushButton("Entrar com Microsoft")
        self.login_btn.clicked.connect(lambda: self._login())
        lay.addWidget(self.login_btn)
        return bar

    def _go(self, index):
        self.pages.setCurrentIndex(index)
        for i, b in enumerate(self.nav_buttons):
            b.setChecked(i == index)

    # ---------- página Início (menu principal) ----------
    def _build_home_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(20, 0, 20, 10)
        lay.setSpacing(8)

        self.name_label = QLabel("")
        self.name_label.setObjectName("name")
        self.name_label.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.name_label)

        self.skin_view = SkinView()
        lay.addWidget(self.skin_view, 1)

        self.play_btn = QPushButton("LAUNCH")
        self.play_btn.setObjectName("primary")
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.clicked.connect(self._play)
        lay.addWidget(self.play_btn, alignment=Qt.AlignCenter)

        row = QHBoxLayout()
        row.setAlignment(Qt.AlignCenter)
        self.version_box = QComboBox()
        self.version_box.setMinimumWidth(150)
        self.version_box.currentTextChanged.connect(self._update_play_text)
        self.loader_box = QComboBox()
        self.loader_box.addItems(game.LOADERS)
        self.loader_box.setCurrentText(self.cfg.get("loader", "Vanilla"))
        row.addWidget(self.version_box)
        row.addWidget(self.loader_box)
        lay.addLayout(row)

        self.status_label = QLabel("")
        self.status_label.setObjectName("muted")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setValue(0)
        lay.addWidget(self.status_label)
        lay.addWidget(self.progress)
        return page

    def _update_play_text(self, version):
        if version and version != "A carregar...":
            self.play_btn.setText(f"LAUNCH {version}")
        else:
            self.play_btn.setText("LAUNCH")

    def _load_versions(self):
        snapshots = self.cfg.get("snapshots", False)
        self.version_box.blockSignals(True)
        self.version_box.clear()
        self.version_box.addItem("A carregar...")
        self.version_box.blockSignals(False)
        self._update_play_text("")

        def done(versions):
            self.version_box.clear()
            self.version_box.addItems(versions)
            saved = self.cfg.get("version")
            if saved in versions:
                self.version_box.setCurrentText(saved)
            self._update_play_text(self.version_box.currentText())

        self.run_task(lambda cb: game.list_versions(snapshots), done,
                      lambda err: self.status_label.setText(f"Erro a obter versões: {err}"))

    def _play(self):
        if not self.account:
            self._login(then=self._play)
            return
        version = self.version_box.currentText()
        loader = self.loader_box.currentText()
        if not version or version == "A carregar...":
            return
        ram = self.cfg.get("ram", 4096)
        self.cfg.update(version=version, loader=loader)
        config.save(self.cfg)
        self.play_btn.setEnabled(False)
        self.progress.setValue(0)

        def job(cb):
            account = auth.restore() or self.account  # renova o token do Minecraft
            version_id = game.install(version, loader, cb)
            return account, version_id

        def started(result):
            account, version_id = result
            self.account = account
            game.launch(version_id, account, ram)
            self.status_label.setText("Jogo iniciado. Bom jogo!")
            self.progress.setValue(self.progress.maximum())
            self.play_btn.setEnabled(True)

        def failed(err):
            self.status_label.setText(f"Erro: {err}")
            self.play_btn.setEnabled(True)

        self.run_task(job, started, failed,
                      on_status=self.status_label.setText, on_progress=self._set_progress)

    def _set_progress(self, value, maximum):
        self.progress.setMaximum(max(maximum, 1))
        self.progress.setValue(value)

    # ---------- login (browser) ----------
    def _login(self, then=None):
        if config.CLIENT_ID.startswith("COLOCA"):
            QMessageBox.warning(self, config.APP_NAME,
                                "Falta o CLIENT_ID do Azure em config.py. Vê o LEIAME.md.")
            return
        self.login_btn.setEnabled(False)
        self.status_label.setText("Abre o browser e conclui o login Microsoft...")
        self.account_label.setText("A aguardar login no browser...")

        def ok(account):
            self.login_btn.setEnabled(True)
            self.status_label.setText("")
            self._logged_in(account)
            if then:
                then()

        def fail(err):
            self.login_btn.setEnabled(True)
            self.status_label.setText(f"Login falhou: {err}")
            self.account_label.setText("Sem sessão iniciada")

        self.run_task(lambda cb: auth.login(), ok, fail)

    def _restore_session(self):
        self.run_task(lambda cb: auth.restore(),
                      lambda acc: self._logged_in(acc) if acc else None)

    def _logged_in(self, account):
        self.account = account
        self.account_label.setText(f"Sessão: {account['name']}")
        self.name_label.setText(account["name"])
        self.login_btn.setText("Trocar de conta")
        self._load_skin(account)
        self._load_official_capes()

    def _logout(self):
        auth.logout()
        self.account = None
        self.account_label.setText("Sem sessão iniciada")
        self.name_label.setText("")
        self.login_btn.setText("Entrar com Microsoft")
        self.skin_view.set_pixmap(None)
        self.official_capes.clear()
        self.official_capes.addItem("Inicia sessão para ver as tuas capas")

    def _load_skin(self, account):
        url, slim = account.get("skin_url"), account.get("skin_variant") == "SLIM"
        if not url:
            self.skin_view.set_pixmap(None)
            return

        def job(cb):
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            config.ensure_dirs()
            config.SKIN_FILE.write_bytes(r.content)
            return skin.render(config.SKIN_FILE, slim)

        self.run_task(job, lambda pix: self.skin_view.set_pixmap(pix), lambda err: None)

    # ---------- página Mods ----------
    def _build_mods_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(20, 0, 20, 10)
        lay.addLayout(self._title(
            "Mods", "Arrasta ficheiros .jar para aqui. Só funcionam com o loader Fabric ou Forge."))
        drop = DropZone("Larga aqui os teus mods (.jar)", [".jar"])
        drop.dropped.connect(self._add_mods)
        lay.addWidget(drop)
        self.mods_list = QListWidget()
        self.mods_list.setSelectionMode(QListWidget.ExtendedSelection)
        lay.addWidget(self.mods_list, 1)
        row = QHBoxLayout()
        add = QPushButton("Adicionar...")
        add.clicked.connect(self._pick_mods)
        remove = QPushButton("Remover selecionados")
        remove.clicked.connect(self._remove_mods)
        open_btn = QPushButton("Abrir pasta dos mods")
        open_btn.clicked.connect(lambda: self._open_folder(config.MODS_DIR))
        row.addWidget(add)
        row.addWidget(remove)
        row.addStretch(1)
        row.addWidget(open_btn)
        lay.addLayout(row)
        return page

    def _open_folder(self, path):
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(str(path))  # noqa: S606
        elif sys.platform == "darwin":
            os.system(f'open "{path}"')
        else:
            os.system(f'xdg-open "{path}"')

    def _refresh_mods(self):
        config.ensure_dirs()
        self.mods_list.clear()
        for f in sorted(config.MODS_DIR.glob("*.jar")):
            self.mods_list.addItem(f.name)

    def _add_mods(self, paths):
        config.ensure_dirs()
        for p in paths:
            shutil.copy2(p, config.MODS_DIR / Path(p).name)
        self._refresh_mods()

    def _pick_mods(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Escolher mods", "", "Mods (*.jar)")
        if paths:
            self._add_mods(paths)

    def _remove_mods(self):
        for item in self.mods_list.selectedItems():
            (config.MODS_DIR / item.text()).unlink(missing_ok=True)
        self._refresh_mods()

    # ---------- página Cosméticos ----------
    def _build_cosmetics_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(20, 0, 20, 10)
        lay.addLayout(self._title(
            "Cosméticos",
            "Carrega um PNG para a tua capa personalizada (formato 64x32) e vê a pré-visualização."))
        row = QHBoxLayout()

        left = QVBoxLayout()
        self.cape_drop = DropZone("Larga aqui o PNG da capa", [".png"])
        self.cape_drop.dropped.connect(lambda paths: self._set_cape(paths[0]))
        left.addWidget(self.cape_drop)
        pick = QPushButton("Escolher PNG...")
        pick.clicked.connect(self._pick_cape)
        left.addWidget(pick)
        note = QLabel("Nota: a Mojang só mostra a outros jogadores capas oficiais. "
                      "A capa personalizada é guardada no launcher para uso local.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        left.addWidget(note)
        left.addStretch(1)
        row.addLayout(left, 1)

        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(22, 20, 22, 20)
        self.cape_preview = QLabel("Sem capa")
        self.cape_preview.setAlignment(Qt.AlignCenter)
        self.cape_preview.setMinimumSize(200, 280)
        cl.addWidget(self.cape_preview)
        row.addWidget(card)
        lay.addLayout(row)

        lab = QLabel("Capas oficiais da conta")
        lab.setObjectName("name")
        lay.addWidget(lab)
        self.official_capes = QComboBox()
        self.official_capes.addItem("Inicia sessão para ver as tuas capas")
        equip = QPushButton("Equipar")
        equip.clicked.connect(lambda: self._equip_cape())
        hide = QPushButton("Esconder capa")
        hide.clicked.connect(lambda: self._equip_cape(hide=True))
        r2 = QHBoxLayout()
        r2.addWidget(self.official_capes, 1)
        r2.addWidget(equip)
        r2.addWidget(hide)
        lay.addLayout(r2)
        lay.addStretch(1)
        return page

    def _pick_cape(self):
        path, _ = QFileDialog.getOpenFileName(self, "Escolher capa", "", "Imagens PNG (*.png)")
        if path:
            self._set_cape(path)

    def _set_cape(self, path):
        pix = QPixmap(path)
        if pix.isNull():
            QMessageBox.warning(self, config.APP_NAME, "Não consegui abrir essa imagem.")
            return
        w, h = pix.width(), pix.height()
        if w != h * 2 and w * 17 != h * 22:
            QMessageBox.warning(
                self, config.APP_NAME,
                f"Tamanho {w}x{h} não é de uma capa. Usa 64x32 (ou múltiplos, ex: 128x64).")
            return
        config.ensure_dirs()
        shutil.copy2(path, config.CAPES_DIR / "custom.png")
        self._refresh_cape_preview()

    def _refresh_cape_preview(self):
        path = config.CAPES_DIR / "custom.png"
        if not path.exists():
            return
        pix = QPixmap(str(path))
        scale = pix.width() / 64 if pix.width() == pix.height() * 2 else pix.width() / 22
        # Frente da capa no formato 64x32: x=1..10, y=1..16
        front = pix.copy(int(scale), int(scale), int(10 * scale), int(16 * scale))
        self.cape_preview.setPixmap(front.scaled(180, 288, Qt.KeepAspectRatio, Qt.FastTransformation))

    def _api_headers(self):
        return {"Authorization": f"Bearer {self.account['access_token']}"}

    def _load_official_capes(self):
        capes = (self.account or {}).get("capes", [])
        self.official_capes.clear()
        if not capes:
            self.official_capes.addItem("Esta conta não tem capas oficiais")
            return
        for c in capes:
            label = c.get("alias", "Capa") + (" (ativa)" if c.get("state") == "ACTIVE" else "")
            self.official_capes.addItem(label, c["id"])

    def _equip_cape(self, hide=False):
        if not self.account:
            QMessageBox.information(self, config.APP_NAME, "Inicia sessão primeiro.")
            return
        cape_id = self.official_capes.currentData()
        if not hide and not cape_id:
            return
        url = "https://api.minecraftservices.com/minecraft/profile/capes/active"
        headers = self._api_headers()

        def job(cb):
            if hide:
                r = requests.delete(url, headers=headers, timeout=15)
            else:
                r = requests.put(url, headers=headers, json={"capeId": cape_id}, timeout=15)
            r.raise_for_status()
            return True

        def done(_):
            QMessageBox.information(self, config.APP_NAME, "Capa atualizada.")

        self.run_task(job, done,
                      lambda err: QMessageBox.warning(self, config.APP_NAME, f"Erro: {err}"))

    # ---------- página Definições ----------
    def _build_settings_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(20, 0, 20, 10)
        lay.addLayout(self._title("Definições"))

        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.setSpacing(12)

        self.ram_label = QLabel()
        self.ram_slider = QSlider(Qt.Horizontal)
        self.ram_slider.setRange(1024, 16384)
        self.ram_slider.setSingleStep(512)
        self.ram_slider.setPageStep(512)
        self.ram_slider.setValue(self.cfg.get("ram", 4096))
        self.ram_slider.valueChanged.connect(self._ram_changed)
        self._ram_changed(self.ram_slider.value())
        cl.addWidget(self.ram_label)
        cl.addWidget(self.ram_slider)

        self.snap_check = QCheckBox("Mostrar snapshots na lista de versões")
        self.snap_check.setChecked(self.cfg.get("snapshots", False))
        self.snap_check.toggled.connect(self._snapshots_changed)
        cl.addWidget(self.snap_check)

        folder = QPushButton("Abrir pasta do jogo")
        folder.clicked.connect(lambda: self._open_folder(config.MC_DIR))
        cl.addWidget(folder, alignment=Qt.AlignLeft)
        out = QPushButton("Terminar sessão")
        out.clicked.connect(self._logout)
        cl.addWidget(out, alignment=Qt.AlignLeft)
        lay.addWidget(card)
        lay.addStretch(1)
        return page

    def _ram_changed(self, value):
        self.ram_label.setText(f"Memória RAM: {value / 1024:.1f} GB")
        self.cfg["ram"] = value
        config.save(self.cfg)

    def _snapshots_changed(self, checked):
        self.cfg["snapshots"] = checked
        config.save(self.cfg)
        self._load_versions()


def main():
    config.ensure_dirs()
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
