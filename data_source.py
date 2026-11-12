import json
from pathlib import Path


def choose_data_file(project):
    project = Path(project).resolve()
    settings = project / 'local_settings.json'
    if not settings.exists():
        return project / 'sample_data' / 'posts.json', True
    config = json.loads(settings.read_text(encoding='utf-8'))
    if not isinstance(config, dict) or not isinstance(config.get('posts_file'), str):
        raise ValueError('개인 설정의 posts_file 항목을 확인해 주세요.')
    selected = (project / config['posts_file']).resolve()
    if not selected.is_relative_to(project):
        raise ValueError('데이터는 프로젝트 폴더 안에 있어야 합니다.')
    if not selected.is_file():
        raise ValueError('개인 데이터 파일을 찾지 못했습니다. local_settings.json을 확인해 주세요.')
    return selected, False

