"""
Simple RTSP player + transparent HTML overlay + start/stop recording.
- Reads RTSP_URL and REST_URL from your existing VLC_Overalay_PTZWorking.py when available.
- Uses python-vlc to render RTSP into a Qt widget.
- Uses PyQtWebEngine (QWebEngineView) for transparent HTML overlay.
- Starts FFmpeg to record the application window (so overlay is captured).

Requirements:
- pip install PyQt5 PyQtWebEngine python-vlc
- ffmpeg available on PATH (or edit FFMPEG_EXE)

Run: python rtsp_html_overlay_recorder.py
"""

import sys
import os
import subprocess
import datetime
import logging
import urllib.request
import urllib.error
import ctypes
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QUrl
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
except Exception:
    QWebEngineView = None

# Try to import user's constants (fall back to example values)
try:
    from VLC_Overalay_PTZWorking import RTSP_URL, REST_URL  
except Exception:
    RTSP_URL = "rtsp://user:pass@192.168.0.100:554/Streaming/Channels/101"
    REST_URL="https://www.google.com/"
    #REST_URL = "http://192.168.0.101:8002/EejoPages/LiveBoard_New.html"

# FFmpeg config
FFMPEG_EXE = "ffmpeg"
REC_FPS = 30
REC_PRESET = "veryfast"
REC_CRF = 18

# Configure logging
LOG_PATH = os.path.join(os.getcwd(), 'rtsp_overlay.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('rtsp_overlay')

# Determine overlay URL: environment override (OVERLAY_URL) else use REST_URL
overlay_url = "http://192.168.0.101:8002/EejoPages/testOverlay.html"
logger.info('Using overlay URL: %s', overlay_url)


class FFmpegWindowRecorder:
    """Record a window by its title using ffmpeg (gdigrab on Windows).
    Stops by sending 'q' to stdin.
    """
    def __init__(self, window_title: str, out_dir: str = None):
        self.window_title = window_title
        self.out_dir = out_dir or os.getcwd()
        self.proc = None

    def _out_path(self):
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        fn = f"record_{ts}.mp4"
        return os.path.join(self.out_dir, fn)

    def _ffmpeg_exists(self):
        try:
            p = subprocess.run([FFMPEG_EXE, '-version'], capture_output=True)
            return p.returncode == 0
        except Exception:
            return False

    def start(self, out_path: str = None, capture_rect: tuple = None):
        """Start ffmpeg recording.
        If capture_rect is provided (x, y, w, h) use desktop capture with offsets
        so both the VLC video and the separate overlay window (which is placed at
        screen coordinates) are recorded. Otherwise fallback to title-based capture.
        """
        logger.debug('Recorder.start() called (capture_rect=%s)', capture_rect)
        if not self._ffmpeg_exists():
            logger.error('ffmpeg not found')
            raise RuntimeError('ffmpeg not found')
        if self.is_recording():
            logger.debug('Recorder already running')
            return self.proc
        out_path = out_path or self._out_path()

        # If a capture rectangle was given, prefer desktop capture with offsets
        if capture_rect and len(capture_rect) == 4:
            x, y, w, h = capture_rect
            if sys.platform.startswith('win'):
                cmd = [
                    FFMPEG_EXE, '-y',
                    '-f', 'gdigrab',
                    '-framerate', str(REC_FPS),
                    '-offset_x', str(x),
                    '-offset_y', str(y),
                    '-video_size', f'{w}x{h}',
                    '-i', 'desktop',
                    '-draw_mouse', '1',
                    '-c:v', 'libx264',
                    '-preset', REC_PRESET,
                    '-crf', str(REC_CRF),
                    '-r', str(REC_FPS),
                    out_path
                ]
            elif sys.platform.startswith('linux'):
                display = os.environ.get('DISPLAY', ':0.0')
                cmd = [
                    FFMPEG_EXE, '-y',
                    '-f', 'x11grab',
                    '-framerate', str(REC_FPS),
                    '-video_size', f'{w}x{h}',
                    '-i', f'{display}+{x},{y}',
                    '-c:v', 'libx264',
                    '-preset', REC_PRESET,
                    '-crf', str(REC_CRF),
                    '-r', str(REC_FPS),
                    out_path
                ]
            else:
                logger.error('Unsupported OS for rectangle recording: %s', sys.platform)
                raise RuntimeError('Unsupported OS for rectangle recording')
        else:
            # Fallback: capture by window title as before
            if sys.platform.startswith('win'):
                cmd = [
                    FFMPEG_EXE, '-y',
                    '-f', 'gdigrab',
                    '-framerate', str(REC_FPS),
                    '-i', f"title={self.window_title}",
                    '-c:v', 'libx264',
                    '-preset', REC_PRESET,
                    '-crf', str(REC_CRF),
                    '-r', str(REC_FPS),
                    out_path
                ]
            elif sys.platform.startswith('linux'):
                display = os.environ.get('DISPLAY', ':0.0')
                cmd = [
                    FFMPEG_EXE, '-y',
                    '-f', 'x11grab',
                    '-framerate', str(REC_FPS),
                    '-i', display,
                    '-c:v', 'libx264',
                    '-preset', REC_PRESET,
                    '-crf', str(REC_CRF),
                    '-r', str(REC_FPS),
                    out_path
                ]
            else:
                logger.error('Unsupported OS for automatic recording: %s', sys.platform)
                raise RuntimeError('Unsupported OS for automatic recording')

        logger.info('Starting ffmpeg with command: %s', ' '.join(cmd))
        # Launch ffmpeg and keep stdin to stop with 'q'
        logpath = os.path.join(self.out_dir, 'ffmpeg_record.log')
        logf = open(logpath, 'a', encoding='utf-8')
        logf.write(f"{datetime.datetime.now()}: starting ffmpeg: {' '.join(cmd)}\n")
        logf.flush()
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=logf, stderr=logf)
        logger.debug('ffmpeg PID: %s, logging to: %s', getattr(self.proc, 'pid', None), logpath)
        return out_path

    def stop(self):
        logger.debug('Recorder.stop() called')
        if not self.is_recording():
            logger.debug('Recorder.stop() called but no active process')
            return None
        try:
            self.proc.stdin.write(b'q')
            self.proc.stdin.flush()
            logger.debug('Sent q to ffmpeg stdin')
        except Exception:
            logger.exception('Failed to send q to ffmpeg; attempting terminate')
            try:
                self.proc.terminate()
            except Exception:
                logger.exception('Failed to terminate ffmpeg')
        try:
            self.proc.wait(timeout=5)
            logger.debug('ffmpeg exited cleanly')
        except Exception:
            logger.exception('ffmpeg did not exit in time; killing')
            try:
                self.proc.kill()
            except Exception:
                logger.exception('Failed to kill ffmpeg')
        self.proc = None

    def is_recording(self):
        return self.proc is not None and self.proc.poll() is None


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, rtsp_url: str, html_url: str):
        super().__init__()
        logger.debug('MainWindow.__init__')
        self.setWindowTitle('RTSP + HTML Overlay')
        self.resize(1280, 720)

        self.rtsp_url = rtsp_url
        self.html_url = html_url

        # Central widget: video frame
        self.video_frame = QtWidgets.QFrame(self)
        self.video_frame.setStyleSheet('background: black;')
        self.setCentralWidget(self.video_frame)

        # Layout: stack controls on top
        self.vbox = QtWidgets.QVBoxLayout(self.video_frame)
        self.vbox.setContentsMargins(0, 0, 0, 0)

        # Controls bar
        ctrl = QtWidgets.QWidget(self)
        h = QtWidgets.QHBoxLayout(ctrl)
        h.setContentsMargins(6, 6, 6, 6)
        self.btn_play = QtWidgets.QPushButton('Play')
        self.btn_record = QtWidgets.QPushButton('Start Recording')
        self.btn_stoprec = QtWidgets.QPushButton('Stop Recording')
        self.btn_toggle_overlay = QtWidgets.QPushButton('Toggle Overlay')
        h.addWidget(self.btn_play)
        h.addWidget(self.btn_record)
        h.addWidget(self.btn_stoprec)
        h.addWidget(self.btn_toggle_overlay)
        h.addStretch(1)
        self.vbox.addWidget(ctrl, 0)

        # Ensure stop recording button disabled until recording starts
        self.btn_stoprec.setEnabled(False)

        # Video container (actual area for VLC window)
        self.video_container = QtWidgets.QWidget(self.video_frame)
        self.video_container.setStyleSheet('background: black;')
        self.vbox.addWidget(self.video_container, 1)

        # Setup VLC
        try:
            import vlc as _vlc_mod
            # keep a reference to the vlc module for EventType lookups
            self._vlc_mod = _vlc_mod
            # Allow disabling VLC hardware acceleration to improve compatibility with screen capture
            vlc_args = []
            disable_hw = os.environ.get('DISABLE_VLC_HW', '1')
            if disable_hw.lower() in ('1', 'true', 'yes'):
                vlc_args.append('--avcodec-hw=none')
                logger.info('VLC hardware acceleration disabled for better screen-capture compatibility')
            try:
                self.vlc = _vlc_mod.Instance(vlc_args) if vlc_args else _vlc_mod.Instance()
            except TypeError:
                # Some python-vlc versions expect *args instead of list
                self.vlc = _vlc_mod.Instance(*vlc_args) if vlc_args else _vlc_mod.Instance()
            self.player = self.vlc.media_player_new()
            logger.debug('python-vlc initialized')
        except Exception:
            logger.exception('Failed to initialize python-vlc')
            self.vlc = None
            self.player = None

        # Attach VLC event callbacks if available
        if self.player:
            try:
                em = self.player.event_manager()
                em.event_attach(getattr(self._vlc_mod, 'EventType').MediaPlayerEncounteredError, self._on_vlc_error)
                em.event_attach(getattr(self._vlc_mod, 'EventType').MediaPlayerPlaying, self._on_vlc_playing)
                em.event_attach(getattr(self._vlc_mod, 'EventType').MediaPlayerStopped, self._on_vlc_stopped)
                em.event_attach(getattr(self._vlc_mod, 'EventType').MediaPlayerPaused, self._on_vlc_paused)
                logger.debug('VLC event handlers attached')
            except Exception:
                logger.exception('Failed to attach VLC event handlers')

        # Web overlay
        self.web = None
        self.overlay_window = None
        if QWebEngineView is not None:
            # Create a separate top-level frameless transparent window for the overlay
            flags = QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool
            self.overlay_window = QtWidgets.QWidget(None, flags)
            self.overlay_window.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
            self.overlay_window.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)
            self.overlay_window.setWindowFlag(QtCore.Qt.WindowDoesNotAcceptFocus, True)
            # WebEngineView as child of overlay_window so it renders above native video
            self.web = QWebEngineView(self.overlay_window)
            # Make the web view visually transparent but accept mouse events by default
            self.web.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
            self.web.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
            self.web.setStyleSheet('background: transparent;')
            try:
                self.web.page().setBackgroundColor(QtCore.Qt.transparent)
            except Exception:
                pass
            try:
                self.web.loadFinished.connect(self._on_web_load_finished)
            except Exception:
                logger.exception('Failed to connect web.loadFinished')
            # Load URL directly in the web engine; allow QWebEngineView to handle redirects/headers
            if self.html_url.startswith(('http://', 'https://')):
                try:
                    logger.info('Attempting to load overlay URL in QWebEngineView: %s', self.html_url)
                    self.web.load(QUrl(self.html_url))
                except Exception:
                    logger.exception('QWebEngineView.load() failed to start; will try urllib fallback')
                    self._try_inject_via_urllib(self.html_url)
            else:
                html = f'<html><body style="margin:0;background:transparent;color:white;">Overlay\n<br>{self.html_url}</body></html>'
                self.web.setHtml(html)
            # Show overlay window after main window shown; keep it hidden for now
            self.overlay_window.hide()
        else:
            lbl = QtWidgets.QLabel('PyQtWebEngine not available\nInstall PyQtWebEngine for HTML overlay', self.video_container)
            lbl.setStyleSheet('color:white;background: rgba(0,0,0,0);')
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lbl.show()

        # Recorder placeholder
        self.recorder = FFmpegWindowRecorder(window_title=self.windowTitle())
        logger.debug('Recorder initialized with window_title=%s', self.recorder.window_title)

        # Connections
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_record.clicked.connect(self.start_recording)
        self.btn_stoprec.clicked.connect(self.stop_recording)
        self.btn_toggle_overlay.clicked.connect(self.toggle_overlay)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        # Keep web overlay filling the video container
        if self.web and self.overlay_window:
            # resize and reposition overlay to cover the video_container
            self._update_overlay_geometry()

    def showEvent(self, ev):
        super().showEvent(ev)
        logger.debug('showEvent fired; video_container winId=%s', int(self.video_container.winId()))
        # When shown, if VLC present, set the video widget to the container winId
        if self.player:
            wid = int(self.video_container.winId())
            logger.debug('Assigning VLC video output to window id %s', wid)
            if sys.platform.startswith('linux'):
                self.player.set_xwindow(wid)
            elif sys.platform == 'win32':
                self.player.set_hwnd(wid)
            else:
                try:
                    self.player.set_xwindow(wid)
                except Exception:
                    logger.exception('Failed to set VLC xwindow')
        # Position and show overlay window over the video container
        try:
            if self.overlay_window and self.web:
                self._update_overlay_geometry()
                self.overlay_window.show()
                self.web.show()
                logger.debug('Overlay window shown')
                # On Windows, make overlay an owned window so it minimizes/restores with the main window
                try:
                    if sys.platform == 'win32':
                        try:
                            # winId() returns HWND
                            owner_hwnd = int(self.winId())
                            child_hwnd = int(self.overlay_window.winId())
                            user32 = ctypes.windll.user32
                            GWLP_HWNDPARENT = -8
                            SetWindowLongPtr = getattr(user32, 'SetWindowLongPtrW', None) or user32.SetWindowLongW
                            # Some platforms expect c_long
                            SetWindowLongPtr(child_hwnd, GWLP_HWNDPARENT, owner_hwnd)
                            logger.debug('Set overlay owner on Windows: owner=%s child=%s', owner_hwnd, child_hwnd)
                        except Exception:
                            logger.exception('Failed to set overlay owner via SetWindowLongPtr')
                except Exception:
                    logger.exception('Failed during Windows overlay ownership setup')
        except Exception:
            logger.exception('Failed to show overlay window')
        # Auto-start playback on startup if not playing
        try:
            if self.player and not self.player.is_playing():
                logger.debug('Auto-starting playback in showEvent')
                # ensure output set then play
                try:
                    wid = int(self.video_container.winId())
                    if sys.platform.startswith('linux'):
                        self.player.set_xwindow(wid)
                    elif sys.platform == 'win32':
                        self.player.set_hwnd(wid)
                except Exception:
                    pass
                self.player.play()
                logger.debug('player.play() called from showEvent')
        except Exception:
            logger.exception('Failed to auto-start playback')

    def changeEvent(self, event):
        super().changeEvent(event)
        try:
            if event.type() == QtCore.QEvent.WindowStateChange:
                if self.isMinimized():
                    if self.overlay_window:
                        logger.debug('Main window minimized; hiding overlay')
                        self.overlay_window.hide()
                else:
                    if self.overlay_window:
                        logger.debug('Main window restored; showing overlay')
                        self._update_overlay_geometry()
                        self.overlay_window.show()
        except Exception:
            logger.exception('Error handling changeEvent')

    def toggle_play(self):
        logger.debug('toggle_play called; player present=%s', bool(self.player))
        if not self.player or not self.vlc:
            logger.warning('python-vlc missing when trying to play')
            QtWidgets.QMessageBox.warning(self, 'VLC missing', 'python-vlc is not installed or failed to import')
            return
        if self.player.is_playing():
            logger.debug('Stopping playback')
            self.player.stop()
            self.btn_play.setText('Play')
        else:
            logger.debug('Starting playback for URL: %s', self.rtsp_url)
            media = self.vlc.media_new(self.rtsp_url)
            # Attach media-level events if desired
            try:
                media_event_manager = media.event_manager()
                media_event_manager.event_attach(getattr(self._vlc_mod, 'EventType').MediaParsedChanged, lambda e: logger.info('MediaParsedChanged'))
            except Exception:
                logger.exception('Failed to attach media event handlers')
            self.player.set_media(media)
            # Ensure the video output is directed to our video container before starting playback
            try:
                wid = int(self.video_container.winId())
                logger.debug('Setting player video output to winId %s', wid)
                if sys.platform.startswith('linux'):
                    self.player.set_xwindow(wid)
                elif sys.platform == 'win32':
                    self.player.set_hwnd(wid)
                else:
                    try:
                        self.player.set_xwindow(wid)
                    except Exception:
                        logger.exception('Failed to set xwindow on non-standard platform')
            except Exception:
                logger.exception('Failed to obtain video_container.winId()')
            res = self.player.play()
            logger.debug('player.play() returned: %s', res)
            # Schedule status logs to help diagnose blank video issues
            QtCore.QTimer.singleShot(500, self._log_player_status)
            QtCore.QTimer.singleShot(2000, self._log_player_status)
            self.btn_play.setText('Stop')

    # VLC event handlers
    def _on_vlc_error(self, event=None):
        logger.error('VLC reported an error event: %s', event)

    def _on_vlc_playing(self, event=None):
        logger.info('VLC playing')

    def _on_vlc_stopped(self, event=None):
        logger.info('VLC stopped')

    def _on_vlc_paused(self, event=None):
        logger.info('VLC paused')

    def _log_player_status(self):
        try:
            state = None
            try:
                state = str(self.player.get_state())
            except Exception:
                state = 'unknown'
            try:
                vs = self.player.video_get_size(0)
                width, height = vs if isinstance(vs, tuple) else (vs, 0)
            except Exception:
                width, height = (0, 0)
            try:
                length = self.player.get_length()
            except Exception:
                length = -1
            try:
                pos = self.player.get_time()
            except Exception:
                pos = -1
            logger.info('VLC status: state=%s playing=%s video_size=%sx%s length=%s time=%s',
                        state, self.player.is_playing(), width, height, length, pos)
        except Exception:
            logger.exception('Failed to query VLC player status')

    def toggle_overlay(self):
        if not self.web:
            logger.warning('No web overlay to toggle')
            return
        if self.web.isVisible():
            self.overlay_window.hide()
            logger.info('Web overlay hidden')
        else:
            self.overlay_window.show()
            logger.info('Web overlay shown')

    def start_recording(self):
        # Update recorder window_title (in case user changed title)
        self.recorder.window_title = self.windowTitle()
        # Ask user where to save the recording file
        try:
            default_dir = os.path.join(os.getcwd(), 'recordings')
            os.makedirs(default_dir, exist_ok=True)
            default_name = datetime.datetime.now().strftime('record_%Y%m%d_%H%M%S.mp4')
            default_path = os.path.join(default_dir, default_name)
            out_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Recording As', default_path, 'MP4 files (*.mp4);;All files (*)')
            if not out_path:
                logger.info('Recording cancelled by user (no output path chosen)')
                return
            # Ensure ffmpeg log goes to the same folder as the output file
            self.recorder.out_dir = os.path.dirname(out_path) or os.getcwd()

            # Compute capture rectangle for the area we want to record (video_container on screen)
            try:
                gc = self.video_container.mapToGlobal(QtCore.QPoint(0, 0))
                cap_x, cap_y = int(gc.x()), int(gc.y())
                cap_w, cap_h = int(self.video_container.width()), int(self.video_container.height())
                capture_rect = (cap_x, cap_y, cap_w, cap_h)
                logger.debug('Computed capture_rect for recording: %s', capture_rect)
            except Exception:
                logger.exception('Failed to compute capture rectangle; falling back to window title capture')
                capture_rect = None

            out = self.recorder.start(out_path, capture_rect=capture_rect)
            # Update UI state
            self.btn_record.setEnabled(False)
            self.btn_stoprec.setEnabled(True)
            QtWidgets.QMessageBox.information(self, 'Recording', f'Started recording to:\n{out}')
        except Exception as e:
            logger.exception('Failed to start recording')
            QtWidgets.QMessageBox.critical(self, 'Record error', str(e))

    def stop_recording(self):
        if self.recorder.is_recording():
            try:
                self.recorder.stop()
                # Restore UI state
                self.btn_record.setEnabled(True)
                self.btn_stoprec.setEnabled(False)
                QtWidgets.QMessageBox.information(self, 'Recording', 'Recording stopped')
            except Exception as e:
                logger.exception('Error stopping recording')
                QtWidgets.QMessageBox.critical(self, 'Record error', str(e))
        else:
            QtWidgets.QMessageBox.information(self, 'Recording', 'No active recording')

    def _update_overlay_geometry(self):
        # Position overlay_window to match video_container on screen
        try:
            pos = self.video_container.mapToGlobal(QtCore.QPoint(0, 0))
            w = self.video_container.width()
            h = self.video_container.height()
            self.overlay_window.setGeometry(pos.x(), pos.y(), w, h)
            # ensure the web view fills the overlay window
            self.web.setGeometry(0, 0, w, h)
            logger.debug('Overlay geometry updated to %s,%s %sx%s', pos.x(), pos.y(), w, h)
        except Exception:
            logger.exception('Failed to update overlay geometry')

    def _overlay_fallback_html(self, reason: str):
        # Simple fallback to show when remote page is 404/unreachable
        return f'<html><body style="margin:0;background:rgba(0,0,0,0.6);color:white;font-family:Arial;">\n' \
               f'<div style="padding:12px">Overlay load failed: {reason}</div>\n' \
               '</body></html>'

    def _try_inject_via_urllib(self, url: str):
        """Fetch the URL with urllib and inject HTML only if content-type is HTML.
        This is a fallback when QWebEngine can't load the URL directly.
        """
        try:
            logger.info('Fetching overlay URL with urllib fallback: %s', url)
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=6) as resp:
                status = resp.getcode()
                ctype = resp.headers.get('Content-Type', '')
                body = resp.read()
            logger.debug('Fetched overlay via urllib: status=%s content-type=%s length=%d', status, ctype, len(body))
            if status == 200 and 'html' in ctype.lower():
                html_text = body.decode('utf-8', errors='replace')
                self.web.setHtml(html_text, baseUrl=QUrl(url))
                logger.info('Injected fetched HTML into QWebEngineView')
                return True
            else:
                logger.warning('Overlay URL is not HTML (status=%s content-type=%s); showing fallback', status, ctype)
                snippet = ''
                try:
                    snippet = body.decode('utf-8', errors='replace')[:200]
                except Exception:
                    pass
                self.web.setHtml(self._overlay_fallback_html(f'Status {status} content-type {ctype}: {snippet}'))
                return False
        except urllib.error.HTTPError as he:
            logger.exception('HTTPError during urllib fallback: %s', he)
            try:
                body = he.read(1024).decode('utf-8', errors='replace')
            except Exception:
                body = ''
            self.web.setHtml(self._overlay_fallback_html(f'HTTP {he.code}: {he.reason} {body[:200]}'))
            return False
        except Exception:
            logger.exception('Exception during urllib fallback')
            try:
                self.web.setHtml(self._overlay_fallback_html('Unreachable'))
            except Exception:
                pass
            return False

    def _on_web_load_finished(self, ok: bool):
        logger.info('Web overlay loadFinished: %s', ok)
        if not ok:
            try:
                # Replace with friendly message if the page failed to render
                self.web.setHtml(self._overlay_fallback_html('Load Failed'))
                logger.warning('Replaced overlay content with fallback due to load failure')
            except Exception:
                logger.exception('Failed to set fallback overlay HTML')


def main():
    app = QtWidgets.QApplication(sys.argv)
    # Ensure Qt WebEngine is initialized on some platforms
    if QWebEngineView is None:
        QtWidgets.QMessageBox.warning(None, 'Missing', 'PyQtWebEngine not installed. HTML overlay disabled.')

    w = MainWindow(RTSP_URL, overlay_url)
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
