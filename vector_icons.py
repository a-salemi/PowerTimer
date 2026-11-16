"""
Vector Icon Generator for PowerTimer
Generates high-resolution, crisp vector icons using QPainter
"""
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen, QLinearGradient, QPixmap, QPainterPath, QPolygonF
import math

def draw_vector_icon(icon_type: str, size: int = 44) -> QPixmap:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Gradients mapped to actions (matching macOS & EtherDNS style)
    gradients = {
        "shutdown": ("#EF4444", "#B91C1C"),     # Apple Red
        "restart": ("#A855F7", "#6D28D9"),      # Royal Purple
        "sleep": ("#3B82F6", "#1D4ED8"),        # Apple Blue
        "hibernate": ("#06B6D4", "#0369A1"),    # Oceanic Cyan
        "lock": ("#10B981", "#047857"),         # Emerald Green
        "display_off": ("#F59E0B", "#B45309"),  # Sunset Amber
        "app": ("#2563EB", "#7C3AED"),          # Brand Indigo-Blue
    }

    c1, c2 = gradients.get(icon_type, ("#3B82F6", "#1D4ED8"))

    # 1. Squircle Background
    grad = QLinearGradient(0, 0, size, size)
    grad.setColorAt(0, QColor(c1))
    grad.setColorAt(1, QColor(c2))
    p.setBrush(QBrush(grad))
    p.setPen(Qt.PenStyle.NoPen)
    radius = size * 0.26
    p.drawRoundedRect(QRectF(0, 0, size, size), radius, radius)

    # Subtle inner bevel / border highlight
    p.setPen(QPen(QColor(255, 255, 255, 40), 1.0))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(0.5, 0.5, size - 1, size - 1), radius, radius)

    cx, cy = size / 2.0, size / 2.0

    if icon_type == "shutdown":
        # Power arc + vertical pin
        stroke = max(2.2, size * 0.08)
        p.setPen(QPen(QColor("#FFFFFF"), stroke, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        margin = size * 0.25
        rect = QRectF(margin, margin, size - 2 * margin, size - 2 * margin)
        p.drawArc(rect, 45 * 16, 270 * 16)
        p.drawLine(QPointF(cx, size * 0.18), QPointF(cx, cy * 0.95))

    elif icon_type == "restart":
        # Dual circular reload arrows (Apple / EtherDNS style)
        r = size * 0.23
        stroke = max(2.2, size * 0.08)
        p.setPen(QPen(QColor("#FFFFFF"), stroke, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        
        rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)
        p.drawArc(rect, 20 * 16, 140 * 16)
        p.drawArc(rect, 200 * 16, 140 * 16)

        # Arrowheads (solid filled triangles)
        p.setBrush(QBrush(QColor("#FFFFFF")))
        p.setPen(Qt.PenStyle.NoPen)
        arrow_size = size * 0.13

        # Top-right arrowhead
        rad1 = math.radians(15)
        ax1 = cx + r * math.cos(rad1)
        ay1 = cy - r * math.sin(rad1)
        t1 = QPolygonF([
            QPointF(ax1 - arrow_size * 0.5, ay1 - arrow_size * 0.8),
            QPointF(ax1 + arrow_size * 0.6, ay1 - arrow_size * 0.2),
            QPointF(ax1 - arrow_size * 0.2, ay1 + arrow_size * 0.6)
        ])
        p.drawPolygon(t1)

        # Bottom-left arrowhead
        rad2 = math.radians(195)
        ax2 = cx + r * math.cos(rad2)
        ay2 = cy - r * math.sin(rad2)
        t2 = QPolygonF([
            QPointF(ax2 + arrow_size * 0.5, ay2 + arrow_size * 0.8),
            QPointF(ax2 - arrow_size * 0.6, ay2 + arrow_size * 0.2),
            QPointF(ax2 + arrow_size * 0.2, ay2 - arrow_size * 0.6)
        ])
        p.drawPolygon(t2)

    elif icon_type == "sleep":
        # Crescent Moon
        p.setBrush(QBrush(QColor("#FFFFFF")))
        p.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        path.addEllipse(QPointF(cx + size * 0.02, cy), size * 0.26, size * 0.26)
        path2 = QPainterPath()
        path2.addEllipse(QPointF(cx + size * 0.15, cy - size * 0.09), size * 0.23, size * 0.23)
        moon = path.subtracted(path2)
        p.drawPath(moon)

    elif icon_type == "hibernate":
        # Snowflake
        p.setPen(QPen(QColor("#FFFFFF"), size * 0.07, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        r = size * 0.25
        for i in range(3):
            angle = math.radians(i * 60)
            dx = r * math.cos(angle)
            dy = r * math.sin(angle)
            p.drawLine(QPointF(cx - dx, cy - dy), QPointF(cx + dx, cy + dy))
        # Branchlets
        br = size * 0.16
        p.setBrush(QBrush(QColor("#FFFFFF")))
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(6):
            angle = math.radians(i * 60)
            bx = cx + br * math.cos(angle)
            by = cy + br * math.sin(angle)
            p.drawEllipse(QPointF(bx, by), size * 0.03, size * 0.03)

    elif icon_type == "lock":
        # Padlock shackle
        stroke = max(2.0, size * 0.08)
        p.setPen(QPen(QColor("#FFFFFF"), stroke, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        shackle_rect = QRectF(cx - size * 0.14, size * 0.21, size * 0.28, size * 0.28)
        p.drawArc(shackle_rect, 0, 180 * 16)
        # Body
        p.setBrush(QBrush(QColor("#FFFFFF")))
        p.setPen(Qt.PenStyle.NoPen)
        body_rect = QRectF(cx - size * 0.22, cy * 0.95, size * 0.44, size * 0.32)
        p.drawRoundedRect(body_rect, size * 0.07, size * 0.07)
        # Keyhole
        p.setBrush(QBrush(QColor(c2)))
        p.drawEllipse(QPointF(cx, cy * 1.15), size * 0.045, size * 0.045)
        p.drawRect(QRectF(cx - size * 0.02, cy * 1.15, size * 0.04, size * 0.06))

    elif icon_type == "display_off":
        # Monitor
        stroke = max(2.0, size * 0.075)
        p.setPen(QPen(QColor("#FFFFFF"), stroke, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)
        screen_rect = QRectF(cx - size * 0.26, size * 0.22, size * 0.52, size * 0.36)
        p.drawRoundedRect(screen_rect, size * 0.06, size * 0.06)
        # Stand
        p.drawLine(QPointF(cx, size * 0.58), QPointF(cx, size * 0.72))
        p.drawLine(QPointF(cx - size * 0.15, size * 0.72), QPointF(cx + size * 0.15, size * 0.72))
        # Power dot
        p.setBrush(QBrush(QColor("#FFFFFF")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, size * 0.40), size * 0.04, size * 0.04)

    elif icon_type == "app":
        # Shield with timer / power
        p.setPen(QPen(QColor("#FFFFFF"), size * 0.08, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        margin = size * 0.24
        p.drawArc(QRectF(margin, margin, size - 2 * margin, size - 2 * margin), 45 * 16, 270 * 16)
        p.drawLine(QPointF(cx, size * 0.16), QPointF(cx, cy * 0.95))

    p.end()
    return pix

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    for act in ["shutdown", "restart", "sleep", "hibernate", "lock", "display_off", "app"]:
        px = draw_vector_icon(act, 64)
        print(f"Icon {act}: {px.width()}x{px.height()} generated successfully")
