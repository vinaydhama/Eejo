
import sys
import os
import json
import math
import subprocess
import vlc
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtCore import QUrl, QByteArray

# ------------------ CONFIGURE THESE ------------------
RTSP_URL = "rtsp://user:pass@192.168.0.102:554/Streaming/Channels/101"  # <- your camera URL
REST_URL = "http://192.168.0.101:5002/SetLiveHeatCommands?CmdName=LiveBoard"  # <- your REST endpoint
POLL_MS = 500                       # poll every 0.5 seconds
ASPECT_RATIO = (16, 9)              # video area aspect ratio
PANEL_W = 600                       # data panel width
PANEL_H = 800                       # data panel height


# --- Windows capture mode & optional cropping (NEW) ---
# "gfxcapture"     -> Windows.Graphics.Capture source (records even when minimized/occluded; Win10+)
# "gdigrab_title"  -> gdigrab capture of the window by title (requires the window to stay visible)
# "gdigrab_region" -> gdigrab capture of a fixed desktop region
WINDOWS_CAPTURE_MODE = "gfxcapture"

# If True, when capturing the whole app window (gfxcapture/gdigrab_title), crop to just the VLC
# video surface area inside your window. If False, record the full app window.
CROP_TO_VIDEO_SURFACE = False


# --- Recording config ---
FFMPEG_EXE = "ffmpeg"               # or r"C:\ffmpeg\bin\ffmpeg.exe"
REC_FPS = 30
REC_PRESET = "veryfast"             # ultrafast, superfast, veryfast, faster, fast, medium ...
REC_CRF = 18                        # 18=visually lossless-ish; higher=smaller file
USE_DPI_SCALING = True              # multiply Qt logical pixels by screen devicePixelRatio on Windows
AUDIO_DEVICE_NAME = None            # e.g. "virtual-audio-capturer" or "Stereo Mix (Realtek(R) Audio)"
# -----------------------------------------------------

# ---- THEME / STYLE CONFIG (dark overlay rows) ----
ROW_STYLE = {
    # Typography
    "board_font": 16,         # px
    "name_font": 18,          # px
    "time_font": 18,          # px
    "font_family": "Segoe UI",

    # Colors
    "board_color": "rgba(255,255,255,230)",
    "name_color":  "rgba(255,255,255,230)",
    "time_color":  "rgba(255,255,255,230)",

    # Row background (hover-friendly)
    "row_bg": "rgba(255,255,255,0)",            # fully transparent
    "row_bg_hover": "rgba(255,255,255,20)",     # subtle hover tint
    "row_bg_selected": "rgba(255,255,255,40)",  # if you add selection later

    # Separators
    "sep_color": "rgba(255,255,255,50)",
    "sep_height": 1,

    # Spacing / widths
    "row_padding_v": 10,        # inner vertical padding (content padding)
    "row_padding_h": 12,        # inner horizontal padding
    "time_min_w": 100,          # a safe minimum; real width is computed by font metrics
    "board_min_w": 28,
    "board_max_w": 48,
}

def fmt_time_sec(t):
    """Format seconds -> mm:ss.mmm; return '–' if <=0/invalid/None."""
    try:
        if t is None:
            return "–"
        t = float(t)  # allow strings
        if math.isnan(t) or t <= 0:
            return "–"
        m = int(t // 60)
        s = int(t % 60)
        ms = int(round((t - int(t)) * 1000))
        return f"{m:02d}:{s:02d}.{ms:03d}"
    except Exception:
        return "–"


class RowItem(QtWidgets.QWidget):
    """A single transparent row: Board | Swimmer | Time (styleable)."""
    def __init__(self, board_text: str, name_text: str, time_text: str, parent=None):
        super().__init__(parent)
        self.setObjectName("RowItem")

        # Compose stylesheet from the theme config
        ss = f"""
            QWidget#RowItem {{
                background: {ROW_STYLE['row_bg']};
            }}
            QWidget#RowItem:hover {{
                background: {ROW_STYLE['row_bg_hover']};
            }}
            QLabel#Board {{
                color: {ROW_STYLE['board_color']};
                font: 700 {ROW_STYLE['board_font']}px "{ROW_STYLE['font_family']}";
            }}
            QLabel#Name {{
                color: {ROW_STYLE['name_color']};
                font: 600 {ROW_STYLE['name_font']}px "{ROW_STYLE['font_family']}";
            }}
            QLabel#Time {{
                color: {ROW_STYLE['time_color']};
                font: 600 {ROW_STYLE['time_font']}px "{ROW_STYLE['font_family']}";
            }}
        """
        self.setStyleSheet(ss)

        h = QtWidgets.QHBoxLayout(self)
        # a bit extra right padding to protect the time from edge clipping
        h.setContentsMargins(ROW_STYLE["row_padding_h"], ROW_STYLE["row_padding_v"],
                             ROW_STYLE["row_padding_h"] + 6, ROW_STYLE["row_padding_v"])
        h.setSpacing(12)

        self.lab_board = QtWidgets.QLabel(board_text)
        self.lab_board.setObjectName("Board")

        self.lab_name = QtWidgets.QLabel(name_text)
        self.lab_name.setObjectName("Name")
        self.lab_name.setWordWrap(False)
        self.lab_name.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        self.lab_time = QtWidgets.QLabel(time_text)
        self.lab_time.setObjectName("Time")
        self.lab_time.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.lab_time.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        # do not set a maximum; actual width is fixed later by _ensure_time_width()
        self.lab_time.setMinimumWidth(ROW_STYLE["time_min_w"])

        # Prevent text selection/edit
        for lab in (self.lab_board, self.lab_name, self.lab_time):
            lab.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)

        # Fixed-ish board widths, flexible name
        self.lab_board.setMinimumWidth(ROW_STYLE["board_min_w"])
        self.lab_board.setMaximumWidth(ROW_STYLE["board_max_w"])

        h.addWidget(self.lab_board, 0)
        h.addWidget(self.lab_name, 1)   # stretch name
        h.addWidget(self.lab_time, 0)

    # ===== Name eliding to avoid collision with the time column =====
    def elide_name_to_fit(self, time_width: int, board_width: int, left_pad: int, right_pad: int, gap_px: int = 12):
        """Elide the name so it never collides with the time label."""
        total_w = self.width()
        if total_w <= 0:
            return
        avail = total_w - (left_pad + board_width + gap_px + time_width + right_pad)
        if avail <= 20:
            avail = 20
        fm = QtGui.QFontMetrics(self.lab_name.font())
        text = self.lab_name.text()
        elided = fm.elidedText(text, QtCore.Qt.ElideRight, int(avail))
        if elided != text:
            self.lab_name.setText(elided)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        # Re-elide on every size change.
        t_w = self.lab_time.width() if self.lab_time.width() > 0 else self.lab_time.minimumWidth()
        left_pad  = ROW_STYLE["row_padding_h"]
        right_pad = ROW_STYLE["row_padding_h"] + 6
        b_w = self.lab_board.width()
        self.elide_name_to_fit(time_width=t_w, board_width=b_w, left_pad=left_pad, right_pad=right_pad)


class RowWrapper(QtWidgets.QWidget):
    """
    Hosts one RowItem and an optional separator.
    We animate its left content margin via the custom 'offset' property
    to create a slide-in effect that doesn't fight the layout.
    """
    def __init__(self, parent=None, initial_offset=0):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._offset = int(initial_offset)
        self.vbox = QtWidgets.QVBoxLayout(self)
        # Start with initial left margin (offset) so it appears shifted
        self.vbox.setContentsMargins(self._offset, 0, 0, 0)
        self.vbox.setSpacing(0)

    def getOffset(self):
        return self._offset

    def setOffset(self, value):
        self._offset = int(value)
        self.vbox.setContentsMargins(self._offset, 0, 0, 0)

    offset = QtCore.pyqtProperty(int, fget=getOffset, fset=setOffset)


class DataPanel(QtWidgets.QFrame):
    """Right-center floating panel with rows + animations (no table)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DataPanel")

        # Panel ~20% opaque, rows transparent
        self.setStyleSheet("""
            QFrame#DataPanel {
                background: rgba(0, 0, 0, 51);  /* ~20% opacity */
                border-radius: 6px;
                border: 1px solid rgba(255,255,255,70);
            }
            QLabel#Title { color:#fff; font: 700 16px "Segoe UI"; }
            QLabel#Spinner { color:#9ad; font: 16px "Segoe UI"; }
            QScrollBar:vertical { background: transparent; width: 12px; }
            QScrollBar::handle:vertical { background: rgba(255,255,255,60); border-radius: 4px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        self.setFixedSize(PANEL_W, PANEL_H)

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(8)

        # Header: title + spinner
        header = QtWidgets.QHBoxLayout()
        self.title = QtWidgets.QLabel("Live Data")
        self.title.setObjectName("Title")
        self.spinner = QtWidgets.QLabel("⟳")
        self.spinner.setObjectName("Spinner")
        header.addWidget(self.title)
        header.addStretch(1)
        header.addWidget(self.spinner)
        outer.addLayout(header)

        # Scroll area to host rows
        self.scroll = QtWidgets.QScrollArea(self)
        self.scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; }")
        outer.addWidget(self.scroll, 1)

        # Container inside scroll
        self.rows_container = QtWidgets.QWidget()
        self.rows_container.setObjectName("RowsContainer")
        self.rows_container.setStyleSheet("QWidget#RowsContainer { background: transparent; }")
        self.rows_layout = QtWidgets.QVBoxLayout(self.rows_container)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(8)   # OUTER SPACING between rows
        self.scroll.setWidget(self.rows_container)

        # Animations (panel-level)
        self.opacity = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity)
        self.fade = QtCore.QPropertyAnimation(self.opacity, b"opacity", self)
        self.fade.setDuration(300)
        self.fade.setStartValue(0.0)
        self.fade.setEndValue(1.0)
        self.fade.setEasingCurve(QtCore.QEasingCurve.InOutQuad)

        self.slide = QtCore.QPropertyAnimation(self, b"geometry", self)
        self.slide.setDuration(300)
        # Panel slide with subtle bounce
        curve_p = QtCore.QEasingCurve(QtCore.QEasingCurve.OutBack)
        curve_p.setOvershoot(1.12)  # gentle
        self.slide.setEasingCurve(curve_p)

        # Spinner
        self._spin_i = 0
        self.spin_timer = QtCore.QTimer(self)
        self.spin_timer.timeout.connect(self._tick_spinner)

        # Row animations container
        self._row_anims = []

        # --- Time-only update & animation bookkeeping ---
        self._row_time_labels = []                    # list of QLabel refs (time)
        self._time_anims = []                         # list of running animations
        self._time_anim_running = False
        self._time_anim_deadline = QtCore.QElapsedTimer()
        self._last_event_sig = None                   # (EventID, HeatName, row_count)

    def _tick_spinner(self):
        glyphs = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self._spin_i = (self._spin_i + 1) % len(glyphs)
        self.spinner.setText(glyphs[self._spin_i])

    def start_spinner(self):
        if not self.spin_timer.isActive():
            self._spin_i = 0
            self.spin_timer.start(90)

    def stop_spinner(self):
        if self.spin_timer.isActive():
            self.spin_timer.stop()
        self.spinner.setText("")

    # ----- Per-row animation helpers -----
    def _stop_row_anims(self):
        for anim in self._row_anims:
            try:
                anim.stop()
            except Exception:
                pass
        self._row_anims.clear()

    def _animate_row_in(self, wrapper: RowWrapper, index: int,
                        dx: int = 48, dur_ms: int = 240, fade_ms: int = 180, stagger_ms: int = 80):
        """Slide (via margin offset) + fade a single row wrapper in, staggered, with bounce."""
        wrapper.setOffset(dx)

        eff = QtWidgets.QGraphicsOpacityEffect(wrapper)
        eff.setOpacity(0.0)
        wrapper.setGraphicsEffect(eff)

        fade = QtCore.QPropertyAnimation(eff, b"opacity", self)
        fade.setDuration(fade_ms)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QtCore.QEasingCurve.InOutQuad)

        slide = QtCore.QPropertyAnimation(wrapper, b"offset", self)
        slide.setDuration(dur_ms)
        slide.setStartValue(dx)
        slide.setEndValue(0)
        # Row slide with a bit more bounce than panel
        curve = QtCore.QEasingCurve(QtCore.QEasingCurve.OutBack)
        curve.setOvershoot(1.25)  # 1.1–1.4 typical
        slide.setEasingCurve(curve)

        parallel = QtCore.QParallelAnimationGroup(self)
        parallel.addAnimation(fade)
        parallel.addAnimation(slide)

        seq = QtCore.QSequentialAnimationGroup(self)
        seq.addPause(index * stagger_ms)
        seq.addAnimation(parallel)

        self._row_anims.append(seq)
        def _cleanup():
            try:
                self._row_anims.remove(seq)
            except ValueError:
                pass
        seq.finished.connect(_cleanup)
        seq.start()

    # ----- Time label pulse animation (repeat for 10s) -----
    def _start_time_pulse(self, duration_ms: int = 10_000, interval_ms: int = 500):
        """
        Pulse the time labels' opacity (0.6 -> 1.0) with each cycle lasting `interval_ms`.
        Repeat for `duration_ms` total, then stop automatically.
        """
        # Stop previous pulse animations if any
        for a in self._time_anims:
            try:
                a.stop()
            except Exception:
                pass
        self._time_anims.clear()

        loops = max(1, duration_ms // interval_ms)

        for lab in self._row_time_labels:
            eff = lab.graphicsEffect()
            if not isinstance(eff, QtWidgets.QGraphicsOpacityEffect):
                eff = QtWidgets.QGraphicsOpacityEffect(lab)
                lab.setGraphicsEffect(eff)

            eff.setOpacity(1.0)
            anim = QtCore.QPropertyAnimation(eff, b"opacity", self)
            anim.setDuration(interval_ms)
            anim.setStartValue(0.6)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
            anim.setLoopCount(loops)
            self._time_anims.append(anim)
            anim.start()

        self._time_anim_running = True
        self._time_anim_deadline.start()

    def _maybe_stop_time_pulse(self, duration_ms: int = 10_000):
        """Stop time pulse if the deadline has passed."""
        if self._time_anim_running and self._time_anim_deadline.hasExpired(duration_ms):
            for a in self._time_anims:
                try:
                    a.stop()
                except Exception:
                    pass
            self._time_anims.clear()
            self._time_anim_running = False
            for lab in self._row_time_labels:
                eff = lab.graphicsEffect()
                if isinstance(eff, QtWidgets.QGraphicsOpacityEffect):
                    eff.setOpacity(1.0)

    # ----- Ensure the time column never crops (compute fixed width by font metrics) -----
    def _ensure_time_width(self, sample_text: str = "99:59.999", extra_px: int = 18):
        """
        Compute and set a fixed width for all time labels based on current font.
        sample_text should reflect your longest expected time format.
        """
        if not self._row_time_labels:
            return
        fm = QtGui.QFontMetrics(self._row_time_labels[0].font())
        width = fm.horizontalAdvance(sample_text) + extra_px
        for lab in self._row_time_labels:
            lab.setFixedWidth(width)

    # ----- Responsive font scaling (based on panel width) -----
    def _apply_responsive_fonts(self, base_w=350):
        w = max(1, self.width())
        scale = max(0.8, min(1.15, w / base_w))
        board_px = int(round(ROW_STYLE["board_font"] * scale * 0.85))
        name_px  = int(round(ROW_STYLE["name_font"]  * scale * 0.90))
        time_px  = int(round(ROW_STYLE["time_font"]  * scale * 0.90))

        for lab in getattr(self, "_row_time_labels", []):
            f = lab.font()
            f.setPointSize(time_px)
            lab.setFont(f)

        for wrapper_i in range(self.rows_layout.count()):
            w_item = self.rows_layout.itemAt(wrapper_i).widget()
            if not w_item:
                continue
            if isinstance(w_item, RowWrapper) and w_item.vbox.count():
                row = w_item.vbox.itemAt(0).widget()
                if isinstance(row, RowItem):
                    f_board = row.lab_board.font(); f_board.setPointSize(board_px); row.lab_board.setFont(f_board)
                    f_name  = row.lab_name.font();  f_name.setPointSize(name_px);  row.lab_name.setFont(f_name)

        # Recompute time width after font changes
        self._ensure_time_width(sample_text="99:59.999", extra_px=18)

    # ---- JSON mapping -> row widgets ----
    def update_from_payload(self, payload: dict):
        """
        Behavior:
        - First call (or structure/heat change): build rows, slide-in with bounce, start 10s time pulse.
        - Subsequent calls (every 500ms): update ONLY times and keep pulse running.
        """
        try:
            sw = payload.get("SwNames", []) or []
            boards = payload.get("BoardStatusAndTime", []) or []
            event_id = payload.get("EventID", None)
            heat_name = payload.get("HeatName", "") or ""

            # Title
            if event_id is not None and heat_name:
                self.title.setText(f"Event {event_id} · {heat_name}")
            elif event_id is not None:
                self.title.setText(f"Event {event_id}")
            elif heat_name:
                self.title.setText(heat_name)
            else:
                self.title.setText("Live Data")

            # Signature to detect new event/heat or row count change
            event_sig = (event_id, heat_name, len(boards))

            # --- If rows already exist, size matches, and same event/heat: update ONLY times ---
            if (self._row_time_labels
                and len(self._row_time_labels) == len(boards)
                and event_sig == self._last_event_sig):

                for i, b in enumerate(boards):
                    time_text = fmt_time_sec(b.get("Time"))
                    self._row_time_labels[i].setText(time_text)

                # stop pulse if 10s window ended
                self._maybe_stop_time_pulse(duration_ms=10_000)
                return

            # --- Otherwise (first time, count changed, or new event/heat), rebuild rows ---
            self._last_event_sig = event_sig

            # Stop any running per-row animations
            self._stop_row_anims()

            # Clear previous rows & time labels
            while self.rows_layout.count():
                item = self.rows_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
            self._row_time_labels.clear()

            # Build rows
            for i, b in enumerate(boards):
                board_id = b.get("BoardID", i + 1)
                name = sw[i] if i < len(sw) else ""
                time_text = fmt_time_sec(b.get("Time"))

                row = RowItem(str(board_id), name, time_text, self.rows_container)
                # keep a reference to the time label for fast updates
                self._row_time_labels.append(row.lab_time)

                # Wrap the row in RowWrapper to animate margins safely
                wrapper = RowWrapper(self.rows_container, initial_offset=48)
                wrapper.vbox.addWidget(row)

                # Subtle separator under each row except the last
                if i < len(boards) - 1:
                    sep = QtWidgets.QFrame(wrapper)
                    sep.setFrameShape(QtWidgets.QFrame.HLine)
                    sep.setFrameShadow(QtWidgets.QFrame.Plain)
                    sep.setStyleSheet(f"color: {ROW_STYLE['sep_color']};")
                    sep.setFixedHeight(ROW_STYLE["sep_height"])
                    wrapper.vbox.addWidget(sep)

                self.rows_layout.addWidget(wrapper)
                # Animate this row in with a stagger (no geometry fights) + bounce
                self._animate_row_in(wrapper, i, dx=48, dur_ms=240, fade_ms=180, stagger_ms=80)

            # Fix the time column width to avoid cropping (based on current font)
            self._ensure_time_width(sample_text="99:59.999", extra_px=18)
            # Apply responsive fonts after rows exist
            self._apply_responsive_fonts()

            self.rows_layout.addStretch(1)
            # Start a 10-second pulse animation on time labels (interval == POLL_MS)
            self._start_time_pulse(duration_ms=10_000, interval_ms=POLL_MS)

            self.animate_in()

        except Exception as ex:
            self._stop_row_anims()
            while self.rows_layout.count():
                item = self.rows_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
            self._row_time_labels.clear()

            err = RowItem("!", str(ex), "", self.rows_container)
            self.rows_layout.addWidget(err)
            self.rows_layout.addStretch(1)
            self.animate_in()

    def animate_in(self):
        # Panel-level fade to 1.0 (panel translucency controlled by CSS alpha)
        self.fade.stop()
        self.opacity.setOpacity(0.0)
        self.fade.setStartValue(0.0)
        self.fade.setEndValue(1.0)
        self.fade.setDuration(220)
        self.fade.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
        self.fade.start()

        # Small slide-in from the right with bounce
        self.slide.stop()
        final_geo = self.geometry()
        start_geo = QtCore.QRect(final_geo)
        start_geo.moveLeft(final_geo.left() + 48)
        self.setGeometry(start_geo)
        self.slide.setStartValue(start_geo)
        self.slide.setEndValue(final_geo)
        self.slide.setDuration(220)
        # easing curve already set in __init__ to OutBack (with overshoot)
        self.slide.start()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        # keep fonts and time width responsive on size changes
        if getattr(self, "_row_time_labels", None):
            self._apply_responsive_fonts()


class AspectStage(QtWidgets.QWidget):
    """
    Keeps the content area at a fixed aspect ratio and holds ONLY the video widget.
    The overlay panel is a separate (owned) top-level window for true translucency over VLC.
    """
    def __init__(self, ratio, video_widget):
        super().__init__()
        self.rw, self.rh = ratio
        self.video_widget = video_widget

        # Stage background is black (video will paint here).
        self.setStyleSheet("background:black;")

        self.content = QtWidgets.QWidget(self)
        self.content.setStyleSheet("background:black;")  # video lives here; no overlay inside

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.content)

        # The video widget fills 'content'
        vbox = QtWidgets.QVBoxLayout(self.content)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(self.video_widget)

    def _content_rect(self):
        w, h = self.width(), self.height()
        target_h = int(w * self.rh / self.rw)
        if target_h > h:
            target_h = h
            target_w = int(h * self.rw / self.rh)
        else:
            target_w = w
        x = (w - target_w) // 2
        y = (h - target_h) // 2
        return QtCore.QRect(x, y, target_w, target_h)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        # Keep the content (and thus video) centered in the aspect box
        c = self._content_rect()
        self.content.setGeometry(c)


class OverlayWindow(QtWidgets.QFrame):
    """
    Top-level transparent window that sits above the video surface,
    but only within the owning MainWindow (not globally).
    """
    def __init__(self, parent_window: QtWidgets.QMainWindow, target_widget: QtWidgets.QWidget):
        # Owned top-level window (parented), not a global tool
        flags = QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint
        super().__init__(parent_window, flags)

        # Transparency and no focus stealing
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)   # remove to allow mouse on panel
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
        self.setWindowModality(QtCore.Qt.NonModal)
        self.setWindowFlag(QtCore.Qt.WindowDoesNotAcceptFocus, True)
        self.setStyleSheet("background: transparent;")

        self.parent_window = parent_window
        self.target_widget = target_widget

        # One panel inside the overlay
        self.panel = DataPanel(self)
        self.panel.show()

        # Track parent move/resize/focus to reposition and show/hide overlay
        parent_window.installEventFilter(self)

        app = QtWidgets.QApplication.instance()
        app.focusChanged.connect(self._on_app_focus_changed)
        app.applicationStateChanged.connect(self._on_app_state_changed)

        self._sync_geometry()
        self._sync_visibility()

    # ---- Focus / visibility management ----
    def _on_app_focus_changed(self, old, now):
        self._sync_visibility()

    def _on_app_state_changed(self, state):
        self._sync_visibility()

    def _sync_visibility(self):
        app = QtWidgets.QApplication.instance()
        active_win = app.activeWindow()
        parent_active = (active_win is self.parent_window)
        parent_visible = self.parent_window.isVisible() and not self.parent_window.isMinimized()
        app_active = (app.applicationState() == QtCore.Qt.ApplicationActive)

        should_show = parent_visible and app_active and parent_active
        if should_show:
            if not self.isVisible():
                self.show()
        else:
            if self.isVisible():
                self.hide()

    def eventFilter(self, obj, ev):
        if obj is self.parent_window:
            et = ev.type()
            if et in (QtCore.QEvent.Move, QtCore.QEvent.Resize, QtCore.QEvent.WindowStateChange):
                self._sync_geometry()
                self._sync_visibility()
            elif et in (QtCore.QEvent.Show, QtCore.QEvent.Hide, QtCore.QEvent.ActivationChange):
                self._sync_visibility()
        return super().eventFilter(obj, ev)

    def _sync_geometry(self):
        # Make overlay exactly cover the video surface region on screen
        r = self.target_widget.frameGeometry()  # screen coords
        self.setGeometry(r)
        # Position panel at right-center within overlay with a bit more right margin for the time
        margin = 24  # avoid right-edge clipping
        pw, ph = self.panel.width(), self.panel.height()
        px = r.width() - pw - margin
        py = (r.height() - ph) // 2
        self.panel.setGeometry(px, py, pw, ph)
        if self.parent_window.isVisible() and not self.isVisible():
            self.show()

    # Helper for recorder: get current capture rectangle in device pixels
    def capture_rect_device_pixels(self):
        r = self.target_widget.frameGeometry()  # global coords (logical px)
        screen = self.parent_window.windowHandle().screen() if self.parent_window.windowHandle() else QtWidgets.QApplication.primaryScreen()
        dpr = screen.devicePixelRatio() if (USE_DPI_SCALING and screen is not None) else 1.0
        x = int(r.x() * dpr); y = int(r.y() * dpr); w = int(r.width() * dpr); h = int(r.height() * dpr)
        return x, y, w, h


class DataFetcher(QtCore.QObject):
    """Polls REST_URL every POLL_MS and emits parsed JSON."""
    dataReady = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(str)

    def __init__(self, url, interval_ms=POLL_MS, parent=None):
        super().__init__(parent)
        self.url = url
        self.interval_ms = interval_ms
        self.manager = QNetworkAccessManager(self)
        self.manager.finished.connect(self._on_reply)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._poll)

    def start(self):
        self.timer.start(self.interval_ms)
        self._poll()  # immediate first call

    def _poll(self):
        req = QNetworkRequest(QUrl(self.url))
        req.setHeader(QNetworkRequest.UserAgentHeader, "PyQt-Client")
        # If you need auth headers, set them here:
        # req.setRawHeader(b"Authorization", b"Bearer <token>")
        self.manager.get(req)

    def _on_reply(self, reply):
        try:
            if reply.error():
                self.error.emit(f"HTTP error: {reply.errorString()}")
                reply.deleteLater()
                return
            raw: QByteArray = reply.readAll()
            text = bytes(raw).decode("utf-8", errors="replace")
            obj = json.loads(text)
            # Adjust the path if your REST response structure is different
            self.dataReady.emit(obj["commandReturnData"])
        except Exception as ex:
            self.error.emit(f"Parse error: {ex}")
        finally:
            reply.deleteLater()


# # ===== Screen Recorder (FFmpeg) =====
# class ScreenRecorder(QtCore.QObject):
#     """Records the screen region where the RTSP + overlay are visible using FFmpeg."""
#     recordingChanged = QtCore.pyqtSignal(bool, str)  # (isRecording, outputPathOrEmpty)

#     def __init__(self, main_window):
#         super().__init__(main_window)
#         self.main = main_window
#         self.proc = None
#         self.output_path = None

#     def is_recording(self):
#         return self.proc is not None and self.proc.poll() is None

#     def _build_cmd(self, out_path):
#         # Get capture region (device pixels!)
#         x, y, w, h = self.main.overlay.capture_rect_device_pixels()

#         cmd = [FFMPEG_EXE, "-y"]

#         if sys.platform.startswith("win"):
#             # Desktop capture (GDI); fixed region. Do not move the window during recording.
#             cmd += [
#                 "-f", "gdigrab",
#                 "-framerate", str(REC_FPS),
#                 "-offset_x", str(x),
#                 "-offset_y", str(y),
#                 "-video_size", f"{w}x{h}",
#                 "-draw_mouse", "0",
#                 "-i", "desktop"
#             ]
#             # Optional audio (loopback)
#             if AUDIO_DEVICE_NAME:
#                 cmd += [
#                     "-f", "dshow",
#                     "-i", f"audio={AUDIO_DEVICE_NAME}",
#                     "-map", "0:v:0",
#                     "-map", "1:a:0",
#                     "-c:a", "aac",
#                     "-b:a", "160k"
#                 ]
#         elif sys.platform.startswith("linux"):
#             display = os.environ.get("DISPLAY", ":0.0")
#             cmd += [
#                 "-f", "x11grab",
#                 "-framerate", str(REC_FPS),
#                 "-video_size", f"{w}x{h}",
#                 "-i", f"{display}+{x},{y}"
#             ]
#         elif sys.platform == "darwin":
#             # macOS: capture full screen index 1 (may vary), then crop to region
#             # You can list devices with: ffmpeg -f avfoundation -list_devices true -i ""
#             cmd += [
#                 "-f", "avfoundation",
#                 "-framerate", str(REC_FPS),
#                 "-i", "1:none",     # screen index may need adjustment
#                 "-vf", f"crop={w}:{h}:{x}:{y}"
#             ]
#         else:
#             raise RuntimeError("Unsupported OS for screen recording")

#         # Video encoding
#         cmd += [
#             "-c:v", "libx264",
#             "-preset", REC_PRESET,
#             "-crf", str(REC_CRF),
#             "-pix_fmt", "yuv420p",
#             "-r", str(REC_FPS),
#             out_path
#         ]
#         return cmd

#     def start(self, out_path=None):
#         if self.is_recording():
#             return self.output_path

#         if out_path is None:
#             ts = QtCore.QDateTime.currentDateTime().toString("yyyyMMdd_HHmmss")
#             out_path = f"overlay_capture_{ts}.mp4"

#         cmd = self._build_cmd(out_path)
#         try:
#             self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#             self.output_path = out_path
#             self.recordingChanged.emit(True, out_path)
#             return out_path
#         except FileNotFoundError:
#             QtWidgets.QMessageBox.critical(self.main, "FFmpeg not found",
#                                            f"Could not find FFmpeg executable.\nSet FFMPEG_EXE correctly.\nTried: {FFMPEG_EXE}")
#             return None
#         except Exception as ex:
#             QtWidgets.QMessageBox.critical(self.main, "Recorder error", str(ex))
#             return None

#     def stop(self):
#         if not self.is_recording():
#             return None
#         try:
#             # Graceful stop: send 'q' to ffmpeg's stdin
#             self.proc.stdin.write(b"q")
#             self.proc.stdin.flush()
#         except Exception:
#             try:
#                 self.proc.terminate()
#             except Exception:
#                 pass

#         try:
#             self.proc.wait(timeout=3)
#         except Exception:
#             self.proc.kill()

#         path = self.output_path
#         self.proc = None
#         self.output_path = None
#         self.recordingChanged.emit(False, path or "")
#         return path



# ===== Windows virtual desktop helpers =====
def _win_virtual_desktop_rect_device_px():
    """
    Return (vx, vy, vw, vh) in device pixels for the *entire* virtual desktop.
    Works across multi-monitor (even with negative coords).
    """
    import ctypes
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()  # avoid logical px here
    SM_XVIRTUALSCREEN = 76
    SM_YVIRTUALSCREEN = 77
    SM_CXVIRTUALSCREEN = 78
    SM_CYVIRTUALSCREEN = 79
    vx = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
    vy = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
    vw = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
    vh = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
    return vx, vy, vw, vh


# ===== Screen Recorder (FFmpeg) =====
class ScreenRecorder(QtCore.QObject):
    
    """Records the screen region where the RTSP + overlay are visible using FFmpeg."""
    recordingChanged = QtCore.pyqtSignal(bool, str)  # (isRecording, outputPathOrEmpty)

    def _supports_gfxcapture(self) -> bool:
        """
        Return True if the installed FFmpeg build has the 'gfxcapture' source filter.
        """
        try:
            p = subprocess.run(
                [FFMPEG_EXE, "-hide_banner", "-filters"],
                capture_output=True, text=True
            )
            if p.returncode != 0:
                return False
            out = (p.stdout or "") + (p.stderr or "")
            # Look for '...  V->V  gfxcapture ...' or similar listing
            return "gfxcapture" in out.lower()
        except Exception:
            return False

    
    
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main = main_window
        self.proc = None
        self.output_path = None
        self.log_path = os.path.abspath("ffmpeg_recorder.log")

    def is_recording(self):
        return self.proc is not None and self.proc.poll() is None

    def _ffmpeg_exists(self):
        try:
            p = subprocess.run([FFMPEG_EXE, "-version"], capture_output=True, text=True)
            return p.returncode == 0
        except Exception:
            return False

    def _capture_rect_device_pixels(self):
        """
        Returns (x, y, w, h) for the video surface in *device* pixels,
        normalized to the Windows virtual desktop for gdigrab.
        """
        # # 1) Get overlay target in device px (your helper)
        # x, y, w, h = self.main.overlay.capture_rect_device_pixels()

        # # 2) Normalize offsets relative to the virtual desktop origin
        # vx, vy, vw, vh = _win_virtual_desktop_rect_device_px()
        # ox = x - vx
        # oy = y - vy

        # # 3) Clamp inside the virtual desktop bounds
        # if ox < 0:
        #     w += ox  # reduce width
        #     ox = 0
        # if oy < 0:
        #     h += oy
        #     oy = 0
        # if ox + w > vw:
        #     w = max(0, vw - ox)
        # if oy + h > vh:
        #     h = max(0, vh - oy)

        
        ox, oy, w, h = self._capture_rect_device_pixels()

        # Make dimensions even for yuv420p encoders
        if w % 2: w -= 1
        if h % 2: h -= 1
        if w <= 0 or h <= 0:
            raise RuntimeError(f"Invalid (after even-fix) size: {w}x{h}")

        cmd += [
            "-f", "gdigrab",
            "-framerate", str(REC_FPS),
            "-offset_x", str(ox),
            "-offset_y", str(oy),
            "-video_size", f"{w}x{h}",
            "-draw_mouse", "0",
            "-i", "desktop",
        ]        


        return int(ox), int(oy), int(w), int(h)

    def _build_cmd(self, out_path):
        ox, oy, w, h = self._capture_rect_device_pixels()

        if w <= 0 or h <= 0:
            raise RuntimeError(f"Invalid capture size: {w}x{h} at {ox},{oy}")

        cmd = [FFMPEG_EXE, "-y"]

    
        if sys.platform.startswith("win"):
            win_title = self.main.windowTitle()

            # Decide effective capture mode (fallback if gfxcapture unsupported)
            effective_mode = WINDOWS_CAPTURE_MODE
            if WINDOWS_CAPTURE_MODE == "gfxcapture" and not self._supports_gfxcapture():
                effective_mode = "gdigrab_title"

            if effective_mode == "gfxcapture":

                
                filter_chain = (
                    f"gfxcapture=window_title='{win_title}':max_framerate={REC_FPS},"
                    "hwdownload,format=bgra"
                )

                # If cropping to just the VLC video area:
                if CROP_TO_VIDEO_SURFACE:
                    cx, cy, cw, ch = self._video_rect_in_window_pixels()
                    filter_chain += f",crop={cw}:{ch}:{cx}:{cy}"

                # Always finish with yuv420p + even sizing for H.264
                filter_chain += ",format=yuv420p,scale=trunc(iw/2)*2:trunc(ih/2)*2"

                cmd += ["-filter_complex", f"{filter_chain}[v]"]
                cmd += ["-map", "[v]"]

                # # Capture via Windows.Graphics.Capture...
                # filter_chain = (
                #     f"gfxcapture=window_title='{win_title}':max_framerate={REC_FPS},"
                #     "hwdownload,format=bgra,format=yuv420p"
                # )
                # cmd += ["-filter_complex", f"{filter_chain}[v]"]
                # if AUDIO_DEVICE_NAME:
                #     cmd += [
                #         "-f", "dshow",
                #         "-i", f"audio={AUDIO_DEVICE_NAME}",
                #         "-map", "[v]", "-map", "0:a:0",
                #         "-c:a", "aac", "-b:a", "160k",
                #     ]
                # else:
                #     cmd += ["-map", "[v]"]
                # if CROP_TO_VIDEO_SURFACE:
                #     cx, cy, cw, ch = self._video_rect_in_window_pixels()
                #     cmd += ["-vf", f"crop={cw}:{ch}:{cx}:{cy}"]

            elif effective_mode == "gdigrab_title":
                cmd += [
                    "-f", "gdigrab",
                    "-framerate", str(REC_FPS),
                    "-draw_mouse", "0",
                    "-i", f"title={win_title}",
                ]
                if AUDIO_DEVICE_NAME:
                    cmd += [
                        "-f", "dshow",
                        "-i", f"audio={AUDIO_DEVICE_NAME}",
                        "-map", "0:v:0",
                        "-map", "1:a:0",
                        "-c:a", "aac",
                        "-b:a", "160k",
                    ]
                if CROP_TO_VIDEO_SURFACE:
                                        
                    vf_chain = []
                    if CROP_TO_VIDEO_SURFACE:
                        cx, cy, cw, ch = self._video_rect_in_window_pixels()
                        vf_chain.append(f"crop={cw}:{ch}:{cx}:{cy}")

                    vf_chain.append("format=yuv420p")
                    vf_chain.append("scale=trunc(iw/2)*2:trunc(ih/2)*2")

                    cmd += ["-vf", ",".join(vf_chain)]


            else:  # "gdigrab_region"
                ox, oy, w, h = self._capture_rect_device_pixels()
                if w <= 0 or h <= 0:
                    raise RuntimeError(f"Invalid capture size: {w}x{h} at {ox},{oy}")
                cmd += [
                    "-f", "gdigrab",
                    "-framerate", str(REC_FPS),
                    "-offset_x", str(ox),
                    "-offset_y", str(oy),
                    "-video_size", f"{w}x{h}",
                    "-draw_mouse", "0",
                    "-i", "desktop",
                    # "-show_region", "1",  # uncomment to visualize the capture box
                ]
                if AUDIO_DEVICE_NAME:
                    cmd += [
                        "-f", "dshow",
                        "-i", f"audio={AUDIO_DEVICE_NAME}",
                        "-map", "0:v:0",
                        "-map", "1:a:0",
                        "-c:a", "aac",
                        "-b:a", "160k",
                    ]

        elif sys.platform.startswith("linux"):
            display = os.environ.get("DISPLAY", ":0.0")
            cmd += [
                "-f", "x11grab",
                "-framerate", str(REC_FPS),
                "-video_size", f"{w}x{h}",
                "-i", f"{display}+{ox},{oy}",
            ]
        elif sys.platform == "darwin":
            # macOS: capture full screen index (may vary), then crop to region
            cmd += [
                "-f", "avfoundation",
                "-framerate", str(REC_FPS),
                "-i", "1:none",     # screen index may need adjustment
                "-vf", f"crop={w}:{h}:{ox}:{oy}",
            ]
        else:
            raise RuntimeError("Unsupported OS for screen recording")

        # Video encoding
        cmd += [
            "-c:v", "libx264",
            "-preset", REC_PRESET,
            "-crf", str(REC_CRF),
            "-pix_fmt", "yuv420p",
            "-r", str(REC_FPS),
            out_path,
        ]
        return cmd

   
    def start(self, out_path=None):
        # Diagnostics: ensure ffmpeg is available
        if not self._ffmpeg_exists():
            QtWidgets.QMessageBox.critical(
                self.main, "FFmpeg not found",
                f"Could not run FFmpeg.\nSet FFMPEG_EXE correctly.\nTried: {FFMPEG_EXE}"
            )
            return None

        if self.is_recording():
            return self.output_path

        # --- Default output path in the same directory as this Python file ---
        if out_path is None:
            ts = QtCore.QDateTime.currentDateTime().toString("yyyyMMdd_HHmmss")
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Ensure directory exists and is writable
            os.makedirs(script_dir, exist_ok=True)
            out_path = os.path.join(script_dir, f"overlay_capture_{ts}.mp4")

        try:
            cmd = self._build_cmd(out_path)

            # Open ffmpeg with logging
            log_file = open(self.log_path, "w", encoding="utf-8", errors="replace")
            log_file.write("FFmpeg command:\n" + " ".join(cmd) + "\n\n")
            log_file.flush()

            self.proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=log_file,   # capture output
                stderr=log_file    # capture errors
            )
            self.output_path = out_path
            self.recordingChanged.emit(True, out_path)
            return out_path

        except Exception as ex:
            QtWidgets.QMessageBox.critical(
                self.main, "Recorder error",
                f"{ex}\n\nSee log for details:\n{self.log_path}"
            )
            return None
 
    # def start(self, out_path=None):
    #     # Diagnostics: ensure ffmpeg is available
    #     if not self._ffmpeg_exists():
    #         QtWidgets.QMessageBox.critical(
    #             self.main, "FFmpeg not found",
    #             f"Could not run FFmpeg.\nSet FFMPEG_EXE correctly.\nTried: {FFMPEG_EXE}"
    #         )
    #         return None

    #     if self.is_recording():
    #         return self.output_path

    #     # --- Default output path in the same directory as this Python file ---
    #     if out_path is None:
    #         ts = QtCore.QDateTime.currentDateTime().toString("yyyyMMdd_HHmmss")
    #         script_dir = os.path.dirname(os.path.abspath(__file__))
    #         out_path = os.path.join(script_dir, f"overlay_capture_{ts}.mp4")

    #     try:
    #         cmd = self._build_cmd(out_path)

    #         # Open ffmpeg with logging
    #         log_file = open(self.log_path, "w", encoding="utf-8", errors="replace")
    #         log_file.write("FFmpeg command:\n" + " ".join(cmd) + "\n\n")
    #         log_file.flush()

    #         self.proc = subprocess.Popen(
    #             cmd,
    #             stdin=subprocess.PIPE,
    #             stdout=log_file,   # capture output
    #             stderr=log_file    # capture errors
    #         )
    #         self.output_path = out_path
    #         self.recordingChanged.emit(True, out_path)
    #         return out_path

    #     except Exception as ex:
    #         QtWidgets.QMessageBox.critical(self.main, "Recorder error", str(ex))
    #         return None

    def stop(self):
        if not self.is_recording():
            return None
        try:
            # Graceful stop: send 'q' to ffmpeg's stdin
            self.proc.stdin.write(b"q")
            self.proc.stdin.flush()
        except Exception:
            try:
                self.proc.terminate()
            except Exception:
                pass

        try:
            self.proc.wait(timeout=4)
        except Exception:
            self.proc.kill()

        path = self.output_path
        self.proc = None
        self.output_path = None
        self.recordingChanged.emit(False, path or "")
        return path

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RTSP + Right-Center JSON Panel (Owned Overlay)")
        self.resize(1280, 720)

        # Video surface inside a fixed-aspect stage
        self.video_surface = QtWidgets.QFrame()
        self.video_surface.setStyleSheet("background:black;")

        self.stage = AspectStage(ASPECT_RATIO, self.video_surface)
        self.setCentralWidget(self.stage)

        # VLC player (native window inside video_surface)
        self.vlc = vlc.Instance()
        self.player = self.vlc.media_player_new()
        wid = int(self.video_surface.winId())
        if sys.platform.startswith('linux'):
            self.player.set_xwindow(wid)
        elif sys.platform == "win32":
            self.player.set_hwnd(wid)
        else:
            self.player.set_nsobject(wid)

        media = self.vlc.media_new(RTSP_URL)
        self.player.set_media(media)
        self.player.play()

        # Owned overlay on top of the video surface for TRUE translucency
        self.overlay = OverlayWindow(self, self.video_surface)

        # REST fetcher
        self.fetcher = DataFetcher(REST_URL, POLL_MS, self)
        self.fetcher.dataReady.connect(self.on_data)
        self.fetcher.error.connect(self.on_error)
        self.overlay.panel.start_spinner()
        self.fetcher.start()

        # ===== Recorder =====
        self.recorder = ScreenRecorder(self)
        self.recorder.recordingChanged.connect(self.on_recording_changed)

        # Shortcut: Ctrl+R to toggle recording
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+R"), self, activated=self.toggle_recording)

        # Optional: status bar
        self.status = self.statusBar()
        self.status.showMessage("Ready. Press Ctrl+R to start/stop recording.")

    @QtCore.pyqtSlot(object)
    def on_data(self, payload):
        self.overlay.panel.stop_spinner()
        self.overlay.panel.update_from_payload(payload)

    @QtCore.pyqtSlot(str)
    def on_error(self, msg):
        self.overlay.panel.start_spinner()
        # Show the error message in the title area
        self.overlay.panel.update_from_payload({
            "SwNames": [],
            "Club": [],
            "BoardStatusAndTime": [],
            "HeatName": msg
        })

    # ===== Recording control =====
    def toggle_recording(self):
        if self.recorder.is_recording():
            out = self.recorder.stop()
            if out:
                self.status.showMessage(f"Recording saved: {os.path.abspath(out)}", 5000)
        else:
            out = self.recorder.start()  # or provide a path
            if out:
                self.status.showMessage(f"Recording... (saving to {os.path.basename(out)})")

    def on_recording_changed(self, is_rec, path):
        # You can reflect state in UI (icons, buttons) if needed
        pass


def main():
    app = QtWidgets.QApplication(sys.argv)
    # Optional: better visuals
    # app.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
