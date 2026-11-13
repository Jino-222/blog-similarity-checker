from pathlib import Path
from difflib import SequenceMatcher
import json
import sqlite3
from post_manager import merged_posts
from data_source import choose_data_file
import re
import unicodedata

import streamlit as st
from sentence_transformers import SentenceTransformer


st.set_page_config(
    page_title="내 블로그 중복 검사",
    page_icon=str(Path(__file__).resolve().parent / "assets" / "blog-check.png"),
    layout="centered",
)

PROJECT = Path(__file__).resolve().parent



def normalize(text):
    text = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"[\W_]+", "", text)


@st.cache_resource
def load_model():
    return SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        device="cpu",
    )


@st.cache_data
def encode_titles(titles):
    return load_model().encode(
        list(titles),
        batch_size=32,
        show_progress_bar=False,
    )



try:
    DATA_FILE, SAMPLE_MODE = choose_data_file(PROJECT)
    REGISTRY_FILE = PROJECT / "data" / ("sample_registered_posts.sqlite3" if SAMPLE_MODE else "registered_posts.sqlite3")
    posts = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    posts = merged_posts(posts, REGISTRY_FILE)
    if not isinstance(posts, list):
        raise ValueError("글 목록 형식이 올바르지 않습니다.")
    if not all(
        isinstance(post, dict)
        and isinstance(post.get("title"), str)
        and normalize(post["title"])
        and isinstance(post.get("body"), str)
        for post in posts
    ):
        raise ValueError("일부 글의 제목 또는 본문 형식이 올바르지 않습니다.")
except (OSError, ValueError, sqlite3.Error) as error:
    st.error("저장한 블로그 데이터를 읽지 못했습니다.")
    st.text(str(error))
    st.stop()

if not posts:
    st.warning("등록된 글이 없습니다.")
    st.stop()

from design import header, footer
header(len(posts), PROJECT)
if SAMPLE_MODE:
    st.info("샘플 모드 · 예시 글로 기능을 확인할 수 있습니다.")

with st.expander("등록된 제목 전체 보기"):
    for number, post in enumerate(posts, start=1):
        st.text(f"{number}. {post['title']}")

mode = st.radio("검사 방식", ["제목 검사", "본문 검사", "글 등록·수정"], horizontal=True)
if mode == "본문 검사":
    from body_check import render
    render(posts, load_model, PROJECT)
elif mode == "글 등록·수정":
    from post_manager import render as render_manager
    render_manager(posts, REGISTRY_FILE)
else:
    st.subheader("제목으로 비슷한 글 찾기")
    st.caption("작성하려는 주제를 입력하세요. 꼭 확인할 단어를 함께 넣으면 먼저 찾아드려요.")
    with st.form("check"):
        new_title = st.text_input(
            "새로 쓸 제목",
            placeholder="예: 주민등록등본 온라인 발급 방법",
            max_chars=200,
        )
        keyword = st.text_input(
            "우선 찾을 단어 (선택)",
            placeholder="예: 주민등록등본",
            help="이 단어가 제목에 들어간 글은 의미 점수와 관계없이 먼저 보여줍니다.",
        )
        threshold = st.slider(
            "뜻이 비슷한 정도의 기준",
            min_value=0.0,
            max_value=1.0,
            value=0.70,
            step=0.05,
            help="낮출수록 더 많은 후보가 나옵니다. 0.70은 임시 기준입니다.",
        )
        submitted = st.form_submit_button("제목 검사하기", type="primary", use_container_width=True)
    
    if submitted:
        new_title = new_title.strip()
        normalized_new = normalize(new_title)
    
        if not normalized_new:
            st.warning("문자나 숫자가 포함된 제목을 입력해 주세요.")
        else:
            try:
                with st.spinner("기존 글과 비교하고 있어요. 첫 검사는 잠시 걸립니다."):
                    model = load_model()
                    titles = tuple(post["title"] for post in posts)
                    title_vectors = encode_titles(titles)
                    new_vector = model.encode([new_title])
                    scores = model.similarity(new_vector, title_vectors)[0]
    
                    results = []
                    for post, score in zip(posts, scores):
                        ai_score = float(score)
                        normalized_existing = normalize(post["title"])
                        text_score = SequenceMatcher(
                            None,
                            normalized_new,
                            normalized_existing,
                            autojunk=False,
                        ).ratio() * 100
    
                        if new_title == post["title"]:
                            category = "완전히 같은 제목"
                            priority = 0
                        elif normalized_new == normalized_existing:
                            category = "표기만 다른 제목"
                            priority = 0
                        elif normalize(keyword) and normalize(keyword) in normalized_existing:
                            category = "지정한 단어가 포함된 제목"
                            priority = 0.5
                        elif ai_score >= threshold:
                            category = "뜻이 비슷한 제목"
                            priority = 1
                        elif text_score >= 70:
                            category = "글자가 비슷한 제목"
                            priority = 1
                        else:
                            continue
    
                        results.append(
                            (priority, ai_score, text_score, category, post)
                        )
    
                    results.sort(key=lambda item: (item[0], -item[1]))
    
                st.subheader("검사 결과")
                st.text(f"입력한 제목: {new_title}")
    
                if not results:
                    st.info("설정한 기준 이상의 후보가 없습니다.")
                else:
                    st.info(f"확인할 기존 글을 {len(results)}개 찾았어요.")
    
                    for _, ai_score, text_score, category, post in results:
                        st.divider()
                        st.text(post["title"])
                        st.caption(
                            f"{category} · 의미 점수 {ai_score:.3f}"
                            f" · 글자 유사도 {text_score:.1f}%"
                        )
                        with st.expander("이 글의 본문 보기"):
                            st.text(post["body"])
    
            except Exception as error:
                st.error("비교 중 문제가 발생했습니다.")
                st.text(str(error))

footer()

from app_controls import render as render_controls
render_controls()
