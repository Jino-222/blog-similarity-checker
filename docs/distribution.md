# 공개 자료와 출처

## 포함

- 현재 실행 코드와 설정 예시
- 가상 샘플 글 3개: 실제 블로그 백업을 복사하지 않고 이 프로젝트의 공개 테스트용으로 작성
- 프로젝트용 문서·돋보기·체크 아이콘: 코드로 제작한 그래픽
- 개인 개발 화면 캡처는 공개 업로드에서 제외
- 한글 설명서, 검증 기록, 공개용 자동 검사

## 제외

실제 블로그 HTML·제목·본문, 가져오기 보고서의 개인 경로, SQLite 및 수정 이력, 모델 캐시, 실행 제어 토큰·로그, 가상환경, 로컬 설정, 바탕화면 바로가기, 초기 연습 코드와 개인 백업은 포함하지 않습니다.

최초 공개본(2026-11-12)의 파일 수와 Git 객체 ID는 `docs/package_manifest.json`에 기록되어 있습니다. 자동 설치판이 추가된 현재 파일 목록과는 다르며, 설치 EXE의 검증값은 각 GitHub Release의 `SHA256SUMS.txt`에서 확인합니다. 이 목록은 자신을 제외한 공개 파일들의 Git blob 객체 ID를 포함합니다. 이 ID는 파일의 내용과 Git 객체 형식을 기준으로 계산됩니다.

## 외부 구성 요소

| 구성 요소 | 출처·용도 |
|---|---|
| Python | https://www.python.org/ — 실행 언어 |
| Streamlit | https://docs.streamlit.io/ — 웹 화면 |
| Sentence Transformers | https://sbert.net/ — 임베딩과 유사도 |
| 다국어 MiniLM 모델 | https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 — 사전 학습된 공개 모델 |
| Beautiful Soup | https://www.crummy.com/software/BeautifulSoup/ — HTML 파싱 |
| NumPy | https://numpy.org/ — 벡터 연산·캐시 |
| SQLite | Python 표준 라이브러리 `sqlite3` — 개인 글 저장 |

모델 가중치와 라이브러리는 이 패키지에 동봉하지 않습니다. 각 구성 요소의 이용 조건은 해당 프로젝트의 라이선스를 따릅니다. 저장소 자체의 오픈소스 라이선스는 소유자가 정하지 않아 임의로 부여하지 않았습니다. 공개 저장소라는 이유만으로 자유로운 재사용 허가가 자동 부여되는 것은 아닙니다.

네이버나 SK의 공식 서비스·공식 프로젝트로 표시하지 않습니다. 개인 학습·포트폴리오 프로젝트입니다.
