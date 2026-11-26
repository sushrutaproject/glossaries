"""Entries + citations -> the public concordance (index data only) and a private file with the entry texts.

  python build.py DATA_DIR        e.g. ayurvediya-sabdakosa-1968/data

Public (DATA_DIR): concordance.json, entries.csv, citations.csv -- headwords, gender, page and column, scan regions and
parsed citations.  No glosses: the copyright status of the book is not established (see CLAUDE.md).
Private ($GLOSSARY_WORK/out/full.json): the same with the OCR text of every entry.
"""
import csv, json, math, os, re, sys
from collections import Counter
from columns import WORK, FIRST
from cite import citations
from parse import GENDERS

ITEM = 'ayurvediya-sabdakosa-v-1-1968'
W, H = 3296, 4672                                # the scan; IIIF regions are given in per cent of it
SOURCE = ('Veṇīmādhavaśāstrī Jośī & Nārāyaṇa Harī Jośī, Āyurvedīya Śabdakośa, vol. 1. '
          'Mumbaī: Mahārāṣṭra Rājya Sāhitya-Saṃskṛti Maṇḍaḷa, 1968.')


def regions(e, lines):
    """IIIF regions (one per column the entry runs through): [pdf page, 'pct:x,y,w,h']"""
    out = []
    groups = {}
    for n in e['lines']:
        l = lines[n]; groups.setdefault((l['p'], l['col']), []).append(l)
    for (p, col), ls in groups.items():
        hs = [(l['b'][3] - l['b'][1]) for l in ls]
        y0 = min(l['o'][1] - h / 2 for l, h in zip(ls, hs)) - 14
        y1 = max(l['o'][1] + h / 2 for l, h in zip(ls, hs)) + 14
        l = ls[0]; th = l['theta']; ym = (ls[0]['b'][1] + ls[-1]['b'][3]) / 2
        xr = W / 2 + (l['rule'] - W / 2) * math.cos(th) + (ym - H / 2) * math.sin(th)      # the rule in the unrotated scan
        x0 = xr - 1235 if col == 'L' else xr - 12
        x0 = max(0, x0); x1 = min(W, x0 + 1250)
        y0 = max(0, y0); y1 = min(H, y1)
        out.append([p, 'pct:%.2f,%.2f,%.2f,%.2f' % (100 * x0 / W, 100 * y0 / H, 100 * (x1 - x0) / W, 100 * (y1 - y0) / H)])
    return out


def entry_text(e, lines):
    parts = []
    for n in e['lines']:
        t = lines[n]['t']
        if parts and re.search(r'[ऀ-ॿ][-–]$', parts[-1]):      # a word divided at the line end
            parts[-1] = parts[-1][:-1] + t
        else:
            parts.append(t)
    return ' '.join(parts)


def main():
    dest = sys.argv[1]
    d = json.load(open(f'{WORK}/entries.json'))
    lines, entries = d['lines'], d['entries']
    stats = dict(resolved=Counter(), unresolved=Counter())
    pub, full, refs = [], [], []
    for e in entries:
        text = entry_text(e, lines)
        cs = citations(text, stats)
        seen = set()
        for c in cs:
            key = c[:5]
            if key in seen: continue
            seen.add(key); refs.append([e['id'], c[0], c[1], c[2], c[3], c[4]])
        rec = dict(id=e['id'], headword=dict(deva=e['full'], iast=e['iast'], status=e['status']), kind=e['kind'],
                   gender=[GENDERS[g] for g in e['genders']], pdf_page=e['p'], book_page=e['p'] - FIRST + 1,
                   column='left' if e['col'] == 'L' else 'right',
                   scan=f"https://archive.org/details/{ITEM}/page/n{e['p'] - 1}/mode/1up",
                   scan_regions=regions(e, lines), n_citations=len(seen))
        if e['kind'] == 'sub':
            rec['parent'] = e.get('parent'); rec['member'] = e['hw']
        if e.get('form_of'): rec['form_of'] = e['form_of']
        if e.get('var'): rec['variant'] = e['var']
        if e.get('order') is False: rec['headword']['out_of_order'] = True
        pub.append(rec)
        full.append(dict(rec, text=text, witnesses=e['wit'], raw_citations=[c[5] for c in cs]))
    meta = dict(title='Āyurvedīya Śabdakośa, vol. 1 — index of headwords and citations', source=SOURCE,
                scan=f'https://archive.org/details/{ITEM}',
                note='Headwords, grammatical gender, page and column, and the citations of each entry only; the glosses are '
                     'not included. Read from the scan by OCR: see the status of each headword (ok / probable / check).',
                fields=dict(citations='[entry_id, text, sthana, chapter, verse, commentator]',
                            scan_regions='[pdf_page, IIIF region in per cent of the page image]'))
    os.makedirs(dest, exist_ok=True); os.makedirs(f'{WORK}/out', exist_ok=True)
    json.dump(dict(meta=meta, entries=pub, refs=refs, public=True), open(f'{dest}/concordance.json', 'w'),
              ensure_ascii=False, separators=(',', ':'))
    json.dump(dict(meta=meta, entries=full, refs=refs, public=False, unresolved=stats['unresolved'].most_common()),
              open(f'{WORK}/out/full.json', 'w'), ensure_ascii=False)
    by_id = {r['id']: r for r in pub}
    with open(f'{dest}/entries.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow('id headword_iast headword_deva ocr_status kind parent_id gender book_page pdf_page column n_citations scan_url'.split())
        for r in pub:
            w.writerow([r['id'], r['headword']['iast'], r['headword']['deva'], r['headword']['status'], r['kind'],
                        r.get('parent', ''), ' '.join(r['gender']), r['book_page'], r['pdf_page'], r['column'],
                        r['n_citations'], r['scan']])
    with open(f'{dest}/citations.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow('entry_id headword_iast text sthana chapter verse commentator'.split())
        for r in refs:
            w.writerow([r[0], by_id[r[0]]['headword']['iast']] + r[1:])
    res, unres = sum(stats['resolved'].values()), sum(stats['unresolved'].values())
    print(f'entries {len(pub)}  citations {len(refs)}  (abbreviation resolved {res}, not resolved {unres}: {100 * res / (res + unres):.1f}%)')
    print('entries with at least one citation:', sum(1 for r in pub if r['n_citations']))
    print('by text:', Counter(r[1] for r in refs).most_common())
    print('not resolved, commonest:', stats['unresolved'].most_common(25))


if __name__ == '__main__':
    main()
