import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from suzy_ai import top_ten

ROOT = Path(__file__).resolve().parents[1]


class TopTenTests(unittest.TestCase):
    def setUp(self):
        self.thread = top_ten.read_json(ROOT/'examples/threads/mormon-music.json')
        self.draft = top_ten.read_json(ROOT/'examples/top-ten/mormon-music.json')

    def test_six_reply_source_supports_ten_draft_entries_without_source_mutation(self):
        original = copy.deepcopy(self.thread)
        result = top_ten.curated(self.thread, self.draft)
        self.assertEqual(len(top_ten.source_thread(self.thread)['items']), 6)
        self.assertEqual(len(result['draft']['entries']), 10)
        self.assertEqual(sum(not e['source_items'] for e in result['draft']['entries']), 4)
        self.assertEqual(self.thread, original)
        self.assertFalse(result['stored'])
        self.assertEqual(result['provider'], 'curated')

    def test_nested_replies_preserved_and_long_thread_selected(self):
        thread = top_ten.read_json(ROOT/'examples/threads/best-music-to-take-a-crap-to.json')
        source = top_ten.source_thread(thread)
        self.assertEqual(len(source['items']), 24)
        self.assertIn('baby got back',source['items'][0]['text'])
        self.assertIn('There is NEVER a reason',source['items'][15]['text'])
        draft = top_ten.read_json(ROOT/'examples/top-ten/best-music-to-take-a-crap-to.json')
        self.assertEqual(len(top_ten.curated(thread,draft)['draft']['entries']),10)

    def test_invalid_count_rank_duplicate_and_source_refs_rejected(self):
        variants=[]
        d=copy.deepcopy(self.draft);d['entries'].pop();variants.append(d)
        d=copy.deepcopy(self.draft);d['entries'].reverse();variants.append(d)
        d=copy.deepcopy(self.draft);d['entries'][-1]['rank']=True;variants.append(d)
        d=copy.deepcopy(self.draft);d['entries'][1]['text']=d['entries'][0]['text'];variants.append(d)
        for refs in ([7], [True], [-1], [1,1]):
            d=copy.deepcopy(self.draft);d['entries'][0]['source_items']=refs;variants.append(d)
        d=copy.deepcopy(self.draft);d['approved']=True;variants.append(d)
        for d in variants:
            with self.assertRaises(ValueError):top_ten.validate_draft(d,6)

    def test_fake_generation_is_draft_and_source_is_reference_data(self):
        calls=[]
        draft=self.draft
        class Fake:
            model='test-model'
            def complete(self,messages,max_tokens):
                calls.append((messages,max_tokens));return json.dumps(draft)
        result=top_ten.generate(self.thread,Fake())
        self.assertEqual(result['status'],'draft')
        self.assertEqual(result['provider'],'local-model')
        self.assertFalse(result['stored'])
        self.assertEqual(calls[0][1],2048)
        self.assertEqual(len(json.loads(calls[0][0][1]['content'])['items']),6)

    def test_bad_model_output_not_silently_repaired(self):
        class Fake:
            model='test-model'
            def complete(self,*args,**kwargs):return '{"entries":[]}'
        with self.assertRaises(ValueError):top_ten.generate(self.thread,Fake())

    def test_markdown_uses_explicit_descending_numbers_and_escapes_html(self):
        draft=copy.deepcopy(self.draft);draft['entries'][0]['text']='<script>alert(1)</script>'
        text=top_ten.markdown(top_ten.curated(self.thread,draft))
        self.assertLess(text.index('**10.**'),text.index('**1.**'))
        self.assertNotIn('<script>',text)
        self.assertIn('parody draft',text)

    def test_cli_renders_curated_without_inference(self):
        result=subprocess.run([sys.executable,'-m','suzy_ai.cli','top-ten',
            '--thread','examples/threads/mormon-music.json','--list','examples/top-ten/mormon-music.json',
            '--format','json'],cwd=ROOT,capture_output=True,text=True,check=True)
        self.assertEqual(json.loads(result.stdout)['provider'],'curated')
