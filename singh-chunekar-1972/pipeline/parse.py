"""Parse glossary pages (PDF 25-498) into entries.

Stage 1: detect headword lines from the Latin+Devanagari OCR TSV.
Stage 2: re-read the Devanagari part of each headword line with Sanskrit /
Hindi / Devanagari-script models (tesserocr); choose the reading whose
transliteration best agrees with the romanised capitals; merge the two
readings into one IAST headword.  Output: entries.json
"""
import sys, os, re, json, unicodedata, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lines import read_lines, is_deva, fix_diacritics, fold
from PIL import Image
from rapidfuzz.distance import Levenshtein
from indic_transliteration import sanscript

WORK = os.environ.get('GLOSSARY_WORK', 'work')
FIRST, LAST = int(os.environ.get('FIRST', 25)), int(os.environ.get('LAST', 498))
OFFSET = 24                                    # book page = pdf page - 24

CAPS = "A-ZĀĪŪṚṜḶṄÑṬḌṆŚṢḤṂŞŢŅḐŖṀȚŠȘÄÜÂÛ"
# capitalised token; may carry bracketed/hyphenated variants: KAKODU(DU)MBARIKĀ, SAVARA,-KA,-LODHRA
CAPS_TOK = re.compile(rf"^[\(\[]?([{CAPS}][{CAPS}'’\-—\(\)\[\]{{}},]*?)[\]\)]?[,.;:]*$")
NUM_TOK = re.compile(r"^\(?\d+\)?[,.]?$")
REF_START = re.compile(r"^(C\.|S\.|A\.)\s*(S|H|8|9|5)")

def norm_tok(t):
    t = t.replace(']', 'I').replace('|', 'I').replace('İ', 'I').replace('Í', 'I').replace('Ì', 'I')
    # a final long ī often comes out lower-case: GANGEYi, NANDi, KAKANDAKIĪ
    t = re.sub(r'(?<=[A-ZĀĪŪṢṬḌṆŚṚ])[iíīìı](?=[,.;:]?$)', 'Ī', t)
    # one stray lower-case letter inside a long capitalised word: UDICcYA
    if len(re.findall(r'[a-z]', t)) == 1 and len(re.findall(r'[A-Z]', t)) >= 4:
        t = t.upper()
    return t

def caps_run(ws):
    i, letters, longest = len(ws), 0, 0
    while i > 0:
        t = norm_tok(ws[i - 1]['text'])
        m = CAPS_TOK.match(t)
        if m:
            n = len(re.findall(rf"[{CAPS}]", m.group(1)))
            letters += n; longest = max(longest, n); i -= 1; continue
        if NUM_TOK.match(t) and i == len(ws):
            i -= 1; continue
        break
    if i == len(ws) or letters < 3 or longest < 3:
        return None
    # every capitalised word must contain a vowel (YTR is garbled Devanagari)
    for w in ws[i:]:
        m = CAPS_TOK.match(norm_tok(w['text']))
        if m and len(m.group(1)) >= 3 and not re.search(r'[AEIOUĀĪŪṚ]', fix_diacritics(m.group(1))):
            return None
    # a comma before the capitals means a list of synonyms, not a headword
    if i > 0 and ws[i - 1]['text'].endswith(',') and is_deva(ws[i - 1]['text']):
        return None
    return i

def is_heading(line):
    if line['left'] > 205 or REF_START.match(line['text']):
        return None
    i = caps_run(line['words'])
    if i is None or i > 4:
        return None
    return i

JUNK_TOK = re.compile(r"^([`'\"\-:.,;|°~_•=]+|[a-z]|[\u0900-\u097F]{1,2})$")

def stage1():
    entries, cur = [], None
    for p in range(FIRST, LAST + 1):
        ls = [l for l in read_lines(f'{WORK}/ocr/{p:03d}.tsv') if l['top'] >= 120]
        if not ls:
            continue
        margin = min(l['left'] for l in ls)
        for l in ls:
            # drop trailing OCR specks (` - : . o |)
            while len(l['words']) > 1 and JUNK_TOK.match(l['words'][-1]['text']):
                l = dict(l, words=l['words'][:-1])
                l['text'] = ' '.join(w['text'] for w in l['words'])
            hi = is_heading(l)
            if hi == 0 and len(l['words']) == 1:
                # a lone capitalised token: only a heading if it is a real word at the margin
                m = CAPS_TOK.match(norm_tok(l['words'][0]['text']))
                if len(m.group(1)) < 4 or l['left'] > margin + 20:
                    hi = None
            split_body = None
            if hi is None:
                # heading merged onto the end of the previous text line:
                # "... See synonym-X. अनन्ता ANANTA"
                ws = l['words']
                i = caps_run(ws)
                if i is not None and 2 <= i < len(ws):
                    j = i
                    while j > 0 and is_deva(ws[j - 1]['text']) and i - j < 3:
                        j -= 1
                    if j < i and j >= 1 and re.search(r'[.\)]$', ws[j - 1]['text']):
                        split_body = ' '.join(w['text'] for w in ws[:j])
                        hw = ws[j:]
                        l = dict(l, words=hw, left=hw[0]['left'],
                                 top=min(w['top'] for w in hw),
                                 bottom=max(w['top'] + w['h'] for w in hw))
                        hi = i - j
            if split_body is not None and cur is not None:
                cur['body'].append(dict(pdf_page=p, left=ls[0]['left'], top=l['top'], text=split_body))
            if hi is not None:
                ws = l['words']
                head = dict(pdf_page=p, top=l['top'], bottom=l['bottom'],
                            margin=min(margin, l['left']) if split_body is None else l['left'] - 4,
                            tokens=[(w['text'], w['left']) for w in ws], hi=hi)
                if cur is not None and not cur['body']:
                    cur['heads'].append(head)       # several headwords, one entry
                else:
                    cur = dict(heads=[head], body=[], pdf_page=p)
                    entries.append(cur)
            elif cur is not None:
                cur['body'].append(dict(pdf_page=p, left=l['left'], top=l['top'], text=l['text']))
    return entries

# ---------- stage 2 ----------
def translit(deva):
    deva = re.sub(r'[^ऀ-ॿ ]', '', deva).replace('ळ', 'ल').strip()
    if not deva:
        return ''
    return unicodedata.normalize('NFC', sanscript.transliterate(deva, sanscript.DEVANAGARI, sanscript.IAST))

def key(s):
    s = re.sub(r'\(\d+\)', '', s)
    return re.sub(r"[^a-z]", '', fold(fix_diacritics(s)))

VOW = 'aeiou'
def pre_correct(roman):
    """known Latin-OCR slips in the spaced capitals"""
    r = ' '.join(norm_tok(w) for w in roman.split())
    r = fix_diacritics(r).replace(']', 'Ī').replace(' |', '').replace('|', 'I')
    r = re.sub(r'([AEIOUĀĪŪ])I([AĀ])', r'\1J\2', r)                 # AVALGUIA -> AVALGUJA
    r = re.sub(r'(?<=[BCDGHKMNPRSTVYŚṢṬḌṆ])[TL1]\b', 'Ī', r)          # ADHAKT -> ADHAKĪ
    r = re.sub(r'([A-ZĀĪŪṢṬḌṆŚ]) ([A-ZĀĪŪṢṬḌṆŚ]{1,2})$', r'\1\2', r)   # ABHISUK A -> ABHISUKA
    C = 'BCDGHJKLMNPSTVYŚṢṬḌṆ'
    r = re.sub(rf'(?<=[{C}])R(?=[{C}])', 'Ṛ', r)                      # AMRTA -> AMṚTA
    r = re.sub(rf'\bR(?=[{C}])', 'Ṛ', r)
    return r

# deva-letter vs roman-letter mismatches where the roman reading is the usual culprit
ROMAN_SLIPS = {('s', 'a'), ('j', 'i'), ('i', 't'), ('i', 'l'), ('u', 'v'), ('v', 'u'),
               ('s', 'o'), ('r', 'k'), ('h', 'b'), ('i', 'j')}

def merge(deva_iast, roman):
    """letter-level merge: diacritics/agreements from the Devanagari reading,
    disagreements from the roman capitals unless they are a typical roman slip."""
    d = deva_iast.replace(' ', '')
    dk = key(d)
    # map each base letter of d to its IAST char (fold is 1:1 per NFC char)
    dchars = [c for c in d if key(c)]
    rr = re.sub(r'\(\d+\)', '', roman)
    rchars = [c.lower() for c in fix_diacritics(rr) if key(c)]
    rk = ''.join(key(c) for c in rchars)
    if len(dchars) != len(dk) or len(rchars) != len(rk):
        return None
    out, disagreements = [], 0
    for op, a0, a1, b0, b1 in difflib.SequenceMatcher(None, dk, rk, autojunk=False).get_opcodes():
        if op == 'equal':
            out += [dchars[i] if key(dchars[i]) == key(rchars[b0 + i - a0]) else rchars[b0 + i - a0]
                    for i in range(a0, a1)]
            # prefer whichever side carries a diacritic
            for j, i in enumerate(range(a0, a1)):
                if dchars[i] == key(dchars[i]) and rchars[b0 + j] != key(rchars[b0 + j]):
                    out[len(out) - (a1 - a0) + j] = rchars[b0 + j]
        else:
            disagreements += max(a1 - a0, b1 - b0)
            if op == 'replace' and a1 - a0 == b1 - b0 and all(
                    (dk[a0 + j], rk[b0 + j]) in ROMAN_SLIPS for j in range(a1 - a0)):
                out += dchars[a0:a1]
            elif op == 'delete':
                out += dchars[a0:a1] if (a1 - a0 == 1 and dk[a0] in 'ś') else []
            else:
                out += rchars[b0:b1]
    return ''.join(out), disagreements

def word_split(merged, roman):
    """re-insert spaces where the roman headword has them"""
    words = [key(w) for w in re.sub(r'\(\d+\)', '', roman).split() if key(w)]
    if len(words) < 2:
        return merged
    # only split at word boundaries that look like real words (>=3 letters)
    out, pos = [], 0
    lens = [len(w) for w in words]
    if sum(lens) != len(key(merged)) or min(lens) < 3:
        return merged
    chars = [c for c in merged if key(c)]
    for L in lens:
        out.append(''.join(chars[pos:pos + L])); pos += L
    return ' '.join(out)

APIS = None
def ocr_crop(img, box):
    global APIS
    import tesserocr
    if APIS is None:
        APIS = {m: tesserocr.PyTessBaseAPI(path=os.environ.get('TESSDATA_PREFIX', 'tessdata').rstrip('/') + '/', lang=m,
                                          psm=tesserocr.PSM.SINGLE_LINE)
                for m in ('san_best', 'hin', 'script/Devanagari')}
    crop = img.crop(box)
    res = []
    for m, api in APIS.items():
        api.SetImage(crop)
        t = re.sub(r'[^ऀ-ॣ॰-ॿ ]', '', api.GetUTF8Text())
        t = t.replace('ळ', 'ल').strip()          # ḷa -> la (model artefact)
        if re.search(r'[अ-ह]', t):
            res.append((m, t))
    return res

def read_head(h, img):
    toks, hi = h['tokens'], h['hi']
    x0 = max(0, h['margin'] - 18)
    pads = [(5, 9), (12, 14)]
    best = None
    # k = how many of the leading capital tokens are really garbled Devanagari
    nrun = len(toks) - hi
    for k in range(0, min(4, nrun)):
        roman_toks = [t for t, _ in toks[hi + k:]]
        roman = ' '.join(roman_toks)
        if len(key(roman)) < 2:
            break
        x1 = toks[hi + k][1] - 4
        cands = []
        pre_deva = ' '.join(t for t, _ in toks[:hi] if is_deva(t))
        if k == 0 and pre_deva:
            cands.append(('latin+deva', pre_deva))
        rk = key(pre_correct(roman))
        if x1 - x0 > 30:
            for pt, pb in pads:
                c = ocr_crop(img, (x0, max(0, h['top'] - pt), x1, h['bottom'] + pb))
                cands += c
                if any(Levenshtein.normalized_distance(key(translit(t)), rk) <= 0.1 for _, t in c):
                    break
        for m, t in cands:
            ti = translit(t)
            d = Levenshtein.normalized_distance(key(ti), rk)
            score = d + 0.02 * k + (0 if m == 'san_best' else 0.001)
            if best is None or score < best[0]:
                best = (score, d, m, t, ti, roman)
        if best and best[1] <= 0.1:
            break
    return best

def stage2(entries):
    img_page, img = None, None
    for n, e in enumerate(entries):
        for h in e['heads']:
            p = h['pdf_page']
            if p != img_page:
                img_page, img = p, Image.open(f'{WORK}/img/pg-{p:03d}.png')
            best = read_head(h, img)
            if best is None:
                roman = ' '.join(t for t, _ in h['tokens'][h['hi']:])
                h.update(deva='', deva_src='', dist=1.0, roman_ocr=roman)
            else:
                _, d, m, t, ti, roman = best
                h.update(deva=t, deva_src=m, dist=round(d, 3), roman_ocr=roman)
            num = ' '.join(re.findall(r'\(\d+\)', h['roman_ocr']))
            roman_c = pre_correct(re.sub(r'[,;.]+$', '', h['roman_ocr'].strip()))
            h['roman'] = roman_c
            iast, status = None, 'check'
            if h['deva'] and h['dist'] <= 0.2:
                mg = merge(translit(h['deva']), roman_c)
                if mg:
                    iast = word_split(mg[0], roman_c) if ' ' in translit(h['deva']) else mg[0]
                    status = 'ok' if mg[1] == 0 else ('probable' if mg[1] <= 1 else 'check')
            if re.search(r'[A-Z]\s*[\(\[,—]|-[A-Z]', roman_c):
                # bracketed / hyphenated variant forms: keep the book's own layout
                iast = re.sub(r'\(\d+\)', '', roman_c).lower().strip(' ,')
                iast = re.sub(r'\(\s+', '(', re.sub(r'\s+\)', ')', iast))
            if iast is None:
                iast = re.sub(r'\(\d+\)', '', roman_c).lower().strip(' ,')
            h['iast'] = unicodedata.normalize('NFC', (iast + (' ' + num if num else '')).strip())
            h['status'] = status
            del h['tokens']
        if n % 250 == 0:
            print(n, len(entries), flush=True)
    return entries

if __name__ == '__main__':
    entries = stage1()
    print('entries', len(entries))
    entries = stage2(entries)
    json.dump(entries, open(os.environ.get('OUT', f'{WORK}/entries.json'), 'w'),
              ensure_ascii=False, indent=0)
