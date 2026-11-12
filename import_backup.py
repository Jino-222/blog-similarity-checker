from pathlib import Path
from datetime import datetime
import json
import re

from bs4 import BeautifulSoup


PROJECT = Path(__file__).resolve().parent


def read_post(path):
    html = path.read_text(encoding="utf-8-sig")
    soup = BeautifulSoup(html, "html.parser")

    title_node = soup.select_one(".se-title-text")
    body_node = soup.select_one(".se-main-container")

    if title_node is None or body_node is None:
        raise ValueError("지원하는 제목·본문 구조를 찾지 못했습니다.")

    title = title_node.get_text("", strip=True)

    # 실행 코드와 화면 꾸미기 정보는 제외합니다.
    for node in body_node.select("script, style"):
        node.decompose()

    # 문단 내부의 강조 표시 때문에 단어가 갈라지지 않도록 읽습니다.
    paragraphs = []
    for node in body_node.select(".se-text-paragraph"):
        text = node.get_text("", strip=False)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            paragraphs.append(text)

    if not title or not paragraphs:
        raise ValueError("제목 또는 본문이 비어 있습니다.")

    folder_info = re.match(r"^(\d{8})_(\d+)_", path.parent.name)

    return {
        "post_id": folder_info.group(2) if folder_info else None,
        "date_from_folder": folder_info.group(1) if folder_info else None,
        "title": title,
        "paragraphs": paragraphs,
        "body": "\n\n".join(paragraphs),
        "source_file": str(path.resolve()),
    }


def main():
    entered = input(
        "압축을 푼 백업 폴더 경로를 붙여 넣고 Enter: "
    ).strip().strip('"')

    if not entered:
        print("폴더 경로를 입력하지 않았습니다.")
        return

    root = Path(entered)
    if not root.is_dir():
        print("폴더를 찾지 못했습니다. 경로를 확인해 주세요.")
        return

    files = sorted(root.rglob("index.html"))
    if not files:
        print("이 폴더 안에서 index.html 파일을 찾지 못했습니다.")
        return

    print(f"\n발견한 HTML 파일: {len(files)}개")
    posts = []
    errors = []
    duplicates = []
    seen = set()

    for number, path in enumerate(files, start=1):
        try:
            post = read_post(path)
            key = post["post_id"] or post["source_file"]

            if key in seen:
                duplicates.append({
                    "file": str(path),
                    "reason": "같은 글 번호가 이미 포함되어 있습니다.",
                })
            else:
                seen.add(key)
                posts.append(post)

        except Exception as error:
            errors.append({
                "file": str(path),
                "reason": str(error),
            })

        if number % 20 == 0 or number == len(files):
            print(f"읽는 중: {number}/{len(files)}")

    # 실행할 때마다 새 폴더를 만들어 이전 결과를 보존합니다.
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output = PROJECT / "data" / f"import_{stamp}"
    output.mkdir(parents=True, exist_ok=False)

    (output / "posts.json").write_text(
        json.dumps(posts, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report = {
        "backup_folder": str(root.resolve()),
        "found_files": len(files),
        "imported_posts": len(posts),
        "failed_files": errors,
        "duplicate_files": duplicates,
    }
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    preview = []
    for post in posts[:3]:
        preview.append(
            f"제목: {post['title']}\n"
            f"본문 문단 수: {len(post['paragraphs'])}\n"
            f"본문 앞부분:\n{post['body'][:600]}\n"
        )

    (output / "preview.txt").write_text(
        "\n" + ("\n" + "=" * 50 + "\n").join(preview),
        encoding="utf-8",
    )

    print("\n가져오기 완료")
    print(f"저장한 글: {len(posts)}개")
    print(f"읽지 못한 파일: {len(errors)}개")
    print(f"같은 글 번호로 제외한 파일: {len(duplicates)}개")
    print(f"\n저장 위치: {output}")
    print("\n원본 백업과 기존 titles.txt는 변경하지 않았습니다.")
    print("아직 검사 화면에 연결된 것은 아닙니다.")


if __name__ == "__main__":
    main()