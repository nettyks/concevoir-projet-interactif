from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from test_render_artifact import render_artifact, valid_questionnaire, valid_planning


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class ConversationTests(unittest.TestCase):
    def test_fragment_preserves_questions_and_compiles_in_both_languages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for locale in ('fr', 'en'):
                data = valid_questionnaire()
                data['locale'] = locale
                data['sections'][0]['questions'][0]['title'] = '</script><script>bad()</script>'
                source = root / 'questions.json'
                output = root / 'questions.html'
                source.write_text(json.dumps(data))
                render_artifact.render('questionnaire', source, output, inline=True)
                html = output.read_text()
                tags = Tags(); tags.feed(html)
                self.assertFalse({'html', 'head', 'body', 'iframe', 'meta'} & {tag for tag, _ in tags.tags})
                self.assertEqual(sum(tag == 'script' for tag, _ in tags.tags), 1)
                self.assertLess(len(html.encode()), 1_000_000)
                script = re.search(r'<script>(.*?)</script>', html, re.S).group(1)
                encoded = re.search(r'const data = (.*);', script).group(1)
                recovered = json.loads(encoded)
                self.assertEqual(recovered['sections'][0]['questions'][0]['title'], data['sections'][0]['questions'][0]['title'])
                self.assertEqual(recovered['locale'], locale)
                self.assertEqual(len(recovered['sections'][0]['questions']), 6)
                self.assertFalse(any(attrs.get('src') for tag, attrs in tags.tags if tag == 'script'))
                if shutil.which('node'):
                    javascript = root / 'check.js'; javascript.write_text(script)
                    subprocess.run(['node', '--check', str(javascript)], check=True, capture_output=True)

    def test_inline_planning_is_rejected_without_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / 'plan.json'; output = root / 'plan.html'
            source.write_text(json.dumps(valid_planning())); output.write_text('original')
            with self.assertRaises(render_artifact.ConfigError):
                render_artifact.render('planning', source, output, inline=True)
            self.assertEqual(output.read_text(), 'original')

    @unittest.skipUnless(shutil.which('node'), 'Node.js required for conversation behavior tests')
    def test_conversation_behavior(self):
        result = subprocess.run(['node', '--test', str(Path(__file__).with_name('test_conversation.mjs'))],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
