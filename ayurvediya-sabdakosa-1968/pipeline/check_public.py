"""Gatekeeper for the public files of the Sabdakosa: run before every commit that touches
ayurvediya-sabdakosa-1968/data/ or docs/ayurvediya-sabdakosa-1968/.

The copyright status of the book is not established, so the public files may hold headwords, gender, page and column,
scan regions and parsed citations: never the glosses or the page OCR.  Fails (exit 1) if a field is not one of those,
or if two Devanagari words in a row (running text) occur anywhere.

    python3 check_public.py [repo_root]
"""
import json, os, re, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
DATA = os.path.join(ROOT, 'ayurvediya-sabdakosa-1968', 'data')
PAGE = os.path.join(ROOT, 'docs', 'ayurvediya-sabdakosa-1968', 'index.html')

FIELDS = {'id', 'headword', 'kind', 'gender', 'pdf_page', 'book_page', 'column', 'scan', 'scan_regions', 'n_citations',
          'parent', 'member', 'form_of', 'variant'}
HEAD = {'deva', 'iast', 'status', 'lex', 'read', 'out_of_order'}
RUN = re.compile(r'[ऀ-ॿ]+[\s,;|।]+[ऀ-ॿ]+')          # two Devanagari words in a row
WORD = re.compile(r'[ऀ-ॿ()]{1,40}')                           # a headword: one word
NUM = re.compile(r'[\d,\-\[\]p. ]*')
problems = []
bad = lambda s: problems.append(s) if len(problems) < 60 else None

d = json.load(open(f'{DATA}/concordance.json'))
if d.get('public') is not True: bad('concordance.json is not marked public')
if set(d) - {'meta', 'entries', 'refs', 'public'}: bad(f'unexpected top-level keys {sorted(set(d))}')
for e in d['entries']:
    if set(e) - FIELDS: bad(f"entry {e['id']}: unexpected fields {sorted(set(e) - FIELDS)}")
    if set(e['headword']) - HEAD: bad(f"entry {e['id']}: unexpected headword fields")
    for s in (e['headword']['deva'], e.get('member', ''), e.get('variant', '')):
        if s and not WORD.fullmatch(s): bad(f"entry {e['id']}: not a single word: {s[:60]}")
for r in d['refs']:
    if len(r) != 6 or not NUM.fullmatch(r[3]) or not NUM.fullmatch(r[4]) or len(r[2]) > 24 or re.search(r'[ऀ-ॿ]', ''.join(r[1:])):
        bad(f'citation not in index form: {r}')

html = open(PAGE, encoding='utf-8').read()
m = re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S)
p = json.loads(m.group(1).replace('<\\/', '</'))
if p.get('public') is not True: bad('page payload is not marked public')
if set(p) - {'public', 'e', 'r', 't', 's', 'c'}: bad(f'page payload: unexpected keys {sorted(set(p))}')
for i, row in enumerate(p['e'], 1):
    strings = [x for x in row if isinstance(x, str)]
    if len(row) > 10 or not (WORD.fullmatch(row[0]) or row[0] == '') or any(len(s) > 40 for s in strings): bad(f'page entry {i} is not in index form')

for name, text in (('concordance.json', open(f'{DATA}/concordance.json', encoding='utf-8').read()), ('page payload', m.group(1)),
                   ('entries.csv', open(f'{DATA}/entries.csv', encoding='utf-8').read()),
                   ('citations.csv', open(f'{DATA}/citations.csv', encoding='utf-8').read())):
    hit = RUN.search(text)
    if hit: bad(f'running Devanagari text in {name}: {hit.group(0)[:80]}')

if problems:
    print('PUBLIC DATA CHECK FAILED'); print('\n'.join(problems)); sys.exit(1)
print(f"public data OK: {len(d['entries'])} entries, {len(d['refs'])} citations, index fields only, no running text")
