import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from contextlib import closing

from data_source import choose_data_file
from import_backup import read_post
from post_manager import merged_posts, parse_url, save_post


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def test_mobile_and_pc_urls_match(self):
        self.assertEqual(parse_url('https://m.blog.naver.com/demo/123?from=x'),
                         parse_url('https://blog.naver.com/demo/123'))

    def test_postview_url(self):
        self.assertEqual(parse_url('https://blog.naver.com/PostView.naver?blogId=demo&logNo=123'),
                         ('123', 'https://blog.naver.com/demo/123'))

    def test_invalid_addresses(self):
        for address in ['https://example.com/demo/123', 'https://blog.naver.com/demo', 'javascript:alert(1)']:
            with self.subTest(address=address), self.assertRaises(ValueError):
                parse_url(address)

    def test_sample_default(self):
        self.assertEqual(choose_data_file(self.root), (self.root/'sample_data/posts.json', True))

    def test_private_selection(self):
        data = self.root/'posts.json'
        data.write_text('[]', encoding='utf-8')
        (self.root/'local_settings.json').write_text('{"posts_file":"posts.json"}', encoding='utf-8')
        self.assertEqual(choose_data_file(self.root), (data, False))

    def test_missing_private_file_does_not_fallback(self):
        (self.root/'local_settings.json').write_text('{"posts_file":"missing.json"}', encoding='utf-8')
        with self.assertRaises(ValueError):
            choose_data_file(self.root)

    def test_outside_path_rejected(self):
        (self.root/'local_settings.json').write_text('{"posts_file":"../outside.json"}', encoding='utf-8')
        with self.assertRaises(ValueError):
            choose_data_file(self.root)

    def test_insert_and_update_without_duplicate(self):
        db = self.root/'posts.sqlite3'
        post = {'post_id':'123', 'title':'가상 제목', 'body':'가상 본문', 'updated_at':'first'}
        save_post(db, post)
        edited = dict(post, body='수정한 가상 본문', updated_at='second')
        save_post(db, edited)
        self.assertEqual(merged_posts([], db), [edited])
        with closing(sqlite3.connect(db)) as connection:
            history = connection.execute('SELECT payload FROM history').fetchone()[0]
        self.assertEqual(json.loads(history), post)

    def test_imported_original_is_preserved(self):
        base = [{'post_id':'123', 'title':'기존 제목', 'body':'기존 본문'}]
        before = json.dumps(base)
        edited = dict(base[0], title='수정 제목', updated_at='now')
        db = self.root/'posts.sqlite3'
        save_post(db, edited, base[0])
        self.assertEqual(merged_posts(base, db), [edited])
        self.assertEqual(json.dumps(base), before)

    def test_blank_post_rejected(self):
        db = self.root/'posts.sqlite3'
        with self.assertRaises(ValueError):
            save_post(db, {'post_id':'123', 'title':' ', 'body':'본문', 'updated_at':'now'})
        self.assertFalse(db.exists())

    def test_html_title_and_paragraphs(self):
        folder = self.root/'20260101_123_샘플'
        folder.mkdir()
        html = folder/'index.html'
        html.write_text('<div class="se-title-text">가상 제목</div><div class="se-main-container"><script>ignore</script><p class="se-text-paragraph">첫 <b>문단</b>입니다.</p><p class="se-text-paragraph">둘째 문단입니다.</p></div>', encoding='utf-8')
        post = read_post(html)
        self.assertEqual(post['post_id'], '123')
        self.assertEqual(post['title'], '가상 제목')
        self.assertEqual(post['paragraphs'], ['첫 문단입니다.', '둘째 문단입니다.'])

    def test_unsupported_html_rejected(self):
        html = self.root/'index.html'
        html.write_text('<html><body>다른 구조</body></html>', encoding='utf-8')
        with self.assertRaises(ValueError):
            read_post(html)


if __name__ == '__main__':
    unittest.main()
