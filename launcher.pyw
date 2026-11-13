"""Local-only, single-instance launcher. No console and no arbitrary PID killing."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
import webbrowser

ROOT = Path(__file__).resolve().parent
CONTROL_PORT = 18765
APP_PORT = 18766
CONTROL_URL = f'http://127.0.0.1:{CONTROL_PORT}'
APP_URL = f'http://127.0.0.1:{APP_PORT}'
IDENTITY = 'blog-check-' + hashlib.sha256(str(ROOT).encode()).hexdigest()[:16]
STATE = ROOT / 'data' / 'runtime' / 'launcher.json'


def fetch_status():
    with urlopen(CONTROL_URL + '/status', timeout=2) as response:
        status = json.load(response)
    if status.get('identity') != IDENTITY:
        raise RuntimeError('실행용 주소를 다른 프로그램이 사용 중입니다.')
    return status


def wait_and_open(no_browser):
    for _ in range(120):
        status = fetch_status()
        if status['ready']:
            if not no_browser:
                webbrowser.open(APP_URL)
            return
        if status.get('stopping'):
            raise RuntimeError('종료 중입니다. 잠시 후 다시 실행해 주세요.')
        time.sleep(1)
    raise RuntimeError('프로그램 준비 시간이 길어지고 있습니다. 잠시 후 다시 실행해 주세요.')


def main(no_browser=False):
    stop = threading.Event()
    ready = threading.Event()
    token = secrets.token_urlsafe(32)
    child = None

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, code, data):
            payload = json.dumps(data).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            if self.path != '/status':
                self.reply(404, {})
                return
            self.reply(200, {'identity': IDENTITY, 'ready': ready.is_set(),
                             'stopping': stop.is_set(), 'pid': os.getpid(),
                             'child_pid': child.pid if child else None})

        def do_POST(self):
            if self.path != '/shutdown':
                self.reply(404, {})
            elif not hmac.compare_digest(self.headers.get('X-App-Token', ''), token):
                self.reply(403, {})
            else:
                self.reply(200, {'stopping': True})
                stop.set()

    class ControlServer(ThreadingHTTPServer):
        allow_reuse_address = False

        def server_bind(self):
            if os.name == 'nt':
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            super().server_bind()

    try:
        server = ControlServer(('127.0.0.1', CONTROL_PORT), Handler)
    except OSError:
        wait_and_open(no_browser)
        return

    try:
        # Refuse to take over another app's port.
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', APP_PORT))
        python = ROOT / '.venv' / 'Scripts' / 'python.exe'
        if not python.is_file():
            python = ROOT / 'runtime' / 'python.exe'
            os.environ['HF_HOME'] = str(ROOT / 'data' / 'models')
        if not python.is_file():
            raise RuntimeError('Python 실행 환경이 없습니다. README의 설치 방법을 확인해 주세요.')
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps({'identity': IDENTITY, 'token': token,
                                    'control_url': CONTROL_URL}), encoding='utf-8')
        threading.Thread(target=server.serve_forever, daemon=True).start()
        with (STATE.parent / 'server.log').open('a', encoding='utf-8') as log:
            child = subprocess.Popen([
                str(python), '-m', 'streamlit', 'run', str(ROOT / 'app.py'),
                '--server.address', '127.0.0.1', '--server.port', str(APP_PORT),
                '--server.headless', 'true', '--client.toolbarMode', 'minimal',
                '--browser.gatherUsageStats', 'false',
            ], cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            for _ in range(120):
                if stop.is_set():
                    break
                if child.poll() is not None:
                    raise RuntimeError('검사 화면을 시작하지 못했습니다. data/runtime/server.log를 확인해 주세요.')
                try:
                    with urlopen(APP_URL + '/_stcore/health', timeout=1) as response:
                        if response.status == 200:
                            ready.set()
                            break
                except OSError:
                    pass
                time.sleep(1)
            if not ready.is_set() and not stop.is_set():
                raise RuntimeError('검사 화면이 준비되지 않았습니다. 실행 기록을 확인해 주세요.')
            if ready.is_set() and not stop.is_set() and not no_browser:
                webbrowser.open(APP_URL)
            while not stop.wait(1):
                if child.poll() is not None:
                    raise RuntimeError('검사 프로그램이 종료됐습니다. 아이콘으로 다시 실행해 주세요.')
            time.sleep(2)  # Let the UI display its shutdown message.
    finally:
        if child and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
        # Only this launcher owns this file while the control socket is held.
        if STATE.exists():
            try:
                if json.loads(STATE.read_text(encoding='utf-8')).get('token') == token:
                    STATE.unlink()
            except (OSError, ValueError):
                pass
        server.server_close()


if __name__ == '__main__':
    try:
        main('--no-browser' in sys.argv)
    except Exception as error:
        if '--no-browser' in sys.argv:
            raise
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, str(error), '내 블로그 중복 검사', 0x10)
