# Windows 자동 설치판

## 설치

1. [다운로드 페이지](https://github.com/Jino-222/blog-similarity-checker/releases/latest)에서 `BlogSimilarityChecker-Setup.exe` 다운로드
2. 실행 후 **설치 시작** 선택
3. Python·라이브러리·AI 모델 준비가 끝나면 **검사기 실행** 선택
4. 이후 바탕화면의 **Blog Similarity Checker** 아이콘 사용

Windows 10/11 Intel·AMD 64비트용입니다. ARM Windows는 지원 대상으로 검증하지 않았습니다. 첫 설치에는 인터넷과 수 GB의 여유 공간이 필요하며 연결 상태에 따라 수 분 이상 걸릴 수 있습니다. 관리자 권한이나 기존 Python 설치는 필요하지 않습니다.

기존 Python과 PATH 설정은 바꾸지 않습니다. 설치 위치는 `%LOCALAPPDATA%\BlogSimilarityChecker`이며 전용 실행 환경은 `runtime`, 개인 데이터·모델·기록은 `data`에 보관합니다. 모델은 설치 중 다운로드하며, 검색 계산은 컴퓨터에서 수행합니다.

## 첫 체험

- 제목: `실내 식물 물 주는 방법`, 우선 찾을 단어: `실내 식물`
- 본문: **본문 검사 → 기존 글 일부로 테스트하기 → 본문 검사하기**
- 새 글: **글 등록·수정**에서 게시글 주소·제목·본문 등록
- 종료: 검사 화면 아래 **프로그램 종료** 선택

가상 샘플 글 3개를 제공하며 실제 개인 블로그 자료는 배포하지 않습니다. 네이버 백업 가져오기는 기존 [사용 안내](usage.md)를 참고하세요. 설치판에서 명령어가 필요할 때는 `.venv\Scripts\python.exe` 대신 `runtime\python.exe`를 사용합니다.

## 업데이트와 오류

- 프로그램을 종료한 뒤 새 설치 파일 실행. 같은 위치의 `data`와 `local_settings.json`은 유지
- 자동 업데이트 기능은 없음. 새 버전은 GitHub에서 내려받아 재설치
- 설치 중 인터넷 오류가 발생하면 연결을 확인하고 **다시 시도** 선택
- 설치 기록: `%LOCALAPPDATA%\BlogSimilarityChecker\data\install.log`
- 실행 기록: `%LOCALAPPDATA%\BlogSimilarityChecker\data\runtime\server.log`
- 다른 위치의 기존 검사기가 실행 중이면 종료한 뒤 설치판 실행
- 개인 프로젝트의 서명되지 않은 EXE로, Windows 실행 확인 메시지가 나타날 수 있음
- 회사·기관에서 실행이 차단된 경우 해당 관리 정책 확인

## 제거

검사 화면에서 프로그램을 종료한 뒤 필요한 `data`와 `local_settings.json`을 백업하세요. 설치 폴더 `%LOCALAPPDATA%\BlogSimilarityChecker`와 바탕화면·시작 메뉴의 바로가기를 제거하면 됩니다. Windows 앱 목록용 제거 프로그램은 제공하지 않습니다. 설치 폴더를 삭제하면 그 안의 개인 글과 수정 이력도 삭제됩니다.

## 제작과 검증

- `python installer/build.py`: 공개 파일만 포함한 EXE 및 SHA-256 목록 생성
- Python 3.11.9 Windows embedded 배포본, pip 25.3 wheel: 공식 출처에서 다운로드 후 고정 SHA-256 확인
- 의존성: PyPI 및 공식 PyTorch CPU 배포처 사용
- 모델: Sentence Transformers의 공개 다국어 MiniLM 모델
- Windows 자동 빌드에서 빈 폴더 설치·실제 AI 추론·제목 및 본문 검사 후 Release 공개
- CI 검증은 모든 개인 PC·백신·기업 보안 환경의 호환성을 보장하지 않음

Python embedded 배포본은 이 앱 전용입니다. 사용자의 일반 Python 개발 환경을 대신하지 않습니다.

## 검증 기록 (2026-11-13)

[Windows 자동 검증 실행](https://github.com/Jino-222/blog-similarity-checker/actions/runs/43339890769)

- GitHub Windows Server 2025의 빈 폴더에 전용 Python·의존성·모델 설치 성공
- 바탕화면 바로가기 생성 확인
- 설치된 Python으로 샘플 제목 검사·본문 검사·등록 화면 확인
- 준비 상태·중복 실행·인증된 종료 요청과 실행 정보 정리 확인
- 기존 자동 검사 12개 통과
- 공개 Release 파일 다운로드 및 SHA-256 일치 확인

모든 개인 PC와 보안 프로그램 조합에 대한 검증은 아니며, Windows 10/11의 개별 설치 환경에서 추가 확인이 필요할 수 있습니다.
