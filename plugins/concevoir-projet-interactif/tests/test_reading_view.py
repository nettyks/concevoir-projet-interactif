from html.parser import HTMLParser
import json
from pathlib import Path
import tempfile
import unittest

from test_render_artifact import render_artifact, valid_questionnaire, valid_planning


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.tags = []
        self.text = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.text.append(data)


class ReadingViewTests(unittest.TestCase):
    def generate(self, kind, data):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.json'
            target = Path(directory) / 'reading.html'
            source.write_text(json.dumps(data))
            render_artifact.render(kind, source, target, read_only=True)
            return Document(target.read_text())

    def assert_read_only(self, doc, locale):
        self.assertFalse({'script', 'input', 'textarea', 'select', 'form', 'button', 'iframe'} & {tag for tag, _ in doc.tags})
        self.assertFalse(any('contenteditable' in attrs or any(k.startswith('on') for k in attrs) for _, attrs in doc.tags))
        self.assertIn(('html', {'lang': locale}), doc.tags)

    def test_questionnaire_keeps_every_question_and_choice_as_readable_text(self):
        for locale in ('fr', 'en'):
            data = valid_questionnaire()
            data['locale'] = locale
            hostile = '<script>alert("x")</script> __READING_THEME__'
            data['sections'][0]['questions'][0]['title'] = hostile
            doc = self.generate('questionnaire', data)
            self.assert_read_only(doc, locale)
            text = ' '.join(doc.text)
            self.assertIn(hostile, text)
            for section in data['sections']:
                for question in section['questions']:
                    self.assertIn(question['title'], text)
                    for choice in question.get('choices', []):
                        self.assertIn(choice['label'], text)
                    for field in ['description', 'note_placeholder', 'answer_placeholder']:
                        if field in question:
                            self.assertIn(question[field], text)
                    if question['type'] == 'scale':
                        self.assertIn(question['scale']['min_label'], text)
                        self.assertIn(question['scale']['max_label'], text)

    def test_plan_has_both_reading_views_and_keeps_decision_details(self):
        for locale in ('fr', 'en'):
            data = valid_planning()
            data['locale'] = locale
            data['columns'] = [{'id': 'custom', 'title': 'Custom status'}]
            for segment in data['segments']:
                segment['status'] = 'custom'
            doc = self.generate('planning', data)
            self.assert_read_only(doc, locale)
            text = ' '.join(doc.text)
            self.assertIn('Kanban', text)
            self.assertIn('Roadmap', text)
            self.assertIn('Custom status', text)
            self.assertTrue(any(tag == 'a' and attrs.get('href') == '../questionnaire-actif.html' for tag, attrs in doc.tags))
            for segment in data['segments']:
                for key in ('title', 'objective'):
                    self.assertIn(segment[key], text)
                for key in ('dependencies', 'decision_refs', 'deliverables', 'acceptance', 'prerequisites', 'risks', 'questions'):
                    for value in segment[key]:
                        self.assertIn(value, text)

    def test_conflicting_modes_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'reading.html'
            target.write_text('original')
            with self.assertRaises(render_artifact.ConfigError):
                render_artifact.render('questionnaire', Path(directory) / 'absent.json', target, inline=True, read_only=True)
            self.assertEqual(target.read_text(), 'original')


if __name__ == '__main__':
    unittest.main()
