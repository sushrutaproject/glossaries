"""Bring the headword readings made by eye (by Claude, from the contact sheets of sheets.py) into entries.json.
Run after lexcheck.py; running it again changes nothing.

  python readings.py [path to mw_keys.txt]

A reading made by eye is independent of Tesseract's habits, and in a blind trial it was right where two agreeing OCR
readings were wrong.  So where there is one, it becomes the headword, and the status says what supports it:
  ok        supported by an OCR reading or by the word list (Monier-Williams), and not marked uncertain by the reader
  probable  supported by neither; or marked uncertain but supported
  check     marked uncertain and unsupported, or not legible (the OCR reading is kept)
Entries that were not read keep the status that lexcheck.py gave them.  Each entry read gets 'eye': the reading as given.
"""
import glob, json, os, re, sys
from collections import Counter
from indic_transliteration import sanscript
from columns import WORK
from parse import la, norm
from lexcheck import Lexicon, reading, deva


def collect():
    """{entry id: reading}; a later batch wins"""
    out = {}
    for kf in sorted(glob.glob(f'{WORK}/claude/*/key.json')):
        rf = kf.replace('key.json', 'readings.json')
        if not os.path.exists(rf): print('no readings:', kf); continue
        K, R = json.load(open(kf)), json.load(open(rf))
        for sh, ids in K.items():
            if len(R.get(sh, [])) != len(ids): print('wrong number of readings:', rf, sh); continue
            out.update(zip(ids, R[sh]))
    return out


def tidy(r):
    """the reading as a headword: no dashes, parentheses or spaces"""
    return la(re.sub(r'[\s()\-–—‌‍.,?]', '', r))


def main():
    lex = Lexicon(sys.argv[1] if len(sys.argv) > 1 else f'{WORK}/lex/mw_keys.txt')
    data = json.load(open(f'{WORK}/entries.json'))
    entries = data['entries']; by_id = {e['id']: e for e in entries}
    R = collect(); n = Counter(); was = Counter()

    def stem_of(e):
        par = by_id.get(e.get('parent')) if e['kind'] == 'sub' else None
        return re.sub(r'[^\u0900-\u097f]', '', par.get('stem') or '') or par['hw'] if par else ''

    for e in entries:                                      # main headwords first: the sub-entries need their parents
        e.pop('eye', None)
    for kind in ('main', 'sub'):
        for e in entries:
            if e['kind'] != kind or e['id'] not in R: continue
            raw = R[e['id']]; unsure = raw.strip().endswith('?'); r = tidy(raw)
            e['eye'] = raw
            if not r:
                e['status'] = 'check'; n['not legible'] += 1
                if not re.search(r'[\u0900-\u097f]', e['hw']): e['hw'] = ''          # no headword at all: build.py leaves it out
                continue
            if e.get('var'):                               # अपार्थ(क): the optional ending is kept apart
                v = tidy(e['var'])
                if v and r.endswith(v) and norm(r[:-len(v)]) in {norm(la(w)) for w in e['wit'].values()}: r = r[:-len(v)]
            s = reading(r); stem = reading(stem_of(e))
            if stem:
                lv = 'mw' if lex.has(stem + s) else 'member' if len(s) >= 2 and lex.has(s) else 'none'
            else:
                lv = lex.level(s) or 'none'
            ocr = norm(r) in {norm(la(w)) for w in e['wit'].values()}
            sup = ocr or lv != 'none'
            was[e['status'], 'same' if norm(r) == norm(e['hw']) else 'changed'] += 1
            e['hw'] = r; e['lex'] = lv
            e['status'] = ('probable' if unsure else 'ok') if sup else ('check' if unsure else 'probable')
            n['supported by OCR and word list' if ocr and lv != 'none' else 'by OCR only' if ocr else
              'by word list only' if lv != 'none' else 'by neither'] += 1
            n['marked uncertain'] += unsure
    for e in entries:                                      # full forms, also of the unread sub-entries of a changed parent
        if e['kind'] == 'sub' and e.get('parent') in by_id:
            st, m = reading(stem_of(e)), reading(e['hw'])
            e['full'] = deva(st + m) if st and m else stem_of(e) + e['hw']
        else:
            e['full'] = e['hw']
        e['iast'] = sanscript.transliterate(e['full'], sanscript.DEVANAGARI, sanscript.IAST)
    json.dump(data, open(f'{WORK}/entries.json', 'w'), ensure_ascii=False)
    print('readings', len(R), dict(n))
    print('against the reading before:', {f'{a} {b}': v for (a, b), v in sorted(was.items())})
    print('status now:', dict(Counter(e['status'] for e in entries)))


if __name__ == '__main__':
    main()
