from pathlib import Path
import base64
import streamlit as st


def header(count, project):
    icon = base64.b64encode((Path(project) / 'assets' / 'blog-check.png').read_bytes()).decode()
    st.markdown('''<style>
    .block-container {max-width:1080px; padding-top:2.8rem; padding-bottom:3rem;}
    h1,h2,h3 {letter-spacing:-.045em;}
    .brand {display:flex; align-items:center; gap:18px; margin-bottom:24px;}
    .brand img {width:64px; height:64px; border-radius:18px;}
    .brand h1 {font-size:32px; margin:0; padding:0; color:#142b45; font-weight:800;}
    .brand p {color:#54677a; margin:6px 0 0; font-size:15px;}
    .intro {background:#142b45; color:#fff; border-radius:22px; padding:26px 30px;
            display:flex; justify-content:space-between; gap:24px; align-items:center; margin:10px 0 24px;}
    .intro .tag {color:#8de1d3; font-size:12px; font-weight:700; letter-spacing:.08em;}
    .intro h2 {font-size:25px; color:#fff; padding:10px 0 8px; margin:0;}
    .intro p {font-size:14px; color:#d5e0ec; margin:0; line-height:1.7;}
    .library {min-width:130px; border-left:1px solid #46596e; padding-left:30px;}
    .library strong {display:block; font-size:38px; letter-spacing:-.06em; color:#fff;}
    .library span {font-size:13px; color:#d5e0ec;}
    [data-testid="stForm"] {background:#fff; border:1px solid #dce5ec; border-radius:18px; padding:24px;}
    [data-testid="stExpander"] {background:#fff; border-radius:14px;}
    [data-testid="stRadio"] [role="radiogroup"] {gap:10px; padding:8px 0 18px;}
    [data-testid="stRadio"] [role="radiogroup"] label {background:#fff; border:1px solid #dce5ec;
         border-radius:12px; padding:12px 20px; flex:1; min-width:150px;}
    [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {border-color:#087f8c; background:#e7f5f3;}
    [data-testid="stText"] {white-space:pre-wrap; overflow-wrap:anywhere; font-family:inherit; line-height:1.85;}
    [data-testid="stCaptionContainer"] {line-height:1.65;}
    button[kind="primaryFormSubmit"] {border-radius:10px; min-height:44px;}
    .footer-note {margin-top:30px; padding:18px 0; border-top:1px solid #dce5ec;
       color:#637588; font-size:13px; line-height:1.7;}
    @media (max-width:640px) {.brand h1 {font-size:25px;} .intro {padding:22px; flex-direction:column; align-items:flex-start;}
      .library {border-left:0; border-top:1px solid #46596e; padding:12px 0 0; width:100%;}
      .library strong {font-size:28px;} .block-container {padding-top:1.5rem;}}
    </style>''', unsafe_allow_html=True)
    st.markdown(f'''<div class="brand"><img src="data:image/png;base64,{icon}" alt="블로그 검사 아이콘">
    <div><h1>내 블로그 중복 검사</h1><p>쌓아 둔 글을 살펴보고, 다음 글을 더 새롭게.</p></div></div>
    <div class="intro"><div><div class="tag">나만의 글 관리 도우미</div>
    <h2>쓰기 전 한 번, 올리기 전 한 번.</h2>
    <p>제목으로 주제를 찾고, 본문으로 겹치는 내용을 확인하세요.</p></div>
    <div class="library"><span>함께 비교할 기존 글</span><strong>{count:,}<small style="font-size:16px"> 편</small></strong></div></div>''', unsafe_allow_html=True)


def footer():
    st.markdown('<div class="footer-note">의미 점수는 중복 확률이 아닙니다. 비슷한 문장은 직접 검토해 주세요.<br>내 컴퓨터에 저장된 글을 비교합니다 · 네이버 게시글은 자동으로 변경되지 않습니다.</div>', unsafe_allow_html=True)

