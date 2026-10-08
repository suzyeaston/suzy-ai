import json
import os
import tempfile
import unittest
from unittest.mock import patch

from suzy_ai import memory
from suzy_ai.chat import chat


class RecallTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        env = patch.dict(os.environ, {'SUZY_AI_HOME': tmp.name})
        env.start()
        self.addCleanup(env.stop)

    def add(self, title, text):
        return memory.add(title=title, text=text, source='synthetic test', approved=True)

    def test_default_recall_includes_humour_without_matching_topic(self):
        note = self.add('Humour / music / band-name wordplay', 'Six synthetic jokes about accordions.')
        class Adapter:
            model = 'fake'
            def complete(self, messages, max_tokens):
                self.messages = messages
                return 'Synthetic answer'
        adapter = Adapter()
        result = chat({'message': 'Say something funny'}, adapter)
        self.assertEqual(result['sources'][0]['id'], note['id'])
        self.assertIn(note['text'], adapter.messages[-2]['content'])
        self.assertFalse(result['stored'])
        with patch('suzy_ai.chat.memory.recall') as recall:
            result = chat({'message': 'Say something funny', 'use_memory': False}, adapter)
            recall.assert_not_called()
        self.assertEqual(result['sources'], [])

    def test_background_requires_title_label_and_deduplicates(self):
        note = self.add('Humour examples', 'Accordions and orchestras.')
        self.add('Unrelated incident', 'Someone mentioned humour here.')
        results = memory.recall('accordions')
        self.assertEqual([r['id'] for r in results], [note['id']])
        self.assertEqual(memory.recall('xyzzy')[0]['id'], note['id'])

    def test_short_thread_keeps_all_replies(self):
        text = ' '.join('reply%d' % i for i in range(120))
        self.add('Humour thread', text)
        self.assertEqual(memory.recall('reply0')[0]['excerpt'], text)

    def test_recall_budget_deletion_and_empty_store(self):
        self.assertEqual(memory.recall('hello'), [])
        notes = [self.add(f'Humour {i}', 'accordions ' * 180) for i in range(8)]
        results = memory.recall('accordions', limit=3)
        self.assertLessEqual(len(results), 3)
        self.assertLessEqual(sum(len(json.dumps(r, ensure_ascii=False)) for r in results), 6000)
        for note in notes:
            memory.delete(note['id'])
        self.assertEqual(memory.recall('accordions'), [])
