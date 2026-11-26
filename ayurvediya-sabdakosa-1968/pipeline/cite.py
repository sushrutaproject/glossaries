"""Citations of the Sabdakosa: ( सुशा. ६.२७ ), ( चक्र. चचि. २८.४ ), ( चचि. ९.४३; धनि. १.१३४ )  ->  (text, sthana, chapter, verse, commentator)

The abbreviations are the book's own (list in the front matter, PDF 20-22): a text (च सु अहृ असं का) run together with a
sthana (सू नि वि शा इ चि क सि उ खि), or a work without sthanas (रा ध र मा ...), optionally after a commentator
(ड = Dalhana, चक्र = Cakrapani, अरु = Arunadatta, हे = Hemadri, इन्दु = Indu).
Text codes follow the Singh & Chunekar concordance (C.S., S.S., A.H.) so that the two can be queried together.
"""
import re, unicodedata
from collections import Counter

DN = {c: str(i) for i, c in enumerate('०१२३४५६७८९')}

TEXTS = {'च': 'C.S.', 'सु': 'S.S.', 'अहृ': 'A.H.', 'असं': 'A.S.', 'का': 'K.S.'}
STHANAS = {'सू': 'Sū', 'नि': 'Ni', 'वि': 'Vi', 'शा': 'Śā', 'इ': 'In', 'इं': 'In', 'चि': 'Ci', 'क': 'Ka', 'सि': 'Si',
           'उ': 'U', 'खि': 'Khi', 'खिल': 'Khi'}
VALID = {'C.S.': 'Sū Ni Vi Śā In Ci Ka Si', 'S.S.': 'Sū Ni Śā Ci Ka U', 'A.H.': 'Sū Śā Ni Ci Ka U',
         'A.S.': 'Sū Śā Ni Ci Ka U', 'K.S.': 'Sū Vi Śā In Ci Si Ka Khi'}
WORKS = {                      # works cited without a sthana
    'रा': 'Rā.N.', 'रानि': 'Rā.N.', 'रापरि': 'Rā.N.pari.', 'ध': 'Dh.N.', 'धनि': 'Dh.N.', 'धपरि': 'Dh.N.pari.',
    'र': 'R.R.S.', 'रस': 'R.R.S.', 'ररस': 'R.R.S.', 'हर': 'R.R.S.(H)', 'मा': 'M.N.', 'मानि': 'M.N.',
    'भाप्र': 'Bh.P.', 'शा': 'Śā.S.', 'शाम': 'Śā.S.madhya', 'योर': 'Y.R.', 'हा': 'Hā.S.', 'चक्र': 'Cakradatta',
    'अहृको': 'A.H.kośa', 'शानि': 'Śāl.N.', 'मपा': 'Mad.N.', 'वैशसि': 'Vai.Ś.S.',
}
COMM = {'ड': 'Ḍalhaṇa', 'चक्र': 'Cakrapāṇi', 'अरु': 'Aruṇadatta', 'हे': 'Hemādri', 'इन्दु': 'Indu'}

CANON = {}
for t, T in TEXTS.items():
    for s, S in STHANAS.items():
        if S in VALID[T].split():
            CANON[t + s] = (T, S)
for w, W in WORKS.items():
    CANON.setdefault(w, (W, ''))

# the usual misreadings, tried in turn until a known abbreviation results
REPAIRS = [
    (r'^[छपखठणघशउषस]ु', 'सु'), (r'^स॒', 'सु'), (r'^ुु?', 'सु'), (r'^अह(?!ृ)्?ृ?', 'अहृ'), (r'^अह्ृ', 'अहृ'), (r'^[भअ]सं', 'असं'),
    (r'(?<=.)(स्|सु|सृ|स|सूं)$', 'सू'), (r'ड$', 'उ'), (r'ऽ$', 'उ'), (r'(दशा|दा|द्या|या|श्या|शया|रा|ञा)$', 'शा'),
    (r'^घ', 'ध'), (r'^थ$', 'ध'), (r'^र्$', 'र'), (r'चि$', 'चि'), (r'(?<=.)(वि|बि)$', 'वि'), (r'ई$', 'इ'), (r'इं$', 'इ'),
]


def squash(s):
    s = unicodedata.normalize('NFC', s).replace('‌', '').replace('‍', '')
    return re.sub(r"[\s.,:;`'’‘|।<>°॰०\-–—]+", '', s)


def resolve(raw):
    """(text, sthana, commentator) for an abbreviation as read, or None"""
    a = squash(raw)
    if not a: return None
    for c, C in COMM.items():                            # commentator + text
        if a.startswith(c) and len(a) > len(c):
            r = _resolve(a[len(c):])
            if r and r[1]: return r[0], r[1], C
    r = _resolve(a)
    return (r[0], r[1], '') if r else None


PAGE = {'पृ', 'पू', 'षू', 'शृ', 'षृ', 'शू', 'णू', 'णृ', 'पृष्ठ', 'पु', 'षु', 'शु', 'णु', 'प', 'ष', 'श', 'श्', 'ए'}          # पृ. = page (the Samgraha is cited by page too)


def _resolve(a):
    if a in CANON: return CANON[a]
    a = re.sub(r'^छ(?=स्|नि|शा|ड|सु|सू|उ|चि|क)', 'सु', a)
    if a in CANON: return CANON[a]
    if a.startswith('कारेवती'): return ('K.S.', 'Revatīkalpa')
    if a.startswith('काधूम'): return ('K.S.', 'Dhūmakalpa')
    if a.startswith('मा') and 3 < len(a) < 14 and not re.search(r'[०-९]', a):      # Madhavanidana by chapter name: मा ज्वर. ३.१९
        from indic_transliteration import sanscript
        return ('M.N.', sanscript.transliterate(a[2:], sanscript.DEVANAGARI, sanscript.IAST))
    if a.endswith('्'):
        if a[:-1] in CANON and a[:-1] in WORKS: return CANON[a[:-1]]
    forms = {a}
    for _ in range(3):
        new = set()
        for f in forms:
            for pat, rep in REPAIRS:
                g = re.sub(pat, rep, f)
                if g != f: new.add(g)
        new -= forms
        if not new: break
        hit = [g for g in new if g in CANON]
        if hit: return CANON[sorted(hit, key=len, reverse=True)[0]]
        forms |= new
    return None


PAREN = re.compile(r'\(([^()]{2,120})\)')
NUM = r'[०-९]+'
REF = re.compile(r'(?P<abbr>[^०-९;()\[\]]*?)\s*(?P<nums>%s(?:\s*[.,\-–\[\] ]\s*%s|\s*\])*)' % (NUM, NUM))


def numbers(s, text):
    """(chapter, verse) from the numeric part"""
    s = ''.join(DN.get(c, c) for c in s)
    m = re.match(r'\s*(\d+)\s*\[\s*(\d+)\s*\]\s*(.*)', s)      # Caraka Ci. 1 [4] 3: chapter 1, pada 4
    if m:
        ch, rest = f'{m.group(1)}-{m.group(2)}', m.group(3)
    else:
        m = re.match(r'\s*(\d+)(.*)', s)
        ch, rest = m.group(1), m.group(2)
    rest = re.sub(r'\s*[\-–]\s*', '-', rest.strip(' .,'))
    verses = [v for v in re.split(r'[.,\s]+', rest) if v]
    return ch, ','.join(verses)


def citations(text, stats=None):
    """all citations in the running text of an entry: [(text, sthana, chapter, verse, commentator, raw)]"""
    out = []
    for m in PAREN.finditer(text):
        inner = m.group(1)
        if not re.search(NUM, inner): continue
        prev = None
        for part in re.split(r';', inner):
            for r in REF.finditer(part):
                ab = r.group('abbr').strip()
                if squash(ab) in PAGE and out and prev:           # a page number for the citation just read
                    o = out[-1]
                    pg = 'p. ' + ''.join(DN.get(c, c) for c in re.sub(r'[^०-९\-–]', '', r.group('nums')))
                    out[-1] = o[:3] + ((o[3] + ' ' + pg).strip(),) + o[4:5] + (clean_raw(o[5] + ' ' + ab + ' ' + r.group('nums')),)
                    continue
                if squash(ab) == 'परिव': continue                 # परिव० = a changed reading, not a citation
                res = resolve(ab) if squash(ab) else prev
                if res is None:
                    if stats is not None: stats['unresolved'][squash(ab)] += 1
                    prev = None
                    continue
                ch, vs = numbers(r.group('nums'), res[0])
                out.append((res[0], res[1], ch, vs, res[2], clean_raw(ab + ' ' + r.group('nums'))))
                if stats is not None: stats['resolved'][res[0] + ' ' + res[1]] += 1
                prev = res
    return out


def clean_raw(s):
    return re.sub(r'\s+', ' ', s.replace('‌', '').replace('‍', '')).strip()


if __name__ == '__main__':                               # coverage over the page OCR
    import glob, json, os, sys
    from columns import WORK
    st = dict(resolved=Counter(), unresolved=Counter())
    for f in sorted(glob.glob(f'{WORK}/ocr/*.json')):
        d = json.load(open(f))
        if d['kind'] != 'columns' or not 23 <= d['page'] <= 994: continue
        for k in 'LR':
            citations(' '.join(l['t'] for l in d['regions'][k]), st)
    r, u = sum(st['resolved'].values()), sum(st['unresolved'].values())
    print(f'resolved {r}  unresolved {u}  ({100 * r / (r + u):.1f}%)')
    print(st['resolved'].most_common(60)); print(st['unresolved'].most_common(80))
