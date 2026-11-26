"""Check the headwords against a Sanskrit word list (Monier-Williams keys, SLP1) and use it as an independent witness.
Edits $GLOSSARY_WORK/entries.json in place: run it straight after parse.py.

  python lexcheck.py [path to mw_keys.txt, default $GLOSSARY_WORK/lex/mw_keys.txt]

The three OCR readings of a headword share Tesseract's mistakes, so their agreement alone is weak evidence.  Here:
  - a reading found in the word list (or made of two listed words) is confirmed;
  - a main headword not found is looked for among the listed words that fall alphabetically between its confirmed
    neighbours, and a sub-entry among the listed words that begin with its parent; a near match replaces the reading;
  - readings that agree are never overruled, except by a third reading one letter away that is a listed word;
  - status:  ok        two readings agree and the word list confirms them
             probable  the word list confirms or corrects, but the readings disagree; or they agree and the list is silent
             check     neither
Each entry gets 'lex': mw | compound | member | corrected | none.
"""
import bisect, json, os, re, sys
from collections import Counter, defaultdict
from indic_transliteration import sanscript
from rapidfuzz.distance import Levenshtein
from columns import WORK
from parse import la, norm, ORDER

slp = lambda s: sanscript.transliterate(s, sanscript.DEVANAGARI, sanscript.SLP1)
deva = lambda s: sanscript.transliterate(s, sanscript.SLP1, sanscript.DEVANAGARI)
key = lambda s: [ORDER[c] for c in s if c in ORDER]
VOWELS = set('aAiIuUfFxXeEoO')


def reading(v):
    """a witness reading as SLP1, letters only"""
    return re.sub(r'[^a-zA-Z]', '', slp(la(re.sub(r'[\s()‌‍`]', '', v))))


def nasal(s):
    """spelling variants folded for the lookup: anusvara before a stop as the class nasal (संप्लव / सम्प्लव), single or double t"""
    s = re.sub(r'M(?=[kKgG])', 'N', s); s = re.sub(r'M(?=[cCjJ])', 'Y', s); s = re.sub(r'M(?=[wWqQ])', 'R', s)
    s = re.sub(r'M(?=[tTdD])', 'n', s); s = re.sub(r'M(?=[pPbB])', 'm', s)
    return s.replace('ttr', 'tr').replace('ttv', 'tv')            # पत्त्र / पत्र, सत्त्व / सत्व


class Lexicon:
    def __init__(self, path):
        self.words = set(open(path).read().split())
        self.nasal = {nasal(w) for w in self.words}
        self.sorted = sorted(((key(w), w) for w in self.words))
        self.keys = [k for k, _ in self.sorted]
        self.by_len = defaultdict(list)
        for w in self.words: self.by_len[len(w)].append(w)
        self.by_prefix = defaultdict(list)
        for w in self.words:
            if len(w) >= 4: self.by_prefix[w[:3]].append(w)

    def has(self, s):
        return s in self.words or nasal(s) in self.nasal

    def compound(self, s):
        """two listed words, joined plainly or by vowel sandhi"""
        W = self.words
        for i in range(2, len(s) - 1):
            l, r = s[:i], s[i:]
            if len(r) < 3 or len(l) < 3: continue
            if l in W and r in W: return True
            c = s[i - 1]                                   # the vowel at the join
            l0 = s[:i - 1]
            if c == 'A' and (l0 + 'a' in W or l0 + 'A' in W) and ('a' + r in W or 'A' + r in W): return True
            if c == 'e' and (l0 + 'a' in W or l0 + 'A' in W) and ('i' + r in W or 'I' + r in W): return True
            if c == 'o' and (l0 + 'a' in W or l0 + 'A' in W) and ('u' + r in W or 'U' + r in W): return True
            if c == 'I' and (l0 + 'i' in W or l0 + 'I' in W) and ('i' + r in W or 'I' + r in W): return True
            if c == 'U' and (l0 + 'u' in W or l0 + 'U' in W) and ('u' + r in W or 'U' + r in W): return True
        return False

    def level(self, s):
        if self.has(s): return 'mw'
        if len(s) >= 7 and self.compound(s): return 'compound'
        return None

    def between(self, lo, hi):
        a, b = bisect.bisect_left(self.keys, lo), bisect.bisect_right(self.keys, hi)
        return [w for _, w in self.sorted[a:b]] if 0 <= b - a <= 4000 else None

    def near(self, s, pool, maxd):
        """(distance, word) of the listed words in pool nearest to s, if there is exactly one nearest within maxd"""
        best, hits = maxd + 1, []
        for w in pool:
            if abs(len(w) - len(s)) > maxd: continue
            d = Levenshtein.distance(s, w, score_cutoff=maxd)
            if d < best: best, hits = d, [w]
            elif d == best and d <= maxd: hits.append(w)
        return (best, hits[0]) if len(hits) == 1 else None


def astem(s, lex):
    """कन्द् read for कन्द: a final consonant that no stem ends in, where the a-stem is a listed word"""
    if len(s) > 2 and s[-1] not in VOWELS and s[-1] not in 'MH' and lex.has(s + 'a'):
        if s[-1] in 'hlkgwqRpbmyBGDJQKCWTP' or (s[-2] not in VOWELS and not lex.has(s)):
            return s + 'a'
    return s


def slip(a, b):
    """b differs from a by one letter, and not merely in the final vowel (which is the gender ending)"""
    if Levenshtein.distance(a, b) != 1: return False
    return not (a[:-1] == b[:-1] or a[:-1] == b or b[:-1] == a) or (a[-1] not in VOWELS and b[-1] not in VOWELS)


def choose(rs, lex, stem=''):
    """(reading, lex, agreed) from the witness readings; with a parent stem, the full form is looked up first"""
    votes = Counter(rs)
    agreed = [r for r, n in votes.items() if n >= 2]
    def level(r):
        if stem and lex.has(stem + r): return 'mw'
        if stem: return 'member' if len(r) >= 2 and lex.has(r) else None
        return lex.level(r)
    if agreed:
        a = agreed[0]
        for m in (a, astem(a, lex)):
            if level(m): return m, level(m), True
        for r in rs:                                       # one witness has a listed word, a letter away from the other two
            for m in (r, astem(r, lex)):
                if m != a and level(m) in ('mw', 'member') and slip(a, m) and len(m) >= 4: return m, level(m), False
        return a, 'none', True
    for want in ('mw', 'member', 'compound'):
        for r in rs:
            for m in (r, astem(r, lex)):
                if level(m) == want: return m, want, False
    return (rs[0] if rs else ''), 'none', False


def main():
    lex = Lexicon(sys.argv[1] if len(sys.argv) > 1 else f'{WORK}/lex/mw_keys.txt')
    data = json.load(open(f'{WORK}/entries.json'))
    entries = data['entries']; by_id = {e['id']: e for e in entries}
    how = Counter()
    for e in entries:
        e['_rs'] = [r for r in (reading(v) for v in e['wit'].values()) if r]
        e.pop('hw_ocr', None)
    # ---- main headwords
    mains = [e for e in entries if e['kind'] == 'main']
    for e in mains:
        e['_slp'], e['lex'], e['_agree'] = choose(e['_rs'], lex)
    anchors = [i for i, e in enumerate(mains) if e['lex'] == 'mw' and e['_agree']]
    for a, b in zip(anchors, anchors[1:]):                 # readings that disagree: look between two confirmed neighbours
        lo, hi = key(mains[a]['_slp']), key(mains[b]['_slp'])
        if b - a < 2 or b - a > 40: continue
        pool = lex.between(lo, hi) if lo <= hi else None
        if not pool: continue
        for e in mains[a + 1:b]:
            if e['lex'] != 'none' or e['_agree']: continue
            best = None
            for r in e['_rs']:
                if len(r) < 4: continue
                hit = lex.near(r, pool, 1 if len(r) < 7 else 2)
                if hit and (best is None or hit[0] < best[0]): best = hit
            if best:
                e['_slp'], e['lex'] = best[1], 'corrected'; how['main corrected between neighbours'] += 1
    for e in mains:
        if e['lex'] == 'none' and not e['_agree']:         # anywhere in the list, one letter away, only for longer words
            for r in e['_rs']:
                if len(r) >= 7:
                    hit = lex.near(r, lex.by_len[len(r)] + lex.by_len[len(r) - 1] + lex.by_len[len(r) + 1], 1)
                    if hit:
                        e['_slp'], e['lex'] = hit[1], 'corrected'; how['main corrected, one letter'] += 1; break
    # ---- sub-entries: parent + member
    for e in entries:
        if e['kind'] != 'sub': continue
        par = by_id.get(e.get('parent'))
        stem = (reading(par['stem']) if par and par.get('stem') else par['_slp'] if par else '') or ''
        mem, lv, agree = choose(e['_rs'], lex, stem)
        if lv == 'none' and not agree:
            if len(stem) >= 3:                             # a listed word that begins with the parent, near a reading
                pool = [w[len(stem):] for w in lex.by_prefix.get(stem[:3], ()) if w.startswith(stem) and len(w) > len(stem)]
                best = None
                for r in e['_rs']:
                    hit = lex.near(r, pool, 1) if len(r) >= 4 else None
                    if hit and (best is None or hit[0] < best[0]): best = hit
                if best: mem, lv = best[1], 'corrected'; how["sub corrected from the parent's compounds"] += 1
            if lv == 'none':
                for r in e['_rs']:
                    if len(r) >= 6:
                        hit = lex.near(r, lex.by_len[len(r)] + lex.by_len[len(r) - 1] + lex.by_len[len(r) + 1], 1)
                        if hit: mem, lv = hit[1], 'corrected'; how['sub member corrected, one letter'] += 1; break
        e['_slp'], e['lex'], e['_agree'], e['_stem'] = mem, lv, agree, stem
    # ---- write back
    changed = Counter()
    for e in entries:
        if e['lex'] != 'none' and e['_slp']:
            new = deva(e['_slp'])
            if norm(new) != norm(la(e['wit']['T'])): changed[e['kind']] += 1; e['hw_ocr'] = e['wit']['T']
            e['hw'] = new
        elif e['_agree'] and e['_slp']:
            e['hw'] = deva(e['_slp'])
        else:
            e['hw'] = la(e['wit']['T'])
        confirmed = e['lex'] in ('mw', 'compound', 'member')
        e['status'] = 'ok' if e['_agree'] and confirmed else 'probable' if e['lex'] != 'none' or e['_agree'] else 'check'
    for e in entries:
        if e['kind'] == 'sub' and e.get('parent'):
            par = by_id[e['parent']]
            e['full'] = deva(e['_stem'] + e['_slp']) if e['_stem'] and e['_slp'] else (par.get('stem') or par['hw']) + e['hw']
        else:
            e['full'] = e['hw']
        e['iast'] = sanscript.transliterate(e['full'], sanscript.DEVANAGARI, sanscript.IAST)
    for e in entries:
        for k in ('_slp', '_rs', '_agree', '_stem'): e.pop(k, None)
    json.dump(data, open(f'{WORK}/entries.json', 'w'), ensure_ascii=False)
    print('lexicon', len(lex.words), 'words')
    for kind in ('main', 'sub'):
        es = [e for e in entries if e['kind'] == kind]
        print(kind, len(es), 'lex:', dict(Counter(e['lex'] for e in es)), 'status:', dict(Counter(e['status'] for e in es)))
    print('reading changed by the word list:', dict(changed)); print(dict(how))


if __name__ == '__main__':
    main()
