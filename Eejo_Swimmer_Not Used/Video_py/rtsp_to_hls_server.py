"""
rtsp_to_hls_server.py

Transcode an RTSP stream to HLS and serve a small webpage that plays it with hls.js.

Requirements:
- ffmpeg installed and on PATH
- Python 3.8+

Usage:
    python rtsp_to_hls_server.py --rtsp "rtsp://user:pass@192.168.0.100:554/Streaming/Channels/101" \
        --port 8090 --outdir ./hls

Open in browser:
- http://<host>:<port>/player.html

Notes:
- This creates HLS segments under the outdir and serves them via a simple HTTP server.
- hls.js is used in the page to play the HLS stream on browsers that do not natively support HLS.
"""

import argparse
import os
import subprocess
import threading
import http.server
import socketserver
import signal
import sys
import time
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('rtsp2hls')

# Default configuration variables (can be edited here)
DEFAULT_RTSP = 'rtsp://user:pass@192.168.0.100:554/Streaming/Channels/101'
DEFAULT_HTTP_HOST = '0.0.0.0'
DEFAULT_HTTP_PORT = 8090
DEFAULT_OUTDIR = './hls'
DEFAULT_SEGTIME = 2
DEFAULT_PRESET = 'veryfast'

PLAYER_HTML = '''<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>HLS Player</title>
  <style>body{background:#000;margin:0;display:flex;flex-direction:column;height:100vh}#controls{padding:10px;background:#111;color:#fff}#player{flex:1;display:flex;align-items:center;justify-content:center}video{width:90vw;max-width:1600px;}</style>
</head>
<body>
  <div id="controls">
    <label>Resolution: <select id="resolution"><option value="">Source</option><option value="1280x720">1280x720</option><option value="1920x1080">1920x1080</option><option value="3840x2160">3840x2160</option></select></label>
    <label>Preset: <select id="preset"><option>veryfast</option><option>fast</option><option>medium</option><option>slow</option></select></label>
    <label>Segment (s): <input id="segtime" type="number" value="2" min="1" style="width:60px"/></label>
    <button id="apply">Apply</button>
    <span id="status" style="margin-left:12px;color:#0f0"></span>
  </div>
  <div id="player"><video id="video" controls autoplay muted></video></div>
  <script src="https://cdn.jsdelivr.net/npm/hls.js@1"></script>
  <script>
    async function fetchConfig(){
      try{
        const r = await fetch('/config');
        if(!r.ok) throw new Error('no config');
        return await r.json();
      }catch(e){return null}
    }
    async function applyConfig(cfg){
      const r = await fetch('/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(cfg)});
      return r.ok?await r.json():null;
    }
    (async ()=>{
      const cfg = await fetchConfig();
      if(cfg){
        document.getElementById('segtime').value = cfg.segment_time || 2;
        document.getElementById('preset').value = cfg.preset || 'veryfast';
        if(cfg.scale){document.getElementById('resolution').value = cfg.scale[0]+'x'+cfg.scale[1];}
      }
      document.getElementById('apply').onclick = async ()=>{
        const resEl = document.getElementById('status');
        resEl.textContent = 'Applying...';
        const res = await applyConfig({
          preset: document.getElementById('preset').value,
          segment_time: parseInt(document.getElementById('segtime').value,10) || 2,
          scale: (document.getElementById('resolution').value || null)
        });
        if(res && res.ok){ resEl.style.color='#0f0'; resEl.textContent='Applied'; setTimeout(()=>resEl.textContent='',2000);}else{ resEl.style.color='#f00'; resEl.textContent='Failed'; }
      };

      // HLS player setup
      const video = document.getElementById('video');
      const src = 'index.m3u8';
      if (Hls.isSupported()) {
        const hls = new Hls();
        hls.loadSource(src);
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED,function() { video.play(); });
      } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = src; video.addEventListener('loadedmetadata',function() { video.play(); });
      } else {
        document.body.innerHTML = '<p style="color:white">HLS not supported in this browser.</p>';
      }
    })();
  </script>
</body>
</html>
'''


class ThreadedHTTPServer(object):
    def __init__(self, host: str, port: int, serve_dir: str, producer=None):
        self.host = host
        self.port = port
        self.serve_dir = os.path.abspath(serve_dir)
        self.httpd = None
        self.thread = None
        self.producer = producer

    def start(self):
        os.chdir(self.serve_dir)
        parent = self
        class CustomHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/config':
                    prod = getattr(self.server, 'producer', None)
                    cfg = {}
                    if prod:
                        cfg = {'rtsp': prod.rtsp_url, 'preset': prod.preset, 'segment_time': prod.segment_time, 'scale': prod.scale}
                    self.send_response(200)
                    self.send_header('Content-Type','application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(cfg).encode('utf-8'))
                    return
                return http.server.SimpleHTTPRequestHandler.do_GET(self)

            def do_POST(self):
                if self.path == '/config':
                    length = int(self.headers.get('Content-Length', '0'))
                    body = self.rfile.read(length) if length>0 else b''
                    try:
                        data = json.loads(body.decode('utf-8')) if body else {}
                    except Exception:
                        self.send_response(400); self.end_headers(); return
                    # parse config
                    preset = data.get('preset') or parent.producer.preset
                    segtime = int(data.get('segment_time') or parent.producer.segment_time)
                    scale_val = data.get('scale')
                    if scale_val:
                        if isinstance(scale_val, str) and 'x' in scale_val:
                            parts = scale_val.split('x')
                            try:
                                scale = (int(parts[0]), int(parts[1]))
                            except Exception:
                                scale = None
                        elif isinstance(scale_val, list) and len(scale_val)==2:
                            scale = (int(scale_val[0]), int(scale_val[1]))
                        else:
                            scale = None
                    else:
                        scale = None
                    # restart producer with new config
                    try:
                        old = getattr(self.server, 'producer', None)
                        if old and old.proc:
                            old.stop()
                        newp = FFmpegHLSProducer(old.rtsp_url if old else DEFAULT_RTSP, parent.serve_dir, segment_time=segtime, preset=preset)
                        newp.scale = scale
                        newp.start()
                        self.server.producer = newp
                        self.send_response(200)
                        self.send_header('Content-Type','application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'ok': True}).encode('utf-8'))
                    except Exception as e:
                        logger.exception('Failed to apply config')
                        self.send_response(500)
                        self.end_headers()
                    return
                return http.server.SimpleHTTPRequestHandler.do_POST(self)

        self.httpd = socketserver.TCPServer((self.host, self.port), CustomHandler)
        # attach producer reference to underlying server instance for handler access
        if self.producer:
            setattr(self.httpd, 'producer', self.producer)
        logger.info('HTTP server serving %s on http://%s:%d', self.serve_dir, self.host, self.port)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if self.httpd:
            logger.info('Stopping HTTP server')
            self.httpd.shutdown()
            self.httpd.server_close()
            self.thread.join(timeout=2)
            self.httpd = None


class FFmpegHLSProducer:
    def __init__(self, rtsp_url: str, out_dir: str, segment_time: int = 2, preset: str = 'veryfast', scale: tuple = None):
        self.rtsp_url = rtsp_url
        self.out_dir = os.path.abspath(out_dir)
        self.segment_time = int(segment_time)
        self.proc = None
        self.preset = preset
        self.scale = scale

    def start(self):
        os.makedirs(self.out_dir, exist_ok=True)
        # Clean old playlist/segments
        for f in os.listdir(self.out_dir):
            if f.endswith('.ts') or f.endswith('.m3u8'):
                try:
                    os.remove(os.path.join(self.out_dir, f))
                except Exception:
                    pass

        # Typical ffmpeg HLS command: transcode to H.264/AAC and create playlist
        out_playlist = os.path.join(self.out_dir, 'index.m3u8')
        cmd = [
            'ffmpeg', '-rtsp_transport', 'tcp', '-i', self.rtsp_url,
            '-c:v', 'libx264', '-preset', self.preset, '-tune', 'zerolatency', '-g', '50',
            '-c:a', 'aac', '-b:a', '128k',
        ]

        # Build video filters cleanly and choose bitrate when scaling
        vf_filters = []
        if self.scale and len(self.scale) == 2:
            try:
                sw, sh = int(self.scale[0]), int(self.scale[1])
                vf_filters.append(f'scale={sw}:{sh}:flags=lanczos')
                # choose a target video bitrate based on width
                if sw >= 3840:
                    vb = '12000k'
                elif sw >= 1920:
                    vb = '5000k'
                elif sw >= 1280:
                    vb = '3000k'
                else:
                    vb = '1500k'
                # add bitrate controls
                cmd += ['-b:v', vb, '-maxrate', vb, '-bufsize', str(int(vb[:-1]) * 2) + 'k']
            except Exception:
                vf_filters.append('scale=' + str(self.scale))
        # always ensure pixel format is yuv420p for compatibility
        vf_filters.append('format=yuv420p')
        if vf_filters:
            cmd += ['-vf', ','.join(vf_filters)]

        cmd += [
            '-hls_time', str(self.segment_time),
            '-hls_list_size', '6',
            '-hls_flags', 'delete_segments+append_list',
            '-hls_segment_filename', os.path.join(self.out_dir, 'seg%03d.ts'),
            out_playlist
        ]
        logger.info('Starting ffmpeg HLS producer: %s', ' '.join(cmd))
        logf = open(os.path.join(self.out_dir, 'ffmpeg_hls.log'), 'a', encoding='utf-8')
        self.proc = subprocess.Popen(cmd, stdout=logf, stderr=logf)
        time.sleep(0.5)
        if self.proc.poll() is not None:
            logger.error('ffmpeg exited immediately; check %s for details', logf.name)
            raise RuntimeError('ffmpeg failed to start')
        logger.info('ffmpeg started, pid=%s, writing HLS to %s', getattr(self.proc, 'pid', None), self.out_dir)

    def stop(self):
        if not self.proc:
            return
        logger.info('Stopping ffmpeg (pid=%s)', getattr(self.proc, 'pid', None))
        try:
            self.proc.terminate()
        except Exception:
            logger.exception('Failed to terminate ffmpeg gracefully; killing')
            try:
                self.proc.kill()
            except Exception:
                pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            logger.exception('Failed waiting for ffmpeg to exit')
            try:
                self.proc.kill()
            except Exception:
                pass
        self.proc = None


def parse_args():
    p = argparse.ArgumentParser(description='Transcode RTSP to browser-playable HLS and serve a player page')
    p.add_argument('--rtsp', default=DEFAULT_RTSP, help='RTSP input URL')
    p.add_argument('--port', type=int, default=DEFAULT_HTTP_PORT, help='HTTP server port')
    p.add_argument('--outdir', default=DEFAULT_OUTDIR, help='Output directory for HLS files')
    p.add_argument('--segtime', type=int, default=DEFAULT_SEGTIME, help='HLS segment duration (seconds)')
    p.add_argument('--preset', default=DEFAULT_PRESET, help='ffmpeg preset')
    return p.parse_args()


def main():
    args = parse_args()
    args.outdir = os.path.abspath(args.outdir)
    os.makedirs(args.outdir, exist_ok=True)
    # write player.html
    with open(os.path.join(args.outdir, 'player.html'), 'w', encoding='utf-8') as f:
        f.write(PLAYER_HTML)

    producer = FFmpegHLSProducer(args.rtsp, args.outdir, segment_time=args.segtime, preset=args.preset)
    try:
        producer.scale = None
        producer.start()
    except Exception as e:
        logger.exception('Producer failed to start: %s', e)
        return
    server = ThreadedHTTPServer(DEFAULT_HTTP_HOST, args.port, serve_dir=args.outdir, producer=producer)

    def shutdown(signum=None, frame=None):
        logger.info('Shutting down')
        try:
            producer.stop()
        except Exception:
            pass
        try:
            server.stop()
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    server.start()

    logger.info('Open the player at http://localhost:%d/player.html', args.port)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()


if __name__ == '__main__':
    main()
