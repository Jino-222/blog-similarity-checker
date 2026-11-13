import json
from pathlib import Path
from urllib.request import Request, urlopen

import streamlit as st


def render():
    state_file = Path(__file__).resolve().parent / 'data' / 'runtime' / 'launcher.json'
    if not state_file.exists():
        return
    # A legacy debug instance must not stop the separate managed instance.
    from streamlit import config
    if config.get_option('server.port') != 18766:
        return
    st.divider()
    st.caption('브라우저 탭만 닫으면 프로그램은 계속 실행됩니다. 사용을 마치면 아래 버튼을 눌러 주세요.')
    if st.button('프로그램 종료', key='shutdown_app'):
        try:
            state = json.loads(state_file.read_text(encoding='utf-8'))
            if state['control_url'] != 'http://127.0.0.1:18765':
                raise ValueError('실행 정보를 확인할 수 없습니다.')
            request = Request(state['control_url'] + '/shutdown', data=b'',
                              headers={'X-App-Token': state['token']}, method='POST')
            with urlopen(request, timeout=3) as response:
                if response.status != 200:
                    raise ValueError('종료 요청에 실패했습니다.')
        except (OSError, ValueError, KeyError) as error:
            st.error('종료하지 못했습니다. 실행 상태를 확인해 주세요.')
            st.text(str(error))
        else:
            st.success('프로그램을 종료합니다. 이 탭을 닫아도 됩니다.')
            st.stop()
