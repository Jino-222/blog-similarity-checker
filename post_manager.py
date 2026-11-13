from contextlib import closing
import json
import re
import sqlite3
from datetime import datetime, timezone
from urllib.parse import urlsplit, parse_qs

import streamlit as st


def parse_url(value):
    value = value.strip()
    if '://' not in value:
        value = 'https://' + value
    url = urlsplit(value)
    if url.scheme not in ('http', 'https') or url.hostname not in ('blog.naver.com', 'm.blog.naver.com') or url.port or url.username:
        raise ValueError('네이버 블로그 게시글 주소를 입력해 주세요.')
    parts = url.path.strip('/').split('/')
    if len(parts) == 2:
        blog, post_id = parts
    elif url.path.lower() == '/postview.naver':
        query = parse_qs(url.query)
        blog = query.get('blogId', [''])[0]
        post_id = query.get('logNo', [''])[0]
    else:
        raise ValueError('블로그 홈이 아닌 게시글 주소가 필요합니다.')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', blog) or not re.fullmatch(r'\d+', post_id):
        raise ValueError('글 주소에서 블로그 이름과 글 번호를 확인할 수 없습니다.')
    return post_id, f'https://blog.naver.com/{blog}/{post_id}'


def merged_posts(base, db):
    if not db.exists():
        return list(base)
    with closing(sqlite3.connect(db)) as connection:
        saved = dict(connection.execute('SELECT post_id, payload FROM posts'))
    overrides = {key: json.loads(value) for key, value in saved.items()}
    result = []
    for post in base:
        key = str(post.get('post_id') or '')
        result.append(overrides.pop(key, post))
    result.extend(overrides.values())
    return result


def save_post(db, post, previous=None):
    if not post['title'].strip() or not post['body'].strip():
        raise ValueError('제목과 본문을 모두 입력해 주세요.')
    db.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db, timeout=10)) as connection, connection:
        connection.execute('CREATE TABLE IF NOT EXISTS posts (post_id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        connection.execute('CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, post_id TEXT, payload TEXT, saved_at TEXT)')
        row = connection.execute('SELECT payload FROM posts WHERE post_id=?', (post['post_id'],)).fetchone()
        old = row[0] if row else json.dumps(previous, ensure_ascii=False) if previous else None
        if old:
            connection.execute('INSERT INTO history (post_id,payload,saved_at) VALUES (?,?,?)',
                               (post['post_id'], old, post['updated_at']))
        connection.execute('INSERT OR REPLACE INTO posts (post_id,payload) VALUES (?,?)',
                           (post['post_id'], json.dumps(post, ensure_ascii=False)))


def render(posts, db):
    st.subheader('게시한 글 등록·수정')
    st.write('네이버에 게시한 글을 이 검사 프로그램에 등록합니다. 네이버의 원문을 수정하거나 게시하지 않습니다.')
    if st.session_state.get('save_notice'):
        st.success(st.session_state.pop('save_notice'))
    address = st.text_input('네이버 게시글 주소', placeholder='https://blog.naver.com/블로그이름/글번호')
    if not address.strip():
        st.info('글 주소를 입력하면 기존 글인지 확인합니다.')
        return
    try:
        post_id, canonical = parse_url(address)
    except ValueError as error:
        st.warning(str(error))
        return
    existing = next((p for p in posts if str(p.get('post_id')) == post_id), None)
    if existing:
        st.info('이미 등록된 글입니다. 저장하면 아래 내용으로 갱신됩니다.')
        st.text('현재 제목: ' + existing['title'])
    else:
        st.info('새 글입니다. 제목과 본문을 붙여 넣어 주세요.')
    st.caption('주소에서 본문을 자동으로 가져오지는 않습니다.')
    revision = (existing or {}).get('updated_at', 'initial')
    with st.form('save_' + post_id + revision):
        title = st.text_input('저장할 제목', value=(existing or {}).get('title', ''), max_chars=300)
        body = st.text_area('저장할 본문', value=(existing or {}).get('body', ''), height=300)
        confirmed = st.checkbox('기존 내용을 위 내용으로 수정합니다.') if existing else True
        submitted = st.form_submit_button('수정 내용 저장' if existing else '새 글 저장', type='primary', use_container_width=True)
    if submitted:
        if not confirmed:
            st.warning('수정 확인 항목에 체크해 주세요.')
        elif not re.search(r'\w', title) or not re.search(r'\w', body):
            st.warning('제목과 본문에 글자 또는 숫자를 입력해 주세요.')
        else:
            post = dict(existing or {})
            post.update(post_id=post_id, url=canonical, title=title.strip(), body=body.strip(),
                        paragraphs=[p.strip() for p in body.splitlines() if p.strip()],
                        updated_at=datetime.now(timezone.utc).isoformat())
            try:
                save_post(db, post, existing)
            except (OSError, sqlite3.Error, ValueError) as error:
                st.error('저장하지 못했습니다. 입력 내용은 그대로 있습니다.')
                st.text(str(error))
            else:
                st.session_state.pop('body_results', None)
                st.session_state['save_notice'] = '저장했습니다. 제목·본문 검사 대상에 반영됐습니다.'
                st.rerun()
    st.caption('백업에서 가져온 원본은 보존하며, 수정 전 내용도 별도로 기록합니다. 저장 후 첫 본문 검사는 비교 자료를 다시 준비할 수 있습니다.')
