"""Exercise the installed app using its own private Python environment."""
import sys
import os
from pathlib import Path

root = Path(sys.argv[1]).resolve()
os.environ['HF_HOME'] = str(root / 'data/models')
os.environ['HF_HUB_OFFLINE'] = '1'
from streamlit.testing.v1 import AppTest
app = AppTest.from_file(str(root / 'app.py'), default_timeout=180).run()
assert not app.exception, app.exception
assert len(app.radio) == 1
app.text_input[0].set_value('실내 식물 물 주기: 흙을 확인하는 습관')
app.button[0].click().run(timeout=180)
assert not app.exception, app.exception
assert any('완전히 같은 제목' in x.value for x in app.caption)
app.radio[0].set_value('본문 검사').run()
next(b for b in app.button if b.label == '기존 글 일부로 테스트하기').click().run()
next(b for b in app.button if b.label == '본문 검사하기').click().run(timeout=180)
assert not app.exception, app.exception
assert any('같은 문구' in x.value for x in app.caption)
app.radio[0].set_value('글 등록·수정').run()
assert not app.exception, app.exception
print('PASS: installed title search, body search, management screen')

if '--launcher' in sys.argv:
    import json
    import subprocess
    import time
    from urllib.request import Request, urlopen
    command = [str(root / 'runtime/python.exe'), str(root / 'launcher.pyw'), '--no-browser']
    process = subprocess.Popen(command, cwd=root)
    try:
        for attempt in range(150):
            if process.poll() is not None:
                raise AssertionError('Launcher exited before becoming ready')
            try:
                with urlopen('http://127.0.0.1:18765/status', timeout=1) as response:
                    if json.load(response)['ready']:
                        break
            except OSError:
                pass
            time.sleep(1)
        else:
            raise AssertionError('Launcher did not become ready')
        subprocess.run(command, cwd=root, check=True, timeout=150)
        state = json.loads((root / 'data/runtime/launcher.json').read_text())
        request = Request(state['control_url'] + '/shutdown', data=b'', headers={'X-App-Token': state['token']})
        with urlopen(request, timeout=5) as response:
            assert response.status == 200
        assert process.wait(timeout=30) == 0
        assert not (root / 'data/runtime/launcher.json').exists()
        print('PASS: launcher health, duplicate launch, authenticated shutdown')
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
