import hashlib
import json
from pathlib import Path

import numpy as np
import streamlit as st


def split_text(text, tokenizer, limit=100, overlap=20):
    """Keep every token within the model limit, retaining original characters."""
    chunks = []
    for paragraph in text.splitlines():
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        offsets = tokenizer(paragraph, add_special_tokens=False,
                            return_offsets_mapping=True)["offset_mapping"]
        for start in range(0, len(offsets), limit - overlap):
            end = min(start + limit, len(offsets))
            piece = paragraph[offsets[start][0]:offsets[end - 1][1]].strip()
            if piece:
                chunks.append(piece)
            if end == len(offsets):
                break
    return chunks


def records_for(posts, model):
    limit = min(100, model.max_seq_length - 4)
    return [(i, piece) for i, post in enumerate(posts)
            for piece in split_text(post['body'], model.tokenizer, limit)]


def get_vectors(records, model, cache_dir):
    fingerprint = hashlib.sha256(json.dumps(
        ['body-v1-multilingual-minilm', records], ensure_ascii=False
    ).encode('utf-8')).hexdigest()
    path = cache_dir / (fingerprint + '.npy')
    if path.exists():
        try:
            vectors = np.load(path, allow_pickle=False)
            if vectors.shape == (len(records), model.get_sentence_embedding_dimension()):
                return vectors
        except (OSError, ValueError):
            pass
    progress = st.progress(0, text='기존 본문을 준비합니다')
    batches = []
    for start in range(0, len(records), 128):
        batches.append(model.encode(
            [r[1] for r in records[start:start + 128]],
            batch_size=32, normalize_embeddings=True,
            show_progress_bar=False,
        ))
        done = min(start + 128, len(records))
        progress.progress(done / len(records), text=f'기존 본문 준비 중: {done:,}/{len(records):,}개 구간')
    vectors = np.concatenate(batches)
    cache_dir.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp.npy')
    np.save(temporary, vectors, allow_pickle=False)
    temporary.replace(path)
    progress.empty()
    return vectors


def render(posts, load_model, project):
    st.subheader('본문 비교')
    st.write('초안과 비슷한 기존 문단을 나란히 확인하세요. 입력한 초안은 게시글로 저장되지 않습니다.')
    sample = next((p for p in posts if '주민등록등본' in p['title']), posts[0])
    sample_lines = [x.strip() for x in sample['body'].splitlines() if len(x.strip()) >= 40]
    if st.button('기존 글 일부로 테스트하기'):
        st.session_state['draft_body'] = '\n\n'.join(sample_lines[:2]) or sample['body'][:500]
        st.session_state.pop('body_results', None)
    st.caption('테스트 원문: ' + sample['title'])
    with st.form('body_form'):
        draft = st.text_area('검사할 본문', key='draft_body', height=220, max_chars=30000)
        threshold = st.slider('본문 의미 점수 기준 (임시 기준)', 0.0, 1.0, 0.75, 0.05)
        submitted = st.form_submit_button('본문 검사하기', type='primary', use_container_width=True)
    st.caption('첫 검사는 기존 글 전체를 준비하므로 몇 분 이상 걸릴 수 있습니다. 준비 결과는 컴퓨터에 보관해 다음 검사에 재사용합니다.')
    if submitted:
        st.session_state.pop('body_results', None)
        if not draft.strip():
            st.warning('본문을 입력하거나 테스트 버튼을 눌러 주세요.')
        else:
            try:
                with st.spinner('본문을 비교하고 있어요…'):
                    model = load_model()
                    records = records_for(posts, model)
                    queries = split_text(draft, model.tokenizer, min(100, model.max_seq_length - 4))
                    if not records or not queries:
                        raise ValueError('비교할 글자가 없습니다.')
                    vectors = get_vectors(records, model, Path(project) / 'data' / 'body_cache')
                    query_vectors = model.encode(queries, normalize_embeddings=True, show_progress_bar=False)
                    results = []
                    for query, vector in zip(queries, query_vectors):
                        scores = vectors @ vector
                        best = []
                        used = set()
                        for index in np.argsort(-scores):
                            post_index, original = records[index]
                            score = float(scores[index])
                            if score < threshold:
                                break
                            if post_index not in used:
                                used.add(post_index)
                                best.append((posts[post_index]['title'], original, score))
                            if len(best) == 3:
                                break
                        results.append((query, best))
                    st.session_state['body_results'] = results
            except Exception as error:
                st.error('본문 비교 중 문제가 발생했습니다.')
                st.text(str(error))
    results = st.session_state.get('body_results')
    if results is not None:
        count = sum(bool(matches) for _, matches in results)
        st.info(f'입력 본문 {len(results)}개 구간 중 {count}개에서 후보를 찾았습니다. 구간별 서로 다른 글 최대 3개를 보여줍니다.')
        for number, (query, matches) in enumerate(results, 1):
            with st.expander(f'입력 구간 {number} · 후보 {len(matches)}개', expanded=bool(matches)):
                left, right = st.columns(2)
                left.markdown('**입력한 내용**')
                left.text(query)
                right.markdown('**비슷한 기존 내용**')
                if not matches:
                    right.write('기준 이상의 후보가 없습니다.')
                for title, original, score in matches:
                    right.text(title)
                    right.caption(f'의미 점수 {score:.3f}' + (' · 같은 문구' if query == original else ''))
                    right.text(original)
                    right.divider()
    st.caption('긴 문단은 겹치는 짧은 구간으로 나눕니다. 짧은 상용 문구도 후보가 될 수 있으며, 점수는 중복 확률이 아닙니다. 이미지 속 글자는 비교하지 않습니다.')

