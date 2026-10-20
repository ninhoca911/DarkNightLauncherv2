"""Desenha a skin de Minecraft (vista de frente) a partir da textura PNG."""
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap, QTransform


def skin_parts(slim, legacy):
    """Lista de (origem_x, origem_y, larg, alt, destino_x, destino_y, espelhar)
    em pixeis de uma skin 64x64 (ou 64x32 se legacy), por ordem de desenho.
    O destino é numa tela de 16x32 pixeis."""
    aw = 3 if slim else 4          # largura do braço
    ax_r = 4 - aw                  # braço direito (esquerda de quem vê)
    parts = [
        # corpo base
        (8, 8, 8, 8, 4, 0, False),                    # cabeça
        (20, 20, 8, 12, 4, 8, False),                 # tronco
        (44, 20, aw, 12, ax_r, 8, False),             # braço direito
        (4, 20, 4, 12, 4, 20, False),                 # perna direita
    ]
    if legacy:
        parts += [(44, 20, aw, 12, 12, 8, True), (4, 20, 4, 12, 8, 20, True)]
    else:
        parts += [(36, 52, aw, 12, 12, 8, False), (20, 52, 4, 12, 8, 20, False),
                  # camadas por cima (casaco, mangas, calças)
                  (20, 36, 8, 12, 4, 8, False),
                  (44, 36, aw, 12, ax_r, 8, False),
                  (52, 52, aw, 12, 12, 8, False),
                  (4, 36, 4, 12, 4, 20, False),
                  (4, 52, 4, 12, 8, 20, False)]
    parts.append((40, 8, 8, 8, 4, 0, False))          # chapéu (camada da cabeça)
    return parts


def render(png_path, slim=False):
    """Devolve um QPixmap (16x32 * escala da skin) ou None se a imagem for inválida."""
    img = QImage(str(png_path)).convertToFormat(QImage.Format_ARGB32)
    if img.isNull() or img.width() < 64:
        return None
    s = img.width() // 64
    legacy = img.height() < img.width()  # 64x32
    out = QImage(16 * s, 32 * s, QImage.Format_ARGB32)
    out.fill(Qt.transparent)
    p = QPainter(out)
    for sx, sy, w, h, dx, dy, flip in skin_parts(slim, legacy):
        piece = img.copy(QRect(sx * s, sy * s, w * s, h * s))
        if flip:
            piece = piece.transformed(QTransform().scale(-1, 1))
        p.drawImage(dx * s, dy * s, piece)
    p.end()
    return QPixmap.fromImage(out)


def placeholder():
    """Boneco simples para quando ainda não há sessão iniciada."""
    img = QImage(16, 32, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    skin, hair, shirt, pants, shoe = (QColor(c) for c in
                                      ("#c99677", "#5b3a29", "#8a5cf0", "#3b2a8a", "#1c1530"))
    p.fillRect(4, 0, 8, 8, skin)
    p.fillRect(4, 0, 8, 3, hair)
    p.fillRect(5, 4, 2, 1, QColor("#ffffff"))
    p.fillRect(9, 4, 2, 1, QColor("#ffffff"))
    p.fillRect(4, 8, 8, 12, shirt)
    p.fillRect(0, 8, 4, 12, skin)
    p.fillRect(12, 8, 4, 12, skin)
    p.fillRect(0, 8, 4, 4, shirt)
    p.fillRect(12, 8, 4, 4, shirt)
    p.fillRect(4, 20, 4, 12, pants)
    p.fillRect(8, 20, 4, 12, pants)
    p.fillRect(4, 29, 4, 3, shoe)
    p.fillRect(8, 29, 4, 3, shoe)
    p.end()
    return QPixmap.fromImage(img)
