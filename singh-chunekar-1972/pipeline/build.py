"""Build the SQLite database + JSON payload for the offline search page.

inputs : work/entries.json (from parse.py), work/ocr/NNN.txt (all pages)
outputs: out/brhattrayi_glossary.sqlite, out/data.json
"""
import sys, re, json, sqlite3, os, unicodedata, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lines import fold, fix_diacritics

WORK, OUT = os.environ.get('GLOSSARY_WORK', 'work'), os.environ.get('GLOSSARY_OUT', 'out')
OFFSET = 24
os.makedirs(OUT, exist_ok=True)

SECTIONS = [(1, 24, 'Front matter'), (25, 498, 'Glossary'),
            (499, 515, 'Index of Latin and English names'),
            (516, 558, 'General index of Sanskrit and other Indian names'),
            (559, 561, 'List of books and journals referred to'),
            (562, 562, 'Supplement'), (563, 568, 'Errata')]

def section_of(p):
    for a, b, n in SECTIONS:
        if a <= p <= b:
            return n

def book_page(p):
    if p >= 25:
        return str(p - OFFSET)
    return ''

# 'C. S.', 'S. S.', 'A. H.' and their OCR variants: 's. S.', '|S. S.', '$. S.', 'C..S.', 'S. 8S.'
REF_START = re.compile(r"^[\s'‘’“”\"‚|\-`.]{0,4}([CcSsA$85])\s*[\.,:;\-]{0,2}\s*['‘]?(S|H|8|9|5|\$)\s*[\.,;S]{0,2}\s*(?=[A-Z][a-z]|U\b|U\.|\d)")
PROSE = re.compile(r"[^\W\d_]{3,}\s+(?:[^\W\d_]{2,}\s+){2,}[^\W\d_]{3,}")   # four words in a row
REF_KEY = {'C': 'C', 'c': 'C', 'S': 'S', 's': 'S', '$': 'S', '8': 'S', '5': 'S', 'A': 'A'}
# a citation line whose indentation was lost (page breaks): accept if a sthāna and number follow
REF_STRONG = re.compile(r"^(Su|Sū|Ni|Vi|Sa|In|Ci|CI|Ka|Si|U)[\.,:]?\s*\d")
STHANA = {'su': 'Sū', 'sū': 'Sū', 'ni': 'Ni', 'vi': 'Vi', 'sa': 'Śā', 'śa': 'Śā', 'in': 'In',
          'ci': 'Ci', 'cl': 'Ci', 'c1': 'Ci', 'ka': 'Ka', 'si': 'Si', 'u': 'U', 'ut': 'U'}
TEXTS = {'C': 'C.S.', 'S': 'S.S.', 'A': 'A.H.'}

def is_numericish(t):
    letters = len(re.findall(r'[A-Za-z]', t))
    digits = len(re.findall(r'\d', t))
    return digits >= 2 and digits >= letters

def dehyphen(lines):
    out = ''
    for t in lines:
        t = t.strip()
        if not out:
            out = t
        elif re.search(r'[a-z]-$', out) and re.match(r'^[a-z]', t):
            out = out[:-1] + t
        else:
            out += ' ' + t
    return re.sub(r'\s+', ' ', out)

def parse_refs(text_key, s):
    """'Su. 27. 32, 93, 99; Vi. 8. 150; Ci. 7. 168; 14. 124' -> list of (sthana, ch, v)"""
    s = re.sub(r'\([^)]*\)', ' ', s)         # (2), ( Va. ... ), (cf. ...)
    s = s.replace(':', ';')
    s = re.sub(r'[\.,]\s*(?=(Su|Sū|Ni|Vi|Sa|Śa|In|Ci|CI|Ka|Si|U)[\.,]\s*\d)', '; ', s)
    out, sth = [], None
    for grp in s.split(';'):
        g = grp.strip()
        m = re.match(r"^([A-Za-zŚśūŪ1]{1,2})[\.,]?\s+(.*)$", g)
        if m and m.group(1).lower() in STHANA:
            sth = STHANA[m.group(1).lower()]; g = m.group(2)
        if sth is None:
            continue
        m = re.match(r"^(\d+(?:\s*-\s*\d+)?)\s*[\.,]\s*(.*)$", g)
        if not m:
            continue
        ch = m.group(1).replace(' ', '')
        verses = re.findall(r'\d+(?:\s*-\s*\d+)?', m.group(2))
        if not verses:
            out.append((TEXTS[text_key], sth, ch, ''))
        for v in verses:
            out.append((TEXTS[text_key], sth, ch, v.replace(' ', '')))
    return out

def structure(e, margin_by_page):
    """split body lines into identification / references / discussion paragraphs"""
    ident, refs, paras = [], collections.OrderedDict(), []
    cur_ref, cur_para, seen_ref = None, None, False
    for b in e['body']:
        t = b['text'].strip()
        indent = b['left'] - margin_by_page.get(b['pdf_page'], 130) > 45
        m = REF_START.match(t)
        if m and PROSE.search(t):
            m = None                          # a sentence that merely begins with a citation
        if m and (indent or REF_STRONG.match(t[m.end():])) and not (m.group(1) in '85' and not REF_STRONG.match(t[m.end():])):
            k = REF_KEY[m.group(1)]
            cur_ref = k; seen_ref = True; cur_para = None
            refs.setdefault(k, []).append(t[m.end():])
            continue
        if cur_ref and not indent and is_numericish(t) and not PROSE.search(t):
            refs[cur_ref].append(t); continue
        cur_ref = None
        if not seen_ref:
            ident.append(t); continue
        if indent or cur_para is None:
            cur_para = [t]; paras.append(cur_para)
        else:
            cur_para.append(t)
    refs = {TEXTS[k]: dehyphen(v) for k, v in refs.items()}
    return [dehyphen([l]) for l in ident], refs, [dehyphen(p) for p in paras]

PAGE_H, TEXT_TOP, LINE_H = 2387, 150, 52     # 300-dpi render geometry

def segments(e):
    """vertical extent of the entry on each page, as IIIF percentages:
    [[pdf_page, y_pct, h_pct], ...]  (full page width)"""
    start = (e['heads'][0]['pdf_page'], max(TEXT_TOP, e['heads'][0]['top'] - 12))
    if e['body']:
        last = e['body'][-1]
        end = (last['pdf_page'], last['top'] + LINE_H)
    else:
        end = (e['heads'][-1]['pdf_page'], e['heads'][-1]['bottom'] + 14)
    out = []
    for p in range(start[0], end[0] + 1):
        y0 = start[1] if p == start[0] else TEXT_TOP
        y1 = end[1] if p == end[0] else PAGE_H - 60
        y1 = min(max(y1, y0 + LINE_H), PAGE_H)
        out.append([p, round(100 * y0 / PAGE_H, 2), round(100 * (y1 - y0) / PAGE_H, 2)])
    return out

def main():
    entries = json.load(open(f'{WORK}/entries.json'))
    margin = {}
    for e in entries:
        for h in e['heads']:
            margin[h['pdf_page']] = h['margin']
    db_path = f'{OUT}/brhattrayi_glossary.sqlite'
    if os.path.exists(db_path):
        os.remove(db_path)
    db = sqlite3.connect(db_path)
    db.executescript(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')).read())
    payload = dict(entries=[], pages=[], refs=[])
    for i, e in enumerate(entries, 1):
        pages = sorted({e['pdf_page']} | {b['pdf_page'] for b in e['body']})
        ident, refs, paras = structure(e, margin)
        heads = [dict(deva=h['deva'], iast=h['iast'], roman=h['roman'], status=h['status'])
                 for h in e['heads']]
        status = 'ok' if all(h['status'] == 'ok' for h in heads) else (
            'check' if any(h['status'] == 'check' for h in heads) else 'probable')
        rec = dict(id=i, pdf=[pages[0], pages[-1]], heads=heads, status=status,
                   ident=ident, refs=refs, paras=paras, seg=segments(e))
        payload['entries'].append(rec)
        full = '\n'.join(ident + [f'{k} {v}' for k, v in refs.items()] + paras)
        db.execute('INSERT INTO entries VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
            i, ' / '.join(h['iast'] for h in heads), ' / '.join(h['deva'] for h in heads),
            ' '.join(fold(h['iast']) for h in heads), status,
            pages[0], pages[-1], book_page(pages[0]), book_page(pages[-1]),
            '\n'.join(ident), refs.get('C.S.', ''), refs.get('S.S.', ''), refs.get('A.H.', ''),
            '\n\n'.join(paras), full))
        for n, h in enumerate(heads):
            db.execute('INSERT INTO headwords VALUES (?,?,?,?,?,?)',
                       (i, n, h['iast'], h['deva'], fold(h['iast']).replace(' ', ''), h['status']))
        for k, v in refs.items():
            for t, sth, ch, vs in parse_refs({'C.S.': 'C', 'S.S.': 'S', 'A.H.': 'A'}[k], v):
                db.execute('INSERT INTO refs VALUES (?,?,?,?,?)', (i, t, sth, ch, vs))
                payload['refs'].append([i, t, sth, ch, vs])
    for p in range(1, 569):
        f = f'{WORK}/ocr/{p:03d}.txt'
        txt = open(f).read().strip() if os.path.exists(f) else ''
        db.execute('INSERT INTO pages VALUES (?,?,?,?)', (p, book_page(p), section_of(p), txt))
        if section_of(p) != 'Glossary':
            payload['pages'].append([p, book_page(p), section_of(p), txt])
    db.execute("INSERT INTO entries_fts(entries_fts) VALUES('rebuild')")
    db.execute("INSERT INTO pages_fts(pages_fts) VALUES('rebuild')")
    db.commit()
    json.dump(payload, open(f'{OUT}/data.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('entries', len(entries), 'refs', len(payload['refs']))

if __name__ == '__main__':
    main()
