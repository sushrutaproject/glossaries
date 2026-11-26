"""The public search page, made from the public concordance alone (so nothing private can reach it).

  python make_page.py DATA_DIR PAGE.html      e.g. ../data ../../docs/ayurvediya-sabdakosa-1968/index.html

Packs concordance.json into short rows inside template.html:
  e  entries    [headword, genders, pdf page, column (0 left, 1 right), status (0 ok, 1 probable, 2 check), parent id or 0,
                 flags (1 read by eye, 2 a form of the entry 'parent' rather than a sub-entry), regions, variant, member]
                regions: [pdf page, x, y, width, height] in hundredths of a per cent of the page image
  r  citations  [entry id, text, sthana, chapter, verse, commentator], the three names as numbers into t, s, c
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = {'पुं.': 'm', 'स्त्री.': 'f', 'न.': 'n', 'वि.': 'a', 'अ.': 'i'}
STATUS = {'ok': 0, 'probable': 1, 'check': 2}


def main():
    src, dest = sys.argv[1], sys.argv[2]
    d = json.load(open(f'{src}/concordance.json'))
    assert d.get('public') is True
    rows = []
    for e in d['entries']:
        while len(rows) < e['id'] - 1: rows.append(['', '', 0, 0, 2, 0, 0, []])      # an id left out of the public data
        assert e['id'] == len(rows) + 1
        regs = []
        for p, r in e['scan_regions']:
            x, y, w, h = (round(float(v) * 100) for v in r[4:].split(','))
            regs.append([p, x, y, w, h])
        h = e['headword']
        row = [h['deva'], ''.join(GEN[g] for g in e['gender']), e['pdf_page'], int(e['column'] == 'right'), STATUS[h['status']],
               e.get('parent') or e.get('form_of') or 0, (1 if h.get('read') == 'eye' else 0) | (2 if e.get('form_of') else 0), regs]
        if e.get('variant') or e.get('member'): row += [e.get('variant', ''), e.get('member', '')]
        rows.append(row)
    tables = [[], [], []]
    def num(t, v):
        if v not in t: t.append(v)
        return t.index(v)
    num(tables[1], ''); num(tables[2], '')
    refs = [[r[0], num(tables[0], r[1]), num(tables[1], r[2]), r[3], r[4], num(tables[2], r[5])] for r in d['refs']]
    payload = dict(public=True, e=rows, r=refs, t=tables[0], s=tables[1], c=tables[2])
    blob = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    html = open(f'{HERE}/template.html').read().replace('__DATA__', blob)
    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    open(dest, 'w').write(html)
    print('page', dest, len(html), 'bytes;', len(rows), 'entries,', len(refs), 'citations')


if __name__ == '__main__':
    main()
