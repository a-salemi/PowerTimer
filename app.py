"""
=============================================================================
 PowerTimer v2.3 - Streamlined macOS Dark System Power Scheduler
 Sidebar + 1-2-3 Linear UX Flow | Google Sans Font | Vector Icons
 Crash-proof, clean, fully functional
=============================================================================
"""
import sys
import os
import time
import datetime
import subprocess
import ctypes
import winsound
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QAbstractButton, QTimeEdit,
    QSlider, QSystemTrayIcon, QMenu, QScrollArea, QGridLayout,
    QMessageBox, QSpinBox, QGraphicsDropShadowEffect, QStackedWidget,
    QProgressBar
)
from PyQt6.QtCore import (
    Qt, QTimer, QTime, QPropertyAnimation, pyqtProperty, QEasingCurve,
    QRectF, QSize, pyqtSignal, QPoint, QPointF
)
from PyQt6.QtGui import (
    QColor, QPainter, QBrush, QPen, QFont, QIcon, QPixmap,
    QPainterPath, QLinearGradient, QFontDatabase
)

import vector_icons


# ---------------------------------------------------------------------------
# Resource Path Helper for PyInstaller Bundle
# ---------------------------------------------------------------------------
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ---------------------------------------------------------------------------
# macOS Traffic Light Window Controls
# ---------------------------------------------------------------------------
class MacTrafficLights(QWidget):
    closeClicked = pyqtSignal()
    minimizeClicked = pyqtSignal()
    zoomClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(68, 20)
        self.is_hovered = False
        self.setMouseTracking(True)

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            x = event.position().x()
            if 0 <= x <= 18:
                self.closeClicked.emit()
            elif 22 <= x <= 40:
                self.minimizeClicked.emit()
            elif 44 <= x <= 62:
                self.zoomClicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = [
            ("#FF5F56", "#E0443E"),
            ("#FFBD2E", "#DEA123"),
            ("#27C93F", "#1AAB29"),
        ]
        centers = [9.0, 31.0, 53.0]
        radius = 6.0
        for i, (normal_c, hover_c) in enumerate(colors):
            cx = centers[i]
            cy = 10.0
            col = QColor(hover_c if self.is_hovered else normal_c)
            p.setBrush(QBrush(col))
            p.setPen(QPen(QColor(0, 0, 0, 40), 0.8))
            p.drawEllipse(QPointF(cx, cy), radius, radius)
            if self.is_hovered:
                p.setPen(QPen(QColor(0, 0, 0, 160), 1.2,
                              Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                if i == 0:
                    p.drawLine(QPointF(cx-2.5, cy-2.5), QPointF(cx+2.5, cy+2.5))
                    p.drawLine(QPointF(cx+2.5, cy-2.5), QPointF(cx-2.5, cy+2.5))
                elif i == 1:
                    p.drawLine(QPointF(cx-3.0, cy), QPointF(cx+3.0, cy))
                elif i == 2:
                    p.drawLine(QPointF(cx-2.5, cy), QPointF(cx+2.5, cy))
                    p.drawLine(QPointF(cx, cy-2.5), QPointF(cx, cy+2.5))
        p.end()


# ---------------------------------------------------------------------------
# iOS-style Animated Toggle Switch
# ---------------------------------------------------------------------------
class ModernSwitch(QAbstractButton):
    def __init__(self, parent=None, checked=False):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setFixedSize(40, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._thumb_position = 20.0 if checked else 3.0
        self._anim = QPropertyAnimation(self, b"thumb_position", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self._on_toggled)

    def _on_toggled(self, checked):
        self._anim.stop()
        self._anim.setStartValue(self._thumb_position)
        self._anim.setEndValue(20.0 if checked else 3.0)
        self._anim.start()

    @pyqtProperty(float)
    def thumb_position(self):
        return self._thumb_position

    @thumb_position.setter
    def thumb_position(self, pos):
        self._thumb_position = pos
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        track_color = QColor("#2563EB") if self.isChecked() else QColor("#222636")
        p.setBrush(QBrush(track_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(0, 0, 40, 22), 11, 11)
        p.setBrush(QBrush(QColor("#FFFFFF")))
        p.drawEllipse(QRectF(self._thumb_position, 2.5, 17.0, 17.0))
        p.end()


# ---------------------------------------------------------------------------
# Action Card (clickable, vector icon + title + subtitle)
# ---------------------------------------------------------------------------
class ModernActionCard(QFrame):
    cardSelected = pyqtSignal(str)

    def __init__(self, action_id, title, subtitle, accent_color, parent=None):
        super().__init__(parent)
        self.action_id = action_id
        self.accent_color = accent_color
        self.is_selected = False

        self.setFixedHeight(106)
        self.setMinimumWidth(100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("ActionCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 10)
        layout.setSpacing(5)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(36, 36)
        self.icon_label.setPixmap(vector_icons.draw_vector_icon(action_id, 36))
        self.icon_label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.icon_label)

        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet(
            "font-size: 13px; font-weight: 700; color: #FFFFFF;"
            " background: transparent; border: none;")
        self.lbl_sub = QLabel(subtitle)
        self.lbl_sub.setStyleSheet(
            "font-size: 10px; color: #8E8E93; background: transparent; border: none;")
        self.lbl_sub.setWordWrap(True)
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_sub)
        layout.addStretch()
        self.update_style()

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.update_style()

    def update_style(self):
        if self.is_selected:
            self.setStyleSheet(f"""
                QFrame#ActionCard {{
                    background-color: #171E2E;
                    border: 1.5px solid {self.accent_color};
                    border-radius: 14px;
                }}
                QFrame#ActionCard QLabel {{
                    background: transparent;
                    border: none;
                }}
            """)
        else:
            self.setStyleSheet("""
                QFrame#ActionCard {
                    background-color: #131622;
                    border: 1px solid rgba(255,255,255,0.06);
                    border-radius: 14px;
                }
                QFrame#ActionCard:hover {
                    background-color: #191D2D;
                    border: 1px solid rgba(255,255,255,0.16);
                }
                QFrame#ActionCard QLabel {
                    background: transparent;
                    border: none;
                }
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.cardSelected.emit(self.action_id)
        super().mousePressEvent(event)


# ---------------------------------------------------------------------------
# Sidebar Navigation Button
# ---------------------------------------------------------------------------
class SidebarNavButton(QPushButton):
    def __init__(self, text, icon_str, parent=None):
        super().__init__(f"  {icon_str}  {text}", parent)
        self.setCheckable(True)
        self.setFixedHeight(38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            SidebarNavButton {
                text-align: left;
                padding-left: 10px;
                font-size: 13px;
                font-weight: 500;
                color: #6B7280;
                background-color: transparent;
                border-radius: 10px;
                border: none;
            }
            SidebarNavButton:hover {
                color: #E5E7EB;
                background-color: rgba(255,255,255,0.05);
            }
            SidebarNavButton:checked {
                color: #FFFFFF;
                background-color: #1E2538;
                font-weight: 700;
                border: none;
            }
            SidebarNavButton:focus {
                outline: none;
            }
        """)


# ---------------------------------------------------------------------------
# Main PowerTimer Window Class
# ---------------------------------------------------------------------------
class ModernPowerTimer(QMainWindow):
    def __init__(self):
        super().__init__()

        # Frameless Window
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(1020, 660)
        self.setMinimumSize(980, 640)

        self._drag_pos = None

        # State Variables
        self.is_scheduled = False
        self.schedule_mode = 0  # 0: Countdown, 1: Specific Time, 2: Inactivity
        self.selected_action = "shutdown"
        self.target_datetime: Optional[datetime.datetime] = None
        self.total_seconds_duration = 0
        self.has_warned_user = False

        # Metadata
        self.actions_info = {
            "shutdown": {
                "title": "Shutdown",
                "desc": "Power off PC",
                "color": "#EF4444",
                "details": "Terminates all running processes and powers off the PC cleanly."
            },
            "restart": {
                "title": "Restart",
                "desc": "Reboot cleanly",
                "color": "#A855F7",
                "details": "Restarts your operating system cleanly without cutting power."
            },
            "sleep": {
                "title": "Sleep",
                "desc": "Low-power standby",
                "color": "#3B82F6",
                "details": "Keeps session in RAM and puts computer into instant low-power sleep."
            },
            "hibernate": {
                "title": "Hibernate",
                "desc": "Save session to disk",
                "color": "#06B6D4",
                "details": "Saves open documents and programs to SSD/HDD and turns off PC."
            },
            "lock": {
                "title": "Lock Screen",
                "desc": "Secure workstation",
                "color": "#10B981",
                "details": "Immediately locks the active Windows session requiring password."
            },
            "display_off": {
                "title": "Turn Off Screen",
                "desc": "Blank all monitors",
                "color": "#F59E0B",
                "details": "Powers off monitors until mouse movement or keyboard press."
            }
        }

        # Master Heartbeat Timers
        self.heartbeat_timer = QTimer(self)
        self.heartbeat_timer.timeout.connect(self._on_heartbeat_tick)

        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self._on_idle_tick)
        self.idle_timer.start(1000)

        self.init_ui()
        self.init_tray()

    # Window Dragging
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def init_ui(self):
        # Outer wrapper
        self.outer_wrapper = QFrame(self)
        self.outer_wrapper.setObjectName("OuterWrapper")
        self.setCentralWidget(self.outer_wrapper)
        self.outer_wrapper.setStyleSheet("""
            QFrame#OuterWrapper {
                background-color: #0C0E14;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 18px;
            }
            QLabel {
                background: transparent;
                border: none;
                color: #FFFFFF;
                font-family: "Google Sans", sans-serif;
            }
            QPushButton:focus {
                outline: none;
            }
        """)

        root_layout = QHBoxLayout(self.outer_wrapper)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Left Sidebar
        self.sidebar = self._build_sidebar()
        root_layout.addWidget(self.sidebar)

        # Vertical Divider
        divider = QFrame()
        divider.setFixedWidth(1)
        divider.setStyleSheet("background-color: rgba(255, 255, 255, 0.06);")
        root_layout.addWidget(divider)

        # 2. Main Stacked Pages (Page 0: Setup Wizard, Page 1: Running Dashboard)
        self.main_stack = QStackedWidget()
        self.page_setup = self._build_setup_page()
        self.page_running = self._build_running_page()

        self.main_stack.addWidget(self.page_setup)
        self.main_stack.addWidget(self.page_running)
        root_layout.addWidget(self.main_stack)

        self._update_summary_dock()

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("background-color: #10121A; border-top-left-radius: 18px; border-bottom-left-radius: 18px;")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        # macOS Traffic Lights
        self.traffic_lights = MacTrafficLights()
        self.traffic_lights.closeClicked.connect(self.close)
        self.traffic_lights.minimizeClicked.connect(self.showMinimized)
        self.traffic_lights.zoomClicked.connect(self._toggle_zoom)
        layout.addWidget(self.traffic_lights)
        layout.addSpacing(6)

        # App Brand
        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(10)

        app_icon_lbl = QLabel()
        app_icon_lbl.setFixedSize(36, 36)
        app_icon_lbl.setPixmap(vector_icons.draw_vector_icon("app", 36))
        brand_layout.addWidget(app_icon_lbl)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(1)
        lbl_app_name = QLabel("PowerTimer")
        lbl_app_name.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF;")
        lbl_version = QLabel("Version 2.3.0")
        lbl_version.setStyleSheet("font-size: 11px; color: #64748B;")
        brand_text.addWidget(lbl_app_name)
        brand_text.addWidget(lbl_version)
        brand_layout.addLayout(brand_text)
        layout.addLayout(brand_layout)
        layout.addSpacing(10)

        # Navigation List (Mode Switcher)
        lbl_nav_group = QLabel("SCHEDULE MODE")
        lbl_nav_group.setStyleSheet("font-size: 10px; font-weight: 700; color: #374151; letter-spacing: 0.6px; padding-left: 4px;")
        layout.addWidget(lbl_nav_group)

        self.nav_btns = []
        self.btn_nav_countdown = SidebarNavButton("Countdown Timer", "⏳")
        self.btn_nav_countdown.setChecked(True)
        self.btn_nav_countdown.clicked.connect(lambda: self._switch_mode(0))
        layout.addWidget(self.btn_nav_countdown)
        self.nav_btns.append(self.btn_nav_countdown)

        self.btn_nav_specific = SidebarNavButton("Specific Time", "⏰")
        self.btn_nav_specific.clicked.connect(lambda: self._switch_mode(1))
        layout.addWidget(self.btn_nav_specific)
        self.nav_btns.append(self.btn_nav_specific)

        self.btn_nav_idle = SidebarNavButton("Inactivity / Idle", "💤")
        self.btn_nav_idle.clicked.connect(lambda: self._switch_mode(2))
        layout.addWidget(self.btn_nav_idle)
        self.nav_btns.append(self.btn_nav_idle)

        layout.addSpacing(10)

        # Preferences Toggles
        lbl_pref_group = QLabel("PREFERENCES")
        lbl_pref_group.setStyleSheet("font-size: 10px; font-weight: 700; color: #374151; letter-spacing: 0.6px; padding-left: 4px;")
        layout.addWidget(lbl_pref_group)

        p1 = QHBoxLayout()
        self.switch_force = ModernSwitch(checked=True)
        self.switch_force.toggled.connect(self._update_summary_dock)
        lbl_p1 = QLabel("Force Close Apps")
        lbl_p1.setStyleSheet("font-size: 11px; font-weight: 500; color: #94A3B8;")
        p1.addWidget(self.switch_force)
        p1.addWidget(lbl_p1)
        p1.addStretch()
        layout.addLayout(p1)

        p2 = QHBoxLayout()
        self.switch_sound = ModernSwitch(checked=True)
        self.switch_sound.toggled.connect(self._update_summary_dock)
        lbl_p2 = QLabel("60s Alert Sound")
        lbl_p2.setStyleSheet("font-size: 11px; font-weight: 500; color: #94A3B8;")
        p2.addWidget(self.switch_sound)
        p2.addWidget(lbl_p2)
        p2.addStretch()
        layout.addLayout(p2)

        p3 = QHBoxLayout()
        self.switch_tray = ModernSwitch(checked=False)
        lbl_p3 = QLabel("Minimize to Tray")
        lbl_p3.setStyleSheet("font-size: 11px; font-weight: 500; color: #94A3B8;")
        p3.addWidget(self.switch_tray)
        p3.addWidget(lbl_p3)
        p3.addStretch()
        layout.addLayout(p3)

        layout.addStretch()

        # Bottom Status Card
        status_card = QFrame()
        status_card.setObjectName("StatusCard")
        status_card.setStyleSheet("""
            QFrame#StatusCard {
                background-color: #161924;
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.06);
            }
            QFrame#StatusCard QLabel {
                background: transparent;
                border: none;
            }
        """)
        sc_layout = QVBoxLayout(status_card)
        sc_layout.setContentsMargins(12, 10, 12, 10)
        sc_layout.setSpacing(3)

        sc_top = QHBoxLayout()
        self.lbl_dot_status = QLabel("● Live System")
        self.lbl_dot_status.setStyleSheet("font-size: 11px; font-weight: 700; color: #10B981;")
        sc_top.addWidget(self.lbl_dot_status)
        sc_top.addStretch()

        self.lbl_system_latency = QLabel("Ready")
        self.lbl_system_latency.setStyleSheet("font-size: 11px; font-weight: 700; color: #38BDF8;")
        sc_top.addWidget(self.lbl_system_latency)
        sc_layout.addLayout(sc_top)

        lbl_profile = QLabel("Automated Power")
        lbl_profile.setStyleSheet("font-size: 12px; font-weight: 600; color: #FFFFFF;")
        sc_layout.addWidget(lbl_profile)

        lbl_user = QLabel("● Administrator")
        lbl_user.setStyleSheet("font-size: 10px; color: #10B981;")
        sc_layout.addWidget(lbl_user)

        layout.addWidget(status_card)
        return sidebar

    # -----------------------------------------------------------------------
    # Setup Page (1-2-3 Linear UX Flow)
    # -----------------------------------------------------------------------
    def _build_setup_page(self):
        page = QWidget()
        page.setStyleSheet("background-color: #0C0E14; border-top-right-radius: 18px; border-bottom-right-radius: 18px;")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 20, 28, 22)
        layout.setSpacing(14)

        # Header with Live Clock
        top_bar = QHBoxLayout()
        top_text_v = QVBoxLayout()
        top_text_v.setSpacing(2)

        lbl_crumb = QLabel("POWER SCHEDULER")
        lbl_crumb.setStyleSheet("font-size: 10px; font-weight: 800; color: #38BDF8; letter-spacing: 0.8px;")
        lbl_title = QLabel("System Power Scheduler")
        lbl_title.setStyleSheet("font-size: 22px; font-weight: 800; color: #FFFFFF;")
        lbl_sub = QLabel("Select an action, configure the timer, and let PowerTimer automate your PC.")
        lbl_sub.setStyleSheet("font-size: 13px; color: #8E8E93;")
        top_text_v.addWidget(lbl_crumb)
        top_text_v.addWidget(lbl_title)
        top_text_v.addWidget(lbl_sub)
        top_bar.addLayout(top_text_v)
        top_bar.addStretch()

        self.pill_clock = QLabel("⏱️ 00:00:00")
        self.pill_clock.setFixedHeight(32)
        self.pill_clock.setStyleSheet("""
            background-color: #161926;
            color: #FFFFFF;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            padding: 4px 14px;
            font-size: 12px;
            font-weight: 600;
        """)
        top_bar.addWidget(self.pill_clock, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(top_bar)

        # -------------------------------------------------------------
        # STEP 1: SELECT POWER ACTION
        # -------------------------------------------------------------
        lbl_s1 = QLabel("1. SELECT POWER ACTION")
        lbl_s1.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 0.6px;")
        layout.addWidget(lbl_s1)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)
        self.action_cards = {}
        for aid, info in self.actions_info.items():
            card = ModernActionCard(aid, info["title"], info["desc"], info["color"])
            card.cardSelected.connect(self._on_action_selected)
            self.action_cards[aid] = card
            actions_row.addWidget(card)
        self.action_cards["shutdown"].set_selected(True)
        layout.addLayout(actions_row)

        layout.addSpacing(2)

        # -------------------------------------------------------------
        # STEP 2: CONFIGURE SCHEDULE
        # -------------------------------------------------------------
        lbl_s2 = QLabel("2. CONFIGURE SCHEDULE")
        lbl_s2.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 0.6px;")
        layout.addWidget(lbl_s2)

        self.stacked_timing = QStackedWidget()

        # View 0: Countdown
        self.view_countdown = self._build_countdown_subview()
        self.stacked_timing.addWidget(self.view_countdown)

        # View 1: Specific Time
        self.view_specific = self._build_specific_subview()
        self.stacked_timing.addWidget(self.view_specific)

        # View 2: Inactivity / Idle
        self.view_idle = self._build_idle_subview()
        self.stacked_timing.addWidget(self.view_idle)

        layout.addWidget(self.stacked_timing)
        layout.addSpacing(2)

        # -------------------------------------------------------------
        # STEP 3: REVIEW & START DOCK
        # -------------------------------------------------------------
        dock = QFrame()
        dock.setObjectName("BottomDock")
        dock.setFixedHeight(74)
        dock.setStyleSheet("""
            QFrame#BottomDock {
                background-color: #121522;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
            }
            QFrame#BottomDock QLabel {
                background: transparent;
                border: none;
            }
        """)
        dock_lay = QHBoxLayout(dock)
        dock_lay.setContentsMargins(18, 10, 18, 10)
        dock_lay.setSpacing(16)

        self.dock_icon = QLabel()
        self.dock_icon.setFixedSize(40, 40)
        self.dock_icon.setPixmap(vector_icons.draw_vector_icon("shutdown", 40))
        dock_lay.addWidget(self.dock_icon)

        sum_v = QVBoxLayout()
        sum_v.setSpacing(2)
        self.lbl_dock_title = QLabel("Shutdown PC in 1 hour 30 minutes")
        self.lbl_dock_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF;")
        self.lbl_dock_sub = QLabel("Executes at 00:00:00 • Force close enabled • Warning alert 60s before")
        self.lbl_dock_sub.setStyleSheet("font-size: 11px; color: #94A3B8;")
        sum_v.addWidget(self.lbl_dock_title)
        sum_v.addWidget(self.lbl_dock_sub)
        dock_lay.addLayout(sum_v)
        dock_lay.addStretch()

        btn_clear = QPushButton("✕ Clear")
        btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear.setFixedSize(84, 42)
        btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #181B28;
                color: #94A3B8;
                font-size: 13px;
                font-weight: 600;
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            QPushButton:hover {
                background-color: #222638;
                color: #FFFFFF;
            }
        """)
        btn_clear.clicked.connect(self._clear_presets)
        dock_lay.addWidget(btn_clear)

        self.btn_start = QPushButton("▶  Start Schedule")
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.setFixedSize(175, 42)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #3B82F6);
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 700;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1D4ED8, stop:1 #2563EB);
            }
        """)
        self.btn_start.clicked.connect(self.start_schedule)
        dock_lay.addWidget(self.btn_start)

        layout.addWidget(dock)
        return page

    def _build_countdown_subview(self):
        card = QFrame()
        card.setObjectName("CountdownCard")
        card.setFixedHeight(94)
        card.setStyleSheet("""
            QFrame#CountdownCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #141724, stop:1 #10121C);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
            }
            QFrame#CountdownCard QLabel {
                background: transparent;
                border: none;
            }
        """)
        tc_layout = QHBoxLayout(card)
        tc_layout.setContentsMargins(20, 10, 20, 10)
        tc_layout.setSpacing(20)
        tc_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Dials
        spin_box = QHBoxLayout()
        spin_box.setSpacing(10)
        spin_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.spin_hours = self._create_dial_spinner(0, 99, 1, "HOURS")
        self.spin_minutes = self._create_dial_spinner(0, 59, 30, "MINUTES")
        self.spin_seconds = self._create_dial_spinner(0, 59, 0, "SECONDS")

        spin_box.addLayout(self.spin_hours[0])
        spin_box.addLayout(self.spin_minutes[0])
        spin_box.addLayout(self.spin_seconds[0])
        tc_layout.addLayout(spin_box)

        # Divider
        t_sep = QFrame()
        t_sep.setFixedSize(1, 48)
        t_sep.setStyleSheet("background-color: rgba(255, 255, 255, 0.07);")
        tc_layout.addWidget(t_sep)

        # Quick Presets
        presets_v = QVBoxLayout()
        presets_v.setSpacing(4)
        presets_v.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        lbl_pr = QLabel("FAST PRESETS")
        lbl_pr.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748B; letter-spacing: 0.5px; background: transparent; border: none;")
        presets_v.addWidget(lbl_pr)

        pr_row = QHBoxLayout()
        pr_row.setSpacing(6)
        presets = [("+15m", 0, 15), ("+30m", 0, 30), ("+1h", 1, 0), ("+2h", 2, 0), ("+4h", 4, 0)]
        for text, h_add, m_add in presets:
            b = QPushButton(text)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setFixedSize(50, 30)
            b.setStyleSheet("""
                QPushButton {
                    background-color: #1A1E2D;
                    color: #38BDF8;
                    font-size: 12px;
                    font-weight: 700;
                    border-radius: 8px;
                    border: 1px solid rgba(56, 189, 248, 0.2);
                }
                QPushButton:hover {
                    background-color: #2563EB;
                    color: #FFFFFF;
                }
            """)
            b.clicked.connect(lambda ch, h=h_add, m=m_add: self._add_preset(h, m))
            pr_row.addWidget(b)

        b_rst = QPushButton("Reset")
        b_rst.setCursor(Qt.CursorShape.PointingHandCursor)
        b_rst.setFixedSize(52, 30)
        b_rst.setStyleSheet("""
            QPushButton {
                background-color: #1E171E;
                color: #EF4444;
                font-size: 11px;
                font-weight: 700;
                border-radius: 8px;
                border: 1px solid rgba(239, 68, 68, 0.25);
            }
            QPushButton:hover {
                background-color: #DC2626;
                color: #FFFFFF;
            }
        """)
        b_rst.clicked.connect(self._reset_inputs)
        pr_row.addWidget(b_rst)

        presets_v.addLayout(pr_row)
        tc_layout.addLayout(presets_v)
        tc_layout.addStretch()

        return card

    def _create_dial_spinner(self, min_val, max_val, init_val, label):
        layout = QVBoxLayout()
        layout.setSpacing(3)

        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(init_val)
        spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spin.setFixedSize(68, 42)
        spin.setStyleSheet("""
            QSpinBox {
                background-color: #1A1D2A;
                color: #FFFFFF;
                font-size: 18px;
                font-weight: 700;
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.09);
            }
            QSpinBox:focus {
                border: 1px solid #3B82F6;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 0px;
            }
        """)
        spin.valueChanged.connect(self._update_summary_dock)

        lbl = QLabel(label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 9px; font-weight: 700; color: #64748B; letter-spacing: 0.5px;")

        layout.addWidget(spin)
        layout.addWidget(lbl)
        return layout, spin

    def _build_specific_subview(self):
        card = QFrame()
        card.setObjectName("SpecificCard")
        card.setFixedHeight(94)
        card.setStyleSheet("""
            QFrame#SpecificCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #141724, stop:1 #10121C);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
            }
            QFrame#SpecificCard QLabel {
                background: transparent;
                border: none;
            }
        """)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        lbl = QLabel("Target Execution Time:")
        lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #FFFFFF;")
        layout.addWidget(lbl)

        self.time_picker = QTimeEdit()
        self.time_picker.setTime(QTime.currentTime().addSecs(3600))
        self.time_picker.setDisplayFormat("HH:mm:ss")
        self.time_picker.setFixedHeight(40)
        self.time_picker.setStyleSheet("""
            QTimeEdit {
                background-color: #1A1D2A;
                color: #FFFFFF;
                font-size: 16px;
                font-weight: 700;
                border-radius: 10px;
                padding: 4px 12px;
                border: 1px solid rgba(255, 255, 255, 0.09);
            }
            QTimeEdit:focus {
                border: 1px solid #3B82F6;
            }
            QTimeEdit::up-button, QTimeEdit::down-button {
                width: 0px;
            }
        """)
        self.time_picker.timeChanged.connect(self._update_summary_dock)
        layout.addWidget(self.time_picker)

        self.lbl_specific_summary = QLabel("Executes Today at ...")
        self.lbl_specific_summary.setStyleSheet("font-size: 13px; color: #38BDF8; font-weight: 600;")
        layout.addWidget(self.lbl_specific_summary)
        layout.addStretch()

        return card

    def _build_idle_subview(self):
        card = QFrame()
        card.setObjectName("IdleCard")
        card.setFixedHeight(94)
        card.setStyleSheet("""
            QFrame#IdleCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #141724, stop:1 #10121C);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
            }
            QFrame#IdleCard QLabel {
                background: transparent;
                border: none;
            }
        """)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(18)

        lbl = QLabel("Trigger after inactivity:")
        lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #FFFFFF;")
        layout.addWidget(lbl)

        self.slider_idle = QSlider(Qt.Orientation.Horizontal)
        self.slider_idle.setRange(5, 120)
        self.slider_idle.setValue(15)
        self.slider_idle.setFixedWidth(200)
        self.slider_idle.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: #1F2230;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #3B82F6;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #FFFFFF;
                width: 18px;
                margin-top: -6px;
                margin-bottom: -6px;
                border-radius: 9px;
            }
        """)
        self.slider_idle.valueChanged.connect(self._on_idle_slider)
        layout.addWidget(self.slider_idle)

        self.lbl_idle_mins = QLabel("15 min")
        self.lbl_idle_mins.setStyleSheet("font-size: 14px; font-weight: 700; color: #38BDF8;")
        layout.addWidget(self.lbl_idle_mins)

        self.lbl_live_idle = QLabel("Current idle: 0s")
        self.lbl_live_idle.setStyleSheet("font-size: 12px; color: #8E8E93;")
        layout.addWidget(self.lbl_live_idle)
        layout.addStretch()

        return card

    # -----------------------------------------------------------------------
    # Running Page (Active Countdown View)
    # -----------------------------------------------------------------------
    def _build_running_page(self):
        page = QWidget()
        page.setStyleSheet("background-color: #0C0E14; border-top-right-radius: 18px; border-bottom-right-radius: 18px;")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 20, 28, 26)
        layout.setSpacing(18)

        # Top Bar
        top_bar = QHBoxLayout()
        top_text_v = QVBoxLayout()
        top_text_v.setSpacing(2)

        lbl_crumb = QLabel("SCHEDULE MONITOR")
        lbl_crumb.setStyleSheet("font-size: 10px; font-weight: 800; color: #10B981; letter-spacing: 0.8px;")
        lbl_title = QLabel("Automated Task Active")
        lbl_title.setStyleSheet("font-size: 22px; font-weight: 800; color: #FFFFFF;")
        lbl_sub = QLabel("PowerTimer is monitoring the countdown. Your PC is safe and on schedule.")
        lbl_sub.setStyleSheet("font-size: 13px; color: #8E8E93;")
        top_text_v.addWidget(lbl_crumb)
        top_text_v.addWidget(lbl_title)
        top_text_v.addWidget(lbl_sub)
        top_bar.addLayout(top_text_v)
        top_bar.addStretch()

        self.running_status_badge = QLabel("●  SCHEDULE ACTIVE")
        self.running_status_badge.setFixedHeight(32)
        self.running_status_badge.setStyleSheet("""
            background-color: rgba(16, 185, 129, 0.15);
            color: #10B981;
            border: 1px solid rgba(16, 185, 129, 0.35);
            border-radius: 12px;
            padding: 4px 14px;
            font-size: 12px;
            font-weight: 800;
        """)
        top_bar.addWidget(self.running_status_badge, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(top_bar)

        # Hero Card for Running Timer
        hero_card = QFrame()
        hero_card.setObjectName("RunningHero")
        hero_card.setStyleSheet("""
            QFrame#RunningHero {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #161A28, stop:1 #10121C);
                border: 1.5px solid rgba(59, 130, 246, 0.35);
                border-radius: 20px;
            }
            QFrame#RunningHero QLabel {
                background: transparent;
                border: none;
            }
        """)
        hero_layout = QVBoxLayout(hero_card)
        hero_layout.setContentsMargins(36, 28, 36, 28)
        hero_layout.setSpacing(18)
        hero_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Action Badge & Title
        badge_row = QHBoxLayout()
        badge_row.setSpacing(14)
        badge_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.running_action_icon = QLabel()
        self.running_action_icon.setFixedSize(54, 54)
        self.running_action_icon.setPixmap(vector_icons.draw_vector_icon("shutdown", 54))
        badge_row.addWidget(self.running_action_icon)

        title_v = QVBoxLayout()
        title_v.setSpacing(2)
        self.lbl_running_action = QLabel("Shutdown Scheduled")
        self.lbl_running_action.setStyleSheet("font-size: 24px; font-weight: 800; color: #FFFFFF;")
        self.lbl_running_target = QLabel("Target Execution: Today at 23:45:00")
        self.lbl_running_target.setStyleSheet("font-size: 13px; color: #94A3B8; font-weight: 500;")
        title_v.addWidget(self.lbl_running_action)
        title_v.addWidget(self.lbl_running_target)
        badge_row.addLayout(title_v)

        hero_layout.addLayout(badge_row)
        hero_layout.addSpacing(6)

        # Giant Digital Clock
        clock_v = QVBoxLayout()
        clock_v.setSpacing(2)
        clock_v.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_big_clock = QLabel("01 : 30 : 00")
        self.lbl_big_clock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_big_clock.setStyleSheet("""
            font-size: 60px;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: 3px;
        """)
        clock_v.addWidget(self.lbl_big_clock)

        lbl_clock_sub = QLabel("HOURS          MINUTES          SECONDS")
        lbl_clock_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_clock_sub.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 2px;")
        clock_v.addWidget(lbl_clock_sub)

        hero_layout.addLayout(clock_v)
        hero_layout.addSpacing(6)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.setValue(1000)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.08);
                border-radius: 4px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #38BDF8);
                border-radius: 4px;
            }
        """)
        hero_layout.addWidget(self.progress_bar)

        # Status Tags
        tags_row = QHBoxLayout()
        tags_row.setSpacing(12)
        tags_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        def make_tag(txt, color="#38BDF8"):
            lbl = QLabel(txt)
            lbl.setStyleSheet(f"""
                background-color: rgba(255, 255, 255, 0.04);
                color: {color};
                font-size: 11px;
                font-weight: 600;
                padding: 4px 12px;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.06);
            """)
            return lbl

        self.tag_force = make_tag("⚡ Force Close Active", "#10B981")
        self.tag_sound = make_tag("🔔 Warning Chime at 60s", "#F59E0B")
        tag_safe = make_tag("🛡️ Crash-Proof Safe Engine", "#38BDF8")

        tags_row.addWidget(self.tag_force)
        tags_row.addWidget(self.tag_sound)
        tags_row.addWidget(tag_safe)
        hero_layout.addLayout(tags_row)

        layout.addWidget(hero_card)

        # Bottom Buttons Dock
        btn_dock = QHBoxLayout()
        btn_dock.setSpacing(14)
        btn_dock.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_minimize_tray = QPushButton("📥  Minimize to Tray")
        btn_minimize_tray.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_minimize_tray.setFixedSize(180, 46)
        btn_minimize_tray.setStyleSheet("""
            QPushButton {
                background-color: #161A28;
                color: #94A3B8;
                font-size: 13px;
                font-weight: 600;
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            QPushButton:hover {
                background-color: #202538;
                color: #FFFFFF;
            }
        """)
        btn_minimize_tray.clicked.connect(self.hide)
        btn_dock.addWidget(btn_minimize_tray)

        btn_cancel = QPushButton("⏹  Cancel Schedule")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setFixedSize(220, 46)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #DC2626, stop:1 #EF4444);
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 700;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #B91C1C, stop:1 #DC2626);
            }
        """)
        btn_cancel.clicked.connect(self.cancel_schedule)
        btn_dock.addWidget(btn_cancel)

        layout.addLayout(btn_dock)
        return page

    # -----------------------------------------------------------------------
    # Dynamic Updates & Controls
    # -----------------------------------------------------------------------
    def _switch_mode(self, mode_idx):
        self.schedule_mode = mode_idx
        self.stacked_timing.setCurrentIndex(mode_idx)
        for i, btn in enumerate(self.nav_btns):
            btn.setChecked(i == mode_idx)
        self._update_summary_dock()

    def _on_action_selected(self, action_id):
        self.selected_action = action_id
        for aid, card in self.action_cards.items():
            card.set_selected(aid == action_id)
        self._update_summary_dock()

    def _add_preset(self, h_add, m_add):
        curr_h = self.spin_hours[1].value()
        curr_m = self.spin_minutes[1].value()
        new_m = curr_m + m_add
        carry_h = new_m // 60
        new_m = new_m % 60
        new_h = min(99, curr_h + h_add + carry_h)
        self.spin_hours[1].setValue(new_h)
        self.spin_minutes[1].setValue(new_m)
        self._update_summary_dock()

    def _clear_presets(self):
        self.spin_hours[1].setValue(0)
        self.spin_minutes[1].setValue(0)
        self.spin_seconds[1].setValue(0)
        self._update_summary_dock()

    def _reset_inputs(self):
        self.spin_hours[1].setValue(1)
        self.spin_minutes[1].setValue(30)
        self.spin_seconds[1].setValue(0)
        self._update_summary_dock()

    def _on_idle_slider(self, val):
        self.lbl_idle_mins.setText(f"{val} min")
        self._update_summary_dock()

    def _update_summary_dock(self):
        info = self.actions_info.get(self.selected_action, self.actions_info["shutdown"])
        act_title = info["title"]
        self.dock_icon.setPixmap(vector_icons.draw_vector_icon(self.selected_action, 40))

        force_str = "Force close enabled" if self.switch_force.isChecked() else "Normal close"
        sound_str = "Warning alert 60s before" if self.switch_sound.isChecked() else "Silent"

        if self.schedule_mode == 0:
            h = self.spin_hours[1].value()
            m = self.spin_minutes[1].value()
            s = self.spin_seconds[1].value()
            tot = h * 3600 + m * 60 + s
            target = datetime.datetime.now() + datetime.timedelta(seconds=tot)
            time_str = f"{h}h {m}m" if h > 0 else f"{m}m {s}s"
            self.lbl_dock_title.setText(f"{act_title} in {time_str}")
            self.lbl_dock_sub.setText(f"Executes at {target.strftime('%H:%M:%S')} • {force_str} • {sound_str}")

        elif self.schedule_mode == 1:
            t = self.time_picker.time()
            now = datetime.datetime.now()
            target_dt = now.replace(hour=t.hour(), minute=t.minute(), second=t.second(), microsecond=0)
            if target_dt <= now:
                target_dt += datetime.timedelta(days=1)
                day_str = "Tomorrow"
            else:
                day_str = "Today"
            diff = int((target_dt - now).total_seconds())
            dh, dm = diff // 3600, (diff % 3600) // 60
            self.lbl_dock_title.setText(f"{act_title} at {target_dt.strftime('%H:%M:%S')}")
            self.lbl_dock_sub.setText(f"{day_str} in {dh}h {dm}m • {force_str} • {sound_str}")
            self.lbl_specific_summary.setText(f"Executes {day_str} at {target_dt.strftime('%H:%M:%S')} (in {dh}h {dm}m)")

        elif self.schedule_mode == 2:
            mins = self.slider_idle.value()
            self.lbl_dock_title.setText(f"{act_title} after {mins}m inactivity")
            self.lbl_dock_sub.setText(f"Monitors keyboard & mouse • {force_str} • {sound_str}")

    # -----------------------------------------------------------------------
    # Schedule Execution & Control
    # -----------------------------------------------------------------------
    def start_schedule(self):
        now = datetime.datetime.now()

        if self.schedule_mode == 0:
            h = self.spin_hours[1].value()
            m = self.spin_minutes[1].value()
            s = self.spin_seconds[1].value()
            tot = h * 3600 + m * 60 + s
            if tot <= 0:
                QMessageBox.warning(self, "Invalid Time", "Please configure a timer duration greater than 0.")
                return
            self.total_seconds_duration = tot
            self.target_datetime = now + datetime.timedelta(seconds=tot)

        elif self.schedule_mode == 1:
            t = self.time_picker.time()
            target_dt = now.replace(hour=t.hour(), minute=t.minute(), second=t.second(), microsecond=0)
            if target_dt <= now:
                target_dt += datetime.timedelta(days=1)
            self.target_datetime = target_dt
            self.total_seconds_duration = int((target_dt - now).total_seconds())

        elif self.schedule_mode == 2:
            self.total_seconds_duration = self.slider_idle.value() * 60
            self.target_datetime = None

        self.is_scheduled = True
        self.has_warned_user = False

        # Update Running Page Details
        info = self.actions_info[self.selected_action]
        self.running_action_icon.setPixmap(vector_icons.draw_vector_icon(self.selected_action, 54))
        self.lbl_running_action.setText(f"{info['title']} Scheduled")

        if self.target_datetime:
            self.lbl_running_target.setText(f"Target Execution: {self.target_datetime.strftime('%Y-%m-%d at %H:%M:%S')}")
        else:
            self.lbl_running_target.setText(f"Trigger: When system is idle for {self.slider_idle.value()} minutes")

        self.tag_force.setText("⚡ Force Close Active" if self.switch_force.isChecked() else "Normal Close")
        self.tag_sound.setText("🔔 Warning Chime at 60s" if self.switch_sound.isChecked() else "Silent Mode")

        # Switch to Running View!
        self.main_stack.setCurrentIndex(1)
        self.heartbeat_timer.start(1000)
        self._on_heartbeat_tick()

        if self.switch_tray.isChecked():
            self.hide()
            if self.tray_icon.isSystemTrayAvailable():
                self.tray_icon.showMessage(
                    "PowerTimer Active",
                    f"Scheduled {info['title']} successfully.",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )

    def cancel_schedule(self):
        self.is_scheduled = False
        self.heartbeat_timer.stop()

        try:
            subprocess.run(["shutdown", "/a"], creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True)
        except Exception:
            pass

        # Return to Setup View!
        self.main_stack.setCurrentIndex(0)
        self.pill_clock.setText("⏱️ 00:00:00")
        self._update_summary_dock()

    def _on_heartbeat_tick(self):
        now = datetime.datetime.now()
        now_str = now.strftime("%H:%M:%S")

        if not self.is_scheduled:
            self.pill_clock.setText(f"⏱️ {now_str}")
            return

        if self.schedule_mode in (0, 1) and self.target_datetime:
            rem = int((self.target_datetime - now).total_seconds())
            if rem <= 0:
                self.lbl_big_clock.setText("00 : 00 : 00")
                self._execute_action()
                return

            rh, rm, rs = rem // 3600, (rem % 3600) // 60, rem % 60
            clock_str = f"{rh:02d} : {rm:02d} : {rs:02d}"
            self.lbl_big_clock.setText(clock_str)
            self.pill_clock.setText(f"⏱️ {rh:02d}:{rm:02d}:{rs:02d}")

            if self.total_seconds_duration > 0:
                pct = int((rem / self.total_seconds_duration) * 1000)
                self.progress_bar.setValue(max(0, min(1000, pct)))

            if rem <= 60 and not self.has_warned_user and self.switch_sound.isChecked():
                self._trigger_warning(rem)

    def _get_system_idle_seconds(self) -> float:
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [('cbSize', ctypes.c_uint), ('dwTime', ctypes.c_uint)]
        try:
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
            millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
            return max(0.0, millis / 1000.0)
        except Exception:
            return 0.0

    def _on_idle_tick(self):
        idle_s = int(self._get_system_idle_seconds())
        threshold_s = self.slider_idle.value() * 60
        m, s = divmod(idle_s, 60)
        self.lbl_live_idle.setText(f"Current idle: {m}m {s}s")

        if self.is_scheduled and self.schedule_mode == 2:
            rem = max(0, threshold_s - idle_s)
            rh, rm, rs = rem // 3600, (rem % 3600) // 60, rem % 60
            self.lbl_big_clock.setText(f"{rh:02d} : {rm:02d} : {rs:02d}")
            self.pill_clock.setText(f"⏱️ {rh:02d}:{rm:02d}:{rs:02d}")

            if threshold_s > 0:
                pct = int((rem / threshold_s) * 1000)
                self.progress_bar.setValue(max(0, min(1000, pct)))

            if rem <= 60 and not self.has_warned_user and self.switch_sound.isChecked():
                self._trigger_warning(rem)

            if idle_s >= threshold_s:
                self._execute_action()

    def _trigger_warning(self, seconds_left):
        self.has_warned_user = True
        try:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass
        if self.tray_icon.isSystemTrayAvailable():
            act_title = self.actions_info[self.selected_action]["title"]
            self.tray_icon.showMessage(
                "⚠️ PowerTimer Alert",
                f"Action '{act_title}' will execute in {seconds_left} seconds!",
                QSystemTrayIcon.MessageIcon.Warning,
                4000
            )

    def _execute_action(self):
        self.heartbeat_timer.stop()
        self.is_scheduled = False
        force = self.switch_force.isChecked()
        act = self.selected_action

        try:
            if act == "shutdown":
                cmd = ["shutdown", "/s", "/t", "0"]
                if force:
                    cmd.append("/f")
                subprocess.run(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
            elif act == "restart":
                cmd = ["shutdown", "/r", "/t", "0"]
                if force:
                    cmd.append("/f")
                subprocess.run(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
            elif act == "sleep":
                try:
                    ctypes.windll.powrprof.SetSuspendState(0, 1, 0)
                except Exception:
                    subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], creationflags=subprocess.CREATE_NO_WINDOW)
            elif act == "hibernate":
                subprocess.run(["shutdown", "/h"], creationflags=subprocess.CREATE_NO_WINDOW)
            elif act == "lock":
                ctypes.windll.user32.LockWorkStation()
            elif act == "display_off":
                ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)
        except Exception as e:
            print(f"Action error: {e}")
        finally:
            self.cancel_schedule()

    def _toggle_zoom(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    # -----------------------------------------------------------------------
    # System Tray
    # -----------------------------------------------------------------------
    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon = QIcon(vector_icons.draw_vector_icon("app", 32))
        self.setWindowIcon(icon)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("PowerTimer - macOS Dark Edition")

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #161824;
                color: #FFFFFF;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 6px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #2563EB;
            }
        """)
        menu.addAction("Open PowerTimer", self.show_and_activate)
        menu.addAction("Cancel Schedule", self.cancel_schedule)
        menu.addSeparator()
        menu.addAction("Exit", self.safe_quit)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.show_and_activate()

    def show_and_activate(self):
        self.showNormal()
        self.activateWindow()

    def safe_quit(self):
        if self.is_scheduled:
            self.cancel_schedule()
        QApplication.quit()


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------
def main():
    try:
        myappid = 'antigravity.powertimer.macdark.2.3'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("PowerTimer")

    # Load Google Sans Fonts
    for font_name in ["GoogleSans-Regular.ttf", "GoogleSans-Medium.ttf", "GoogleSans-Bold.ttf"]:
        font_path = resource_path(os.path.join("fonts", font_name))
        if os.path.exists(font_path):
            QFontDatabase.addApplicationFont(font_path)

    app.setFont(QFont("Google Sans", 10))
    app.setStyleSheet("""
        QLabel {
            background-color: transparent;
            background: transparent;
            border: none;
        }
        QPushButton:focus {
            outline: none;
        }
    """)

    window = ModernPowerTimer()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
