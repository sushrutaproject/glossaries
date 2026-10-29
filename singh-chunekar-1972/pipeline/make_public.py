"""Derive the public concordance from the private build.

Keeps only factual/index data: headwords, page numbers, botanical binomials
(as indexed by the authors and found in the entry), and the parsed Saṃhitā
citations.  The authors' discussion, synonym lists, vernacular glosses and the
page OCR are NOT exported.

inputs : $GLOSSARY_OUT/data.json, $GLOSSARY_OUT/brhattrayi_glossary.sqlite, OCR of index pages
outputs: <dest>/data/concordance.json, entries.csv, citations.csv
"""
import os, sys, re, json, csv, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lines import fold
import assemble
from rapidfuzz import fuzz

OUT = os.environ.get('GLOSSARY_OUT', 'out')
DEST = sys.argv[1] if len(sys.argv) > 1 else 'public'          # folder for data/
SITE = sys.argv[2] if len(sys.argv) > 2 else None              # path of public search page
HERE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE_ID = 'Singh-Chunekar-1972'
os.makedirs(f'{DEST}/data', exist_ok=True)

d = json.load(open(f'{OUT}/data.json'))
latin = []
for kind, name, pages in assemble.parse_index(499, 515, 'Latin/English'):
    # an index line that lost its page numbers can be glued to the next name:
    # 'Cassia auriculata Linn. Cassia fistula Linn.' -> the pages belong to the last name
    parts = re.split(r'\s+(?=[A-Z][a-z]{3,} [a-z][a-z\-]{2,})', name)
    for extra in parts[:-1]:
        latin.append((kind, extra.strip(), []))
    latin.append((kind, parts[-1].strip(), pages))

def binomial_key(name):
    w = name.split()
    if len(w) >= 2 and re.match(r'^[A-Z][a-z]+$', w[0]) and re.match(r'^(x|[a-z][a-z\-]{2,}|sp\.?|Sp\.?)$', w[1]):
        return fold(w[0] + ' ' + w[1].lower())
    return None

by_page = {}
for _, name, pages in latin:
    k = binomial_key(name)
    if not k:
        continue
    for p in pages:
        by_page.setdefault(int(p), []).append((k, name))

# every binomial in the book's Latin index, by key, and the set of genera
all_names = {}
for _, name, pages in latin:
    k = binomial_key(name)
    if k:
        all_names.setdefault(k, name)
genera = {k.split()[0] for k in all_names}
BINOM = re.compile(r'\b([A-Z][a-z]{3,})\s+([a-z][a-z\-]{2,}[a-z])\b')

def binomials_in(lines, require_index):
    out = []
    for l in lines:
        for g, sp in BINOM.findall(l):
            k = fold(g + ' ' + sp)
            if k in all_names:
                out.append((k, all_names[k]))
            elif not require_index and fold(g) in genera and sp not in ('and', 'the', 'var', 'which', 'with', 'from'):
                out.append((k, f'{g} {sp}'))
    return out

def found_in(k, text):
    if not text:
        return False
    if k in text:
        return True
    return len(k) >= 10 and fuzz.partial_ratio(k, text) >= 90

entries, cit_rows, page_rows = [], [], []
for e in d['entries']:
    bp = [e['pdf'][0] - 24, e['pdf'][1] - 24]
    ident_t = re.sub(r'\s+', ' ', fold(' '.join(e['ident'])))
    para_t = re.sub(r'\s+', ' ', fold(' '.join(e['paras'])))
    ident, discussed, seen = [], [], set()
    for p in range(bp[0], bp[1] + 1):
        for k, name in by_page.get(p, []):
            if k in seen:
                continue
            if found_in(k, ident_t):
                ident.append(name); seen.add(k)
            elif found_in(k, para_t):
                discussed.append(name); seen.add(k)
    for k, name in binomials_in(e['ident'], require_index=False):
        if k not in seen:
            ident.append(name); seen.add(k)
    for k, name in binomials_in(e['paras'], require_index=True):
        if k not in seen:
            discussed.append(name); seen.add(k)
    entries.append(dict(
        id=e['id'],
        headwords=[dict(deva=h['deva'], iast=h['iast'], status=h['status']) for h in e['heads']],
        status=e['status'],
        book_pages=bp, pdf_pages=e['pdf'],
        scan=f'https://archive.org/details/{ARCHIVE_ID}/page/n{e["pdf"][0] - 1}/mode/1up',
        identification=ident, also_discussed=discussed,
        citations=e['refs'],
        scan_regions=[dict(pdf_page=p, iiif_region=f'pct:0,{y},100,{h}') for p, y, h in e['seg']]))
    page_rows.append(dict(id=e['id'], pdf=e['pdf'],
        heads=[dict(deva=h['deva'], iast=h['iast'], roman=h['roman'], status=h['status']) for h in e['heads']],
        status=e['status'], ident=ident, also=discussed, refs=e['refs'], paras=[], seg=e['seg']))

refs = [r for r in d['refs']]
meta = dict(
    title='Glossary of Vegetable Drugs in Bṛhattrayī — concordance',
    source='Thakur Balwant Singh & K. C. Chunekar, Glossary of Vegetable Drugs in Brhattrayi, '
           'Chowkhamba Sanskrit Studies 77, Varanasi: Chowkhamba Sanskrit Series Office, 1972.',
    scan=f'https://archive.org/details/{ARCHIVE_ID}',
    note='Headwords, page numbers, botanical names and citations only; the authors\' discussion is not included.',
    fields=dict(citations='[entry_id, text, sthana, chapter, verse]'))
public = dict(meta=meta, entries=entries, refs=refs, public=True)
json.dump(public, open(f'{DEST}/data/concordance.json', 'w'), ensure_ascii=False, indent=1)

with open(f'{DEST}/data/entries.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['id', 'headword_iast', 'headword_deva', 'ocr_status', 'book_page_start', 'book_page_end',
                'pdf_page', 'identification', 'also_discussed', 'refs_cs', 'refs_ss', 'refs_ah', 'scan_url'])
    for x in entries:
        w.writerow([x['id'], ' / '.join(h['iast'] for h in x['headwords']),
                    ' / '.join(h['deva'] for h in x['headwords']), x['status'],
                    x['book_pages'][0], x['book_pages'][1], x['pdf_pages'][0],
                    '; '.join(x['identification']), '; '.join(x['also_discussed']),
                    x['citations'].get('C.S.', ''), x['citations'].get('S.S.', ''),
                    x['citations'].get('A.H.', ''), x['scan']])
hw = {x['id']: ' / '.join(h['iast'] for h in x['headwords']) for x in entries}
with open(f'{DEST}/data/citations.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['entry_id', 'headword_iast', 'text', 'sthana', 'chapter', 'verse'])
    for r in refs:
        w.writerow([r[0], hw[r[0]], r[1], r[2], r[3], r[4]])
n_id = sum(1 for x in entries if x['identification'])
print(f'entries {len(entries)}  with identification {n_id}  citations {len(refs)}')

if SITE:
    os.makedirs(os.path.dirname(SITE), exist_ok=True)
    payload = dict(public=True, entries=page_rows, refs=refs, pages=[], errata=[], index=[])
    html = open(f'{HERE}/template.html').read()
    blob = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    html = (html.replace('__DATA__', blob).replace('__PDF__', '')
                .replace('__SUBTITLE__', 'concordance of headwords, botanical names and Saṃhitā citations, with page images from the Internet Archive'))
    open(SITE, 'w').write(html)
    print('site', SITE, len(html), 'bytes')
