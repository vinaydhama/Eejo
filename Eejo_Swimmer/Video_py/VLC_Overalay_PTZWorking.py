
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
RTSP_URL = "rtsp://user:pass@192.168.0.101:554/Streaming/Channels/101"  # <- your camera URL
REST_URL = "http://192.168.0.103:5002/SetLiveHeatCommands?CmdName=LiveBoard"  # <- your REST endpoint
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

# --- ONVIF IP Camera Control (PTZ/Media) ---
ONVIF_ENABLED = True
ONVIF_HOST = '192.168.0.101'
ONVIF_PORT = 8899
ONVIF_USER = 'user'
ONVIF_PASS = 'pass'
ONVIF_WSDL_DIR = None
ONVIF_PROFILE_INDEX = 0
PTZ_SPEED = 0.6
PTZ_MOVE_MS = 400

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
# 
class OnvifController(QtCore.QObject):
    """ONVIF PTZ/Media/DeviceMgmt helper."""
    connectedChanged = QtCore.pyqtSignal(bool)

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main = main_window
        self.camera = None
        self.media = None
        self.ptz = None
        self.profile = None
        self._enabled = bool(globals().get('ONVIF_ENABLED', False))

    def isEnabled(self):
        return self._enabled

    def connect(self):
        if not self._enabled:
            return False
        try:
            from onvif import ONVIFCamera
        except Exception as ex:
            QtWidgets.QMessageBox.warning(self.main, "ONVIF not available",
                "python-onvif-zeep is not installed. Install with: pip install onvif-zeep\n" + str(ex))
            self._enabled = False
            self.connectedChanged.emit(False)
            return False
        try:
            wsdl_dir = ONVIF_WSDL_DIR if ONVIF_WSDL_DIR else None
            if wsdl_dir:
                self.camera = ONVIFCamera(ONVIF_HOST, ONVIF_PORT, ONVIF_USER, ONVIF_PASS, wsdl_dir)
            else:
                self.camera = ONVIFCamera(ONVIF_HOST, ONVIF_PORT, ONVIF_USER, ONVIF_PASS)
            self.media = self.camera.create_media_service()
            self.ptz = self.camera.create_ptz_service()
            profiles = self.media.GetProfiles()
            idx = max(0, min(ONVIF_PROFILE_INDEX, len(profiles)-1))
            self.profile = profiles[idx]
            self.connectedChanged.emit(True)
            return True
        except Exception as ex:
            QtWidgets.QMessageBox.critical(self.main, "ONVIF connect failed", str(ex))
            self.connectedChanged.emit(False)
            return False

    def _ensure(self):
        if not (self.camera and self.media and self.ptz and self.profile):
            return self.connect()
        return True

   
    def stop(self):
        if not self._ensure():
            return
        try:
            self.ptz.Stop({'ProfileToken': self.profile.token})
        except Exception:
            pass

    
    def _profile_token(self):
        # Return a plain string for the ProfileToken (ReferenceToken)
        for name in ('_token', 'token', 'Token'):
            t = getattr(self.profile, name, None)
            if isinstance(t, str) and t:
                return t
        try:
            t = getattr(self.profile, 'token', None)
            return str(t) if t is not None else None
        except Exception:
            return None


    def zoom_continuous(self, direction: int = +1, speed: float = PTZ_SPEED, ms: int = PTZ_MOVE_MS):
        """
        Zoom in/out continuously for `ms` ms, then stop.
        direction: +1 (in), -1 (out)
        """
        if not self._ensure():
            return
        try:
            token = self._profile_token()
            if not token:
                raise RuntimeError('No ProfileToken')

            # Clamp and build velocity (Zoom only). Many cameras prefer ContinuousMove for zoom.
            sgn = 1 if direction >= 0 else -1
            z = float(speed) * sgn

            req = self.ptz.create_type('ContinuousMove')
            req.ProfileToken = str(token)

            # Build Velocity explicitly to avoid NoneType errors
            req.Velocity = {
                'Zoom':    {'x': z}  # tt:Vector1D
                # PanTilt omitted intentionally when zooming only
            }

            self.ptz.ContinuousMove(req)
            QtCore.QTimer.singleShot(int(ms), lambda: self.stop_pan_tilt_zoom(stop_pan_tilt=False, stop_zoom=True))
        except Exception as ex:
            QtWidgets.QMessageBox.warning(self.main, "PTZ zoom failed", str(ex))

    def stop_pan_tilt_zoom(self, stop_pan_tilt: bool = True, stop_zoom: bool = True):
        """
        ONVIF Stop: stops ongoing pan/tilt/zoom movement. If optional flags are provided,
        they indicate which axes to stop (spec says defaults to true when omitted).
        """
        if not self._ensure():
            return
        try:
            token = self._profile_token()
            if not token:
                raise RuntimeError('No ProfileToken')

            req = {'ProfileToken': str(token)}
            # Some cameras want explicit booleans for which axes to stop
            req['PanTilt'] = bool(stop_pan_tilt)
            req['Zoom']    = bool(stop_zoom)

            self.ptz.Stop(req)
        except Exception as ex:
            QtWidgets.QMessageBox.warning(self.main, "PTZ stop failed", str(ex))

    def goto_home(self):
        """
        Go to home position if supported.
        """
        if not self._ensure():
            return
        try:
            # Detect support (optional but helpful)
            try:
                nodes = self.ptz.GetNodes()  # returns one or more PTZ nodes
                home_ok = False
                for n in nodes or []:
                    if getattr(n, 'HomeSupported', False):
                        home_ok = True
                        break
                if not home_ok:
                    QtWidgets.QMessageBox.information(
                        self.main, "PTZ Home",
                        "Camera reports HomeSupported=False; operation may fail."
                    )
            except Exception:
                # If GetNodes not supported, proceed anyway
                pass

            token = self._profile_token()
            if not token:
                raise RuntimeError('No ProfileToken')

            # Prefer Zeep type, fallback to dict
            try:
                req = self.ptz.create_type('GotoHomePosition')
                req.ProfileToken = str(token)
                self.ptz.GotoHomePosition(req)
            except Exception:
                self.ptz.GotoHomePosition({'ProfileToken': str(token)})
        except Exception as ex:
            QtWidgets.QMessageBox.warning(self.main, "PTZ go home failed", str(ex))

    def set_home(self):
        """
        Set current position as home (if supported).
        """
        if not self._ensure():
            return
        try:
            token = self._profile_token()
            if not token:
                raise RuntimeError('No ProfileToken')

            # Prefer Zeep type, fallback to dict
            try:
                req = self.ptz.create_type('SetHomePosition')
                req.ProfileToken = str(token)
                self.ptz.SetHomePosition(req)
            except Exception:
                self.ptz.SetHomePosition({'ProfileToken': str(token)})

            QtWidgets.QMessageBox.information(self.main, "PTZ Home", "Home position updated.")
        except Exception as ex:
            QtWidgets.QMessageBox.warning(self.main, "PTZ set home failed", str(ex))

    def continuous_move(self, vx=0.0, vy=0.0, vz=0.0, ms=PTZ_MOVE_MS):
        if not self._ensure():
            return
        try:
            token = self._profile_token()
            if not token:
                raise RuntimeError('No ProfileToken')

            # Clamp and build PTZSpeed as dicts (Zeep will map to tt:PTZSpeed)
            vx = max(-1.0, min(1.0, float(vx)))
            vy = max(-1.0, min(1.0, float(vy)))
            vz = max(-1.0, min(1.0, float(vz)))

            req = self.ptz.create_type('ContinuousMove')
            req.ProfileToken = str(token)
            # Create Velocity explicitly to avoid NoneType errors
            req.Velocity = {
                'PanTilt': {'x': vx, 'y': vy},   # tt:Vector2D
                'Zoom':    {'x': vz}             # tt:Vector1D
            }

            self.ptz.ContinuousMove(req)
            QtCore.QTimer.singleShot(int(ms), self.stop)
        except Exception as ex:
            QtWidgets.QMessageBox.warning(self.main, "PTZ move failed", str(ex))

    def relative_move(self, dx=0.0, dy=0.0, dz=0.0, speed=PTZ_SPEED):
        if not self._ensure():
            return
        try:
            token = self._profile_token()
            if not token:
                raise RuntimeError('No ProfileToken')

            req = self.ptz.create_type('RelativeMove')
            req.ProfileToken = str(token)
            req.Translation = {
                'PanTilt': {'x': float(dx), 'y': float(dy)},
                'Zoom':    {'x': float(dz)}
            }
            req.Speed = {
                'PanTilt': {'x': float(speed), 'y': float(speed)},
                'Zoom':    {'x': float(speed)}
            }

            self.ptz.RelativeMove(req)
        except Exception as ex:
            QtWidgets.QMessageBox.warning(self.main, "PTZ relative move failed", str(ex))

    def absolute_move(self, px=0.0, py=0.0, pz=0.0, speed=PTZ_SPEED):
        if not self._ensure():
            return
        try:
            token = self._profile_token()
            if not token:
                raise RuntimeError('No ProfileToken')

            req = self.ptz.create_type('AbsoluteMove')
            req.ProfileToken = str(token)
            # Build Position explicitly (tt:PTZVector)
            req.Position = {
                'PanTilt': {'x': float(px), 'y': float(py)},
                'Zoom':    {'x': float(pz)}
            }
            # Optional speed
            req.Speed = {
                'PanTilt': {'x': float(speed), 'y': float(speed)},
                'Zoom':    {'x': float(speed)}
            }

            self.ptz.AbsoluteMove(req)
        except Exception as ex:
            QtWidgets.QMessageBox.warning(self.main, "PTZ absolute move failed", str(ex))

    def get_presets(self):
        if not self._ensure():
            return []
        try:
            presets = self.ptz.GetPresets({'ProfileToken': self.profile.token})
            return presets or []
        except Exception:
            return []

    def goto_preset(self, preset_token_or_index):
        if not self._ensure():
            return
        try:
            token = None
            presets = self.get_presets()
            if isinstance(preset_token_or_index, int):
                i = max(0, min(preset_token_or_index, len(presets)-1))
                token = presets[i].token if presets else None
            else:
                token = preset_token_or_index
            if token:
                self.ptz.GotoPreset({'ProfileToken': self.profile.token, 'PresetToken': token})
        except Exception as ex:
            QtWidgets.QMessageBox.warning(self.main, "PTZ goto preset failed", str(ex))

    def set_preset(self, name="Preset"):
        if not self._ensure():
            return
        try:
            return self.ptz.SetPreset({'ProfileToken': self.profile.token, 'PresetName': name})
        except Exception as ex:
            QtWidgets.QMessageBox.warning(self.main, "PTZ set preset failed", str(ex))
            return None

    def remove_preset(self, token):
        if not self._ensure():
            return
        try:
            self.ptz.RemovePreset({'ProfileToken': self.profile.token, 'PresetToken': token})
        except Exception as ex:
            QtWidgets.QMessageBox.warning(self.main, "PTZ remove preset failed", str(ex))

    def get_rtsp_uri(self):
        if not self._ensure():
            return None
        try:
            req = self.media.create_type('GetStreamUri')
            req.ProfileToken = self.profile.token
            req.StreamSetup = type('obj', (), {})()
            req.StreamSetup.Stream = 'RTP-Unicast'
            req.StreamSetup.Transport = type('obj', (), {'Protocol': 'RTSP'})()
            uri = self.media.GetStreamUri(req)
            return getattr(uri, 'Uri', None)
        except Exception:
            return None

    # DeviceMgmt / Imaging
    def _ensure_devicemgmt(self):
        if not self._ensure():
            return False
        try:
            if not hasattr(self, 'devicemgmt') or self.devicemgmt is None:
                self.devicemgmt = self.camera.create_devicemgmt_service()
            return True
        except Exception as ex:
            QtWidgets.QMessageBox.warning(self.main, "ONVIF DeviceMgmt", str(ex))
            return False

    def get_device_info(self):
        if not self._ensure_devicemgmt():
            return None
        try:
            return self.devicemgmt.GetDeviceInformation()
        except Exception as ex:
            QtWidgets.QMessageBox.warning(self.main, "GetDeviceInformation failed", str(ex))
            return None

    def get_datetime(self):
        if not self._ensure_devicemgmt():
            return None
        try:
            return self.devicemgmt.GetSystemDateAndTime()
        except Exception as ex:
            QtWidgets.QMessageBox.warning(self.main, "GetSystemDateAndTime failed", str(ex))
            return None

    def set_time_to_system(self, use_utc=True, daylight_savings=False, tz_str='UTC'):
        if not self._ensure_devicemgmt():
            return False
        try:
            req = self.devicemgmt.create_type('SetSystemDateAndTime')
            req.DateTimeType = 'Manual'
            req.DaylightSavings = bool(daylight_savings)
            req.TimeZone = type('obj', (), {})(); req.TimeZone.TZ = tz_str
            dt = QtCore.QDateTime.currentDateTimeUtc() if use_utc else QtCore.QDateTime.currentDateTime()
            req.UTCDateTime = type('obj', (), {})()
            req.UTCDateTime.Date = type('obj', (), {})(); req.UTCDateTime.Time = type('obj', (), {})()
            req.UTCDateTime.Date.Year = dt.date().year(); req.UTCDateTime.Date.Month = dt.date().month(); req.UTCDateTime.Date.Day = dt.date().day()
            req.UTCDateTime.Time.Hour = dt.time().hour(); req.UTCDateTime.Time.Minute = dt.time().minute(); req.UTCDateTime.Time.Second = dt.time().second()
            self.devicemgmt.SetSystemDateAndTime(req)
            return True
        except Exception as ex:
            QtWidgets.QMessageBox.warning(self.main, "SetSystemDateAndTime failed", str(ex))
            return False

    def system_reboot(self):
        if not self._ensure_devicemgmt():
            return False
        try:
            self.devicemgmt.SystemReboot(); return True
        except Exception as ex:
            QtWidgets.QMessageBox.warning(self.main, "SystemReboot failed", str(ex)); return False
class ScreenRecorder(QtCore.QObject):

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


class PTZDockWidget(QtWidgets.QDockWidget):
    def __init__(self, controller: OnvifController, parent=None):
        super().__init__("PTZ Controls", parent)
        self.ctrl = controller
        content = QtWidgets.QWidget(self)
        self.setWidget(content)
        layout = QtWidgets.QVBoxLayout(content)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        grid = QtWidgets.QGridLayout(); grid.setSpacing(4)
        def mk_btn(t, h):
            b = QtWidgets.QPushButton(t); b.setFixedHeight(28); b.clicked.connect(h); return b
        grid.addWidget(mk_btn("↖", lambda: self._move(-1, +1, 0)), 0, 0)
        grid.addWidget(mk_btn("↑", lambda: self._move(0, +1, 0)),    0, 1)
        grid.addWidget(mk_btn("↗", lambda: self._move(+1, +1, 0)), 0, 2)
        grid.addWidget(mk_btn("←", lambda: self._move(-1, 0, 0)),   1, 0)
        grid.addWidget(mk_btn("■", self._stop),                     1, 1)
        grid.addWidget(mk_btn("→", lambda: self._move(+1, 0, 0)),   1, 2)
        grid.addWidget(mk_btn("↙", lambda: self._move(-1, -1, 0)), 2, 0)
        grid.addWidget(mk_btn("↓", lambda: self._move(0, -1, 0)),   2, 1)
        grid.addWidget(mk_btn("↘", lambda: self._move(+1, -1, 0)), 2, 2)
        layout.addLayout(grid)
        zr = QtWidgets.QHBoxLayout()
        # zr.addWidget(mk_btn("Zoom -", lambda: self._move(0,0,-1)))
        # zr.addWidget(mk_btn("Stop", self._stop))
        # zr.addWidget(mk_btn("Zoom +", lambda: self._move(0,0,+1)))
        # layout.addLayout(zr)
        
        zr.addWidget(mk_btn("Zoom -", lambda: self.ctrl.zoom_continuous(direction=-1)))
        zr.addWidget(mk_btn("Stop",   lambda: self.ctrl.stop_pan_tilt_zoom(stop_pan_tilt=False, stop_zoom=True)))
        zr.addWidget(mk_btn("Zoom +", lambda: self.ctrl.zoom_continuous(direction=+1)))
        layout.addLayout(zr)
        
        hr = QtWidgets.QHBoxLayout()
        hr.addWidget(mk_btn("Go Home", self.ctrl.goto_home))
        hr.addWidget(mk_btn("Set Home", self.ctrl.set_home))
        layout.addLayout(hr)

        # hr.addWidget(mk_btn("Go Home", self._home)); hr.addWidget(mk_btn("Set Home", self._set_home))
        # layout.addLayout(hr)
        pr = QtWidgets.QHBoxLayout(); self.presetBox = QtWidgets.QComboBox(); self.presetBox.setMinimumWidth(160)
        pr.addWidget(self.presetBox,2); pr.addWidget(mk_btn("Refresh", self._refresh_presets),0); pr.addWidget(mk_btn("Goto", self._goto_preset),0)
        layout.addLayout(pr)
        sr = QtWidgets.QHBoxLayout(); self.presetName = QtWidgets.QLineEdit(); self.presetName.setPlaceholderText("New preset name…")
        sr.addWidget(self.presetName,2); sr.addWidget(mk_btn("Set Preset", self._set_preset),0); sr.addWidget(mk_btn("Remove", self._remove_preset),0)
        layout.addLayout(sr)
        ur = QtWidgets.QHBoxLayout(); ur.addWidget(mk_btn("Get RTSP URI", self._get_rtsp)); layout.addLayout(ur)
        self._refresh_presets()
    def _move(self, dx, dy, dz):
        try: self.ctrl.continuous_move(dx*PTZ_SPEED, dy*PTZ_SPEED, dz*PTZ_SPEED, ms=PTZ_MOVE_MS)
        except Exception as ex: QtWidgets.QMessageBox.warning(self, "PTZ", str(ex))
    def _stop(self): self.ctrl.stop()
    def _home(self): self.ctrl.goto_home() if hasattr(self.ctrl,'goto_home') else None
    def _set_home(self): self.ctrl.set_home() if hasattr(self.ctrl,'set_home') else None
    def _refresh_presets(self):
        self.presetBox.clear(); presets = self.ctrl.get_presets() or []
        for p in presets:
            name = getattr(p,'Name',getattr(p,'name','Preset')); token = getattr(p,'token',getattr(p,'Token',None))
            self.presetBox.addItem(f"{name}", token)
    def _goto_preset(self):
        token = self.presetBox.currentData();
        if token: self.ctrl.goto_preset(token)
    def _set_preset(self):
        name = self.presetName.text().strip() or "Preset"; self.ctrl.set_preset(name); self._refresh_presets()
    def _remove_preset(self):
        token = self.presetBox.currentData();
        if token: self.ctrl.remove_preset(token); self._refresh_presets()
    def _get_rtsp(self):
        uri = self.ctrl.get_rtsp_uri();
        QtWidgets.QMessageBox.information(self, "ONVIF RTSP URI", uri if uri else "No URI returned")

class ControlCenterWindow(QtWidgets.QMainWindow):
    def __init__(self, main: 'MainWindow'):
        super().__init__(main)
        self.main = main
        self.setWindowTitle("Control Center: Recording + ONVIF")
        self.resize(600, 520)
        self.tabs = QtWidgets.QTabWidget(self); self.setCentralWidget(self.tabs)
        self._build_record_tab(); self._build_ptz_tab(); self._build_device_tab(); self._build_time_tab()
    def _build_record_tab(self):
        w = QtWidgets.QWidget(); lay = QtWidgets.QVBoxLayout(w)
        h = QtWidgets.QHBoxLayout(); h.addWidget(QtWidgets.QLabel("Output folder:"));
        self.outDir = QtWidgets.QLineEdit(getattr(self.main,'output_dir', os.path.dirname(os.path.abspath(__file__))))
        b = QtWidgets.QPushButton("Browse…")
        def _browse():
            d = QtWidgets.QFileDialog.getExistingDirectory(self, "Select output folder", self.outDir.text())
            if d: self.outDir.setText(d); self.main.output_dir = d
        b.clicked.connect(_browse); h.addWidget(self.outDir,1); h.addWidget(b); lay.addLayout(h)
        grid = QtWidgets.QGridLayout(); grid.addWidget(QtWidgets.QLabel("FPS:"),0,0)
        self.fpsSpin = QtWidgets.QSpinBox(); self.fpsSpin.setRange(5,120); self.fpsSpin.setValue(self.main.get_rec_cfg('fps') if hasattr(self.main,'get_rec_cfg') else 30)
        grid.addWidget(self.fpsSpin,0,1); grid.addWidget(QtWidgets.QLabel("CRF:"),0,2)
        self.crfSpin = QtWidgets.QSpinBox(); self.crfSpin.setRange(0,40); self.crfSpin.setValue(self.main.get_rec_cfg('crf') if hasattr(self.main,'get_rec_cfg') else 18)
        grid.addWidget(self.crfSpin,0,3); grid.addWidget(QtWidgets.QLabel("Preset:"),1,0)
        self.presetBox = QtWidgets.QComboBox(); self.presetBox.addItems(["ultrafast","superfast","veryfast","faster","fast","medium","slow","slower","veryslow"])
        if hasattr(self.main,'get_rec_cfg'):
            idx = max(0, self.presetBox.findText(self.main.get_rec_cfg('preset'))); self.presetBox.setCurrentIndex(idx)
        grid.addWidget(self.presetBox,1,1); lay.addLayout(grid)
        row = QtWidgets.QHBoxLayout();
        btnStart = QtWidgets.QPushButton("Start Recording (Ctrl+R)"); btnStop=QtWidgets.QPushButton("Stop"); btnOpen=QtWidgets.QPushButton("Open Folder"); btnLog=QtWidgets.QPushButton("Open FFmpeg Log")
        row.addWidget(btnStart); row.addWidget(btnStop); row.addWidget(btnOpen); row.addWidget(btnLog); lay.addLayout(row)
        def _apply_cfg():
            if hasattr(self.main,'set_rec_cfg'):
                self.main.set_rec_cfg(fps=self.fpsSpin.value(), crf=self.crfSpin.value(), preset=self.presetBox.currentText())
            self.main.output_dir = self.outDir.text().strip() or self.main.output_dir
        btnStart.clicked.connect(lambda: (_apply_cfg(), self.main.toggle_recording()))
        btnStop.clicked.connect(lambda: (self.main.recorder.stop() if self.main.recorder.is_recording() else None))
        btnOpen.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(self.main.output_dir)))
        btnLog.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(self.main.recorder.log_path)))
        lay.addStretch(1)
        self.tabs.addTab(w, "Record")
    def _build_ptz_tab(self):
        w = QtWidgets.QWidget(); lay = QtWidgets.QVBoxLayout(w)
        try:
            panel = PTZDockWidget(self.main.onvif, self); lay.addWidget(panel.widget())
        except Exception:
            lay.addWidget(QtWidgets.QLabel("PTZ panel unavailable"))
        self.tabs.addTab(w, "PTZ")
    def _build_device_tab(self):
        w = QtWidgets.QWidget(); lay = QtWidgets.QVBoxLayout(w)
        btnInfo=QtWidgets.QPushButton("Get Device Info"); btnProfiles=QtWidgets.QPushButton("Get Profiles"); btnUri=QtWidgets.QPushButton("Get Stream URI")
        self.txt=QtWidgets.QPlainTextEdit(); self.txt.setReadOnly(True)
        r=QtWidgets.QHBoxLayout(); r.addWidget(btnInfo); r.addWidget(btnProfiles); r.addWidget(btnUri); lay.addLayout(r); lay.addWidget(self.txt)
        btnInfo.clicked.connect(lambda: self._log(self.main.onvif.get_device_info()))
        btnProfiles.clicked.connect(lambda: self._log(self.main.onvif.media.GetProfiles() if self.main.onvif and self.main.onvif.media else "No media"))
        btnUri.clicked.connect(lambda: self._log(self.main.onvif.get_rtsp_uri()))
        self.tabs.addTab(w, "Device/Media")
    def _build_time_tab(self):
        w = QtWidgets.QWidget(); lay = QtWidgets.QVBoxLayout(w)
        btnGet=QtWidgets.QPushButton("Get Camera Date/Time"); btnSet=QtWidgets.QPushButton("Sync Time to PC (UTC)"); btnReboot=QtWidgets.QPushButton("Reboot")
        self.timeTxt=QtWidgets.QPlainTextEdit(); self.timeTxt.setReadOnly(True)
        rr=QtWidgets.QHBoxLayout(); rr.addWidget(btnGet); rr.addWidget(btnSet); rr.addWidget(btnReboot); lay.addLayout(rr); lay.addWidget(self.timeTxt)
        btnGet.clicked.connect(lambda: self._log(self.main.onvif.get_datetime(), target=self.timeTxt))
        btnSet.clicked.connect(lambda: self._log(self.main.onvif.set_time_to_system(True), target=self.timeTxt))
        btnReboot.clicked.connect(lambda: self._log(self.main.onvif.system_reboot(), target=self.timeTxt))
        self.tabs.addTab(w, "Time & Reboot")
    def _log(self, obj, target=None):
        t = target or self.txt; t.appendPlainText(str(obj))
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # ONVIF controller
        self.onvif = OnvifController(self)
        if self.onvif.isEnabled():
            self.onvif.connect()

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

        # Recording config and control center
        self.output_dir = os.path.dirname(os.path.abspath(__file__))
        self._rec_cfg = {'fps': REC_FPS, 'crf': REC_CRF, 'preset': REC_PRESET}
        def _open_cc():
            try:
                if not hasattr(self, 'controlCenter') or self.controlCenter is None:
                    self.controlCenter = ControlCenterWindow(self)
                self.controlCenter.show(); self.controlCenter.raise_(); self.controlCenter.activateWindow()
            except Exception as ex:
                QtWidgets.QMessageBox.warning(self, "Control Center", str(ex))
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Shift+C"), self, activated=_open_cc)

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
            out_path = self.compose_output_path()
            out = self.recorder.start(out_path)
            if out:
                self.status.showMessage(f"Recording... (saving to {os.path.basename(out)} )")

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

    def get_rec_cfg(self, key):
        return self._rec_cfg.get(key)
    def set_rec_cfg(self, fps=None, crf=None, preset=None):
        global REC_FPS, REC_CRF, REC_PRESET
        if fps is not None:
            REC_FPS = int(fps); self._rec_cfg['fps'] = REC_FPS
        if crf is not None:
            REC_CRF = int(crf); self._rec_cfg['crf'] = REC_CRF
        if preset is not None:
            REC_PRESET = str(preset); self._rec_cfg['preset'] = REC_PRESET
    def compose_output_path(self):
        ts = QtCore.QDateTime.currentDateTime().toString("yyyyMMdd_HHmmss")
        d = self.output_dir or os.path.dirname(os.path.abspath(__file__))
        try: os.makedirs(d, exist_ok=True)
        except Exception: pass
        return os.path.join(d, f"overlay_capture_{ts}.mp4")