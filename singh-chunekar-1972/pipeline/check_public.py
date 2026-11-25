"""Gatekeeper for the public files: run before every commit that touches
singh-chunekar-1972/data/ or docs/.

The book is in copyright. The public concordance may hold headwords, page
numbers, botanical binomials and citation strings, never the authors' prose.
This script fails (exit 1) if anything that looks like running English text,
or a known phrase from the discussion paragraphs, has crept in.

    python3 check_public.py [repo_root]
"""
import sys, os, re, json

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
DATA = os.path.join(ROOT, 'singh-chunekar-1972', 'data', 'concordance.json')
PAGE = os.path.join(ROOT, 'docs', 'singh-chunekar-1972', 'index.html')

# phrases that occur only in the authors' discussion / front matter
SENTINELS = ['decorticated', 'Arunadatta', 'is usually accepted', 'has been identified',
             'Synonym', 'Vanausadhi', 'Dalhana calls', 'PREFACE', 'controversial origin']
PROSE = re.compile(r'[^\W\d_]{3,}(?:\s+[^\W\d_]{2,}){4,}')          # five words in a row
ALLOWED_FIELDS = {'id', 'headwords', 'status', 'book_pages', 'pdf_pages', 'scan',
                  'identification', 'also_discussed', 'citations', 'scan_regions'}

# reviewed exceptions: the book's own short notes inside a citation list
KNOWN_OK = {(662, 'C.S.')}   # '( ... in the same Yoga in Su. 4.3, 4 )'

problems = []
d = json.load(open(DATA))
for e in d['entries']:
    extra = set(e) - ALLOWED_FIELDS
    if extra:
        problems.append(f"entry {e['id']}: unexpected fields {sorted(extra)}")
    for k, v in e['citations'].items():
        if PROSE.search(v) and (e['id'], k) not in KNOWN_OK:
            problems.append(f"entry {e['id']} {k}: prose in citation: {PROSE.search(v).group(0)[:80]}")
    for n in e['identification'] + e['also_discussed']:
        if len(n) > 80:
            problems.append(f"entry {e['id']}: suspiciously long botanical name: {n[:80]}")

html = open(PAGE, encoding='utf-8').read()
m = re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S)
payload = json.loads(m.group(1).replace('<\\/', '</'))
if not payload.get('public'):
    problems.append('page payload is not marked public')
if payload.get('pages') or payload.get('errata') or payload.get('index'):
    problems.append('page payload carries pages/errata/index (full-text material)')
for e in payload['entries']:
    if e.get('paras'):
        problems.append(f"page entry {e['id']} carries discussion paragraphs")
        break

for s in SENTINELS:
    for name, text in (('concordance.json', json.dumps(d, ensure_ascii=False)), ('index.html', m.group(1))):
        if s in text:
            problems.append(f"sentinel phrase '{s}' found in {name}")

if problems:
    print('PUBLIC DATA CHECK FAILED')
    print('\n'.join(problems[:50]))
    sys.exit(1)
print(f"public data OK: {len(d['entries'])} entries, {len(d['refs'])} citations, no prose found")
