"""Second opinion for uncertain headwords from the book's own Sanskrit index
(pdf 516-558), whose regular-weight Devanagari OCRs much better than the bold
headings.  Updates work/entries.json in place."""
import os, sys, json, re, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import assemble, parse
from lines import fold, is_deva
from rapidfuzz.distance import Levenshtein

E = json.load(open(os.path.join(os.environ.get('GLOSSARY_WORK', 'work'), 'entries.json')))
idx = assemble.parse_index(516, 558, 'S')
by_page = {}
for _, name, pages in idx:
    deva = ' '.join(w for w in name.split() if is_deva(w))
    if not deva:
        continue
    k = parse.key(parse.translit(deva))
    for p in pages:
        by_page.setdefault(int(p), []).append((deva, k))

fixed = 0
for e in E:
    pages = sorted({h['pdf_page'] - 24 for h in e['heads']})
    for h in e['heads']:
        if h['status'] == 'ok' or re.search(r'[\(\[,—]|-[A-Z]', h['roman']):
            continue
        rk = parse.key(h['roman'])
        best = None
        for p in pages:
            for deva, k in by_page.get(p, []):
                d = Levenshtein.distance(k, rk)
                if best is None or d < best[0]:
                    best = (d, deva)
        if not best or best[0] > 0 or len(rk) < 3 or 'ँ' in best[1]:
            continue
        if h['deva']:
            od = parse.key(parse.translit(h['deva']))
            if Levenshtein.normalized_distance(od, parse.key(parse.translit(best[1]))) > 0.34:
                continue
        mg = parse.merge(parse.translit(best[1]), h['roman'])
        if not mg:
            continue
        num = ' '.join(re.findall(r'\(\d+\)', h['roman']))
        iast = parse.word_split(mg[0], h['roman']) if ' ' in best[1] else mg[0]
        h.update(deva=best[1], deva_src='book index', iast=unicodedata.normalize('NFC', (iast + ' ' + num).strip()),
                 status='ok' if mg[1] == 0 else 'probable')
        fixed += 1
json.dump(E, open(os.path.join(os.environ.get('GLOSSARY_WORK', 'work'), 'entries.json'), 'w'), ensure_ascii=False, indent=0)
print('headwords improved from index:', fixed)
