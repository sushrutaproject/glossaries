"""Entries of the Sabdakosa from the page OCR -> $GLOSSARY_WORK/entries.json   (private: holds the text of every entry)

A line's indent in its column says what it is (the pages are deskewed, so the margin is vertical):
  at the margin        a headword:    अपान-पु., ...
  one step in (~70 px) a sub-entry:   -मर्मन्-न., ...   = parent headword + this member (अपाङ्ग + मर्मन्)
  further in           continuation of the entry above
Each headword is read three times: our page OCR (T), archive.org's OCR (IA), and a second pass over the single line with
another model and scale (T2).  Two that agree make the reading 'ok'; alphabetical order settles some of the rest.

  python parse.py            (needs ocr/, ia/v1_hocr.html and img/ in $GLOSSARY_WORK)
"""
import json, os, re, sys, unicodedata
from collections import Counter
from multiprocessing import Pool
from columns import WORK, TESS, FIRST, LAST, regions, prep

HOCR = f'{WORK}/ia/v1_hocr.html'
DASH = '-–—'
DASHLIKE = DASH + '~_=“”"'                     # what a leading dash is misread as
JUNK = re.compile(r"^[\s.`'’‘,_:;|।~\"“”*°·•<>=+^\\/!¦-]*$")
GENDERS = {'m': 'पुं.', 'f': 'स्त्री.', 'n': 'न.', 'adj': 'वि.', 'ind': 'अ.'}


def clean(s):
    s = unicodedata.normalize('NFC', s).replace('‌', '').replace('‍', '')
    return re.sub(r'\s+', ' ', s).strip()


def gender(tok):
    """m / f / n / adj / ind for a (possibly misread) tag such as पु. स्त्री. न. वि."""
    t = re.sub(r'[\s.,:;()]+', '', tok)
    if t in ('पु', 'पुं', 'एु', 'ए', 'पू', 'घु', 'यु', 'षु', 'पुः', '9ु', 'ु', 'प', 'पृ'): return 'm'
    if t in ('न', 'नः', 'नं'): return 'n'
    if t in ('वि', 'चि', 'बि', 'वी', 'विः'): return 'adj'
    if t in ('अ', 'अव्य'): return 'ind'
    if 2 <= len(t) <= 6 and t.endswith('ी') and ('्' in t or len(t) <= 3): return 'f'      # स्त्री read as स्नी, ल्ली, ख्री, छी ...
    return None


def la(s):
    """the scan's ल is the Marathi glyph, which the OCR reads as ळ (or as both: लळ)"""
    return re.sub(r'ळ', 'ल', re.sub(r'लळ|ळल', 'ल', s))


SEG = re.compile(r'\s*[%s]+\s*' % re.escape(DASH))
NOTE = re.compile(r'^\(\s*परि[वब]\s*[.०°]*\s*,?\s*\)\s*')


def tags(rest):
    """gender tags at the start of the text after the headword"""
    rest = NOTE.sub('', rest)
    gs = []
    for tok in re.split(r'[,\s]+', rest.lstrip('( '))[:4]:
        g = gender(tok)
        if not g: break
        if g not in gs: gs.append(g)
    return gs


def head(text, sub):
    """(headword, variant, genders, rest, in parentheses) from the text of a headword or sub-entry line, or None.
    अपान-पु., ...   -मर्मन्-न., ...   ( वीरा )-स्त्री., ...   (द्वीपि)-चर्मन्-न., ...   अपार्थ-(क)-वि., ...   -वह-स्रोतस्-न., ..."""
    t = text
    lead = re.match(r'^(\(?\s*)[%s]+\s*' % re.escape(DASHLIKE), t)
    if sub:
        t = (lead.group(1) + t[lead.end():]) if lead else t
    elif lead and re.match(r'^\(?\s*[%s]' % re.escape(DASH), t):
        return None
    segs = SEG.split(t, maxsplit=5)
    if len(segs) < 2: return None
    members, var, paren = [], '', False
    if len(segs[0].split()) <= 3:                        # the OCR splits a headword at a repha or a wide letter-space
        segs[0] = re.sub(r'(?<=[\u0900-\u097f])\s+(?=[\u0900-\u097f])', '', segs[0])
    for i, seg in enumerate(segs[:-1]):
        rest = ' - '.join(segs[i:])                      # what follows if the headword ends before this segment
        if i and (tags(seg) or re.match(r'^\S+\s*[०°]', seg) or NOTE.match(seg) and tags(NOTE.sub('', seg))):
            break
        m = re.match(r'^\(\s*([^\s()]{1,25})\s*\)?$', seg) or re.match(r'^([^\s()]{1,25})\s*\)$', seg)
        if m:                                            # a member in parentheses
            if i == 0 or not members: members.append(m.group(1)); paren = True
            elif len(m.group(1)) <= 4 and not var: var = '(' + m.group(1) + ')'
            else: members.append(m.group(1))
            continue
        if not re.match(r'^[\u0900-\u0963\u0970-\u097f]{1,30}$', seg) or i >= 4:
            if not members: return None
            break
        members.append(seg)
    else:
        rest = segs[-1]
    if not members: return None
    gs = tags(rest)
    if len(members) > 1 and not gs:                      # without a tag to end on, trust only the first member
        rest = ' - '.join(segs[1:]); members = members[:1]; gs = tags(rest)
    stem = la(members[0]) if paren and len(members) > 1 else None      # (द्वीपि)-चर्मन्: later sub-entries hang on द्वीपि
    return la(''.join(members)), var, gs, rest, paren, stem


def first_x(line):
    for w in line['w']:
        if not JUNK.match(w[0]) and w[3] - w[1] > 12:
            return w[1]
    return None


def strip_junk(line):
    ws = [w[0] for w in line['w']]
    while ws and JUNK.match(ws[0]): ws.pop(0)
    return clean(' '.join(ws))


def margin(xs, lo, hi, default):
    xs = sorted(x for x in xs if lo <= x <= hi)
    for i, a in enumerate(xs):
        if sum(1 for b in xs[i:i + 6] if b - a <= 25) >= 3:
            return a
    return default


# ---------- witnesses ----------

def ia_pages():
    """{pdf page: [[text, x0, y0, x1, y1], ...]} from archive.org's hOCR (cached)"""
    cache = f'{WORK}/ia/lines.json'
    if os.path.exists(cache):
        return {int(k): v for k, v in json.load(open(cache)).items()}
    from lxml import html
    raw = open(HOCR, 'rb').read()
    starts = [m.start() for m in re.finditer(rb'<div class=["\']ocr_page["\']', raw)] + [len(raw)]
    res = {}
    for p in range(1, len(starts)):
        frag = html.fromstring(raw[starts[p - 1]:starts[p]].decode('utf8'))
        lines = []
        for ln in frag.xpath('.//*[starts-with(@class,"ocr_line") or @class="ocr_header" or @class="ocr_caption" or @class="ocr_textfloat"]'):
            b = [int(v) for v in re.search(r'bbox (\d+) (\d+) (\d+) (\d+)', ln.get('title')).groups()]
            t = ' '.join(x for x in (''.join(w.itertext()).strip() for w in ln.xpath('.//*[@class="ocrx_word"]')) if x)
            if t: lines.append([t] + b)
        res[p] = lines
    json.dump(res, open(cache, 'w'), ensure_ascii=False)
    return res


def reread(job):
    """second pass over single lines of one page: [(key, text)]"""
    import tesserocr
    p, items = job                                       # items: (key, col, box in deskewed frame)
    regs, geo = regions(p)
    out = []
    with tesserocr.PyTessBaseAPI(path=TESS, lang='script/Devanagari', psm=tesserocr.PSM.SINGLE_LINE) as api:
        for key, col, b in items:
            im, ox, oy = regs[col]
            strip = im.crop((0, max(0, b[1] - oy - 10), im.width, min(im.height, b[3] - oy + 10)))
            api.SetImage(prep(strip, 0.5, 0, 1.0))
            out.append((key, clean(api.GetUTF8Text())))
    return out


# ---------- alphabetical order ----------

from indic_transliteration import sanscript
ORDER = {c: i for i, c in enumerate("aAiIuUfFxXeEoOMHkKgGNcCjJYwWqQRtTdDnpPbBmyrlLvSzsh")}

def sortkey(deva):
    s = sanscript.transliterate(deva, sanscript.DEVANAGARI, sanscript.SLP1)
    return [ORDER[c] for c in s if c in ORDER]


def norm(hw):
    """key for comparing witnesses: without spaces, parentheses, final virama; ल for ळ; anusvara for candrabindu"""
    k = la(re.sub(r'[\s()\u200c\u200d`]', '', unicodedata.normalize('NFC', hw))).replace('ँ', 'ं')
    return k[:-1] if k.endswith('्') else k


def main():
    os.environ['OMP_THREAD_LIMIT'] = '1'
    ia = ia_pages()
    lines = []                                           # every dictionary line in reading order
    skipped = []
    for p in range(FIRST, LAST + 1):
        d = json.load(open(f'{WORK}/ocr/{p:04d}.json'))
        if d['kind'] != 'columns':
            skipped.append(p); continue
        g = d['geo']; c = g['c']
        for col in 'LR':
            L = d['regions'][col]
            xs = [x for x in (first_x(l) for l in L) if x is not None]
            mg = margin(xs, c - 1215, c - 1100, c - 1143) if col == 'L' else margin(xs, c + 40, c + 95, c + 66)
            for i, l in enumerate(L):
                x = first_x(l)
                if x is None: continue
                dd = x - mg
                lines.append(dict(p=p, col=col, i=i, t=strip_junk(l), b=l['b'], o=l['o'], conf=l['conf'],
                                  cls='H' if dd < 35 else 'S' if dd < 100 else 'C', rule=c, theta=g['theta']))
    # entries
    entries = []; conflicts = Counter(); parent = None
    for n, l in enumerate(lines):
        t = l['t']; cls = l['cls']
        starts_dash = bool(re.match(r'^\(?\s*[%s]' % re.escape(DASH), t))
        h = None
        if cls == 'H':
            h = head(t, False)
            if h is None and starts_dash:                # a sub-entry sitting at the margin
                h = head(t, True); cls = 'S' if h else cls; conflicts['sub at margin'] += bool(h)
            elif h is None: conflicts['margin line without headword'] += 1
        elif cls == 'S':
            h = head(t, True) if (starts_dash or re.match(r'^\(?\s*[%s]' % re.escape(DASHLIKE), t)) else None
            if h is None:
                h2 = head(t, False)
                if h2 and h2[2]:                         # looks like a headword with a gender tag: indent misjudged
                    h, cls = h2, 'H'; conflicts['headword at sub indent'] += 1
                else: conflicts['sub indent without dash'] += 1
        if h is None:
            if entries: entries[-1]['lines'].append(n)
            continue
        hw, var, gs, rest, paren, stem = h
        e = dict(id=len(entries) + 1, kind='main' if cls == 'H' else 'sub', hw=hw, var=var, paren=paren, genders=gs,
                 p=l['p'], col=l['col'], line=n, lines=[n])
        if cls == 'H':
            if paren and not stem and parent:            # ( वीरा )-स्त्री.: another form of the headword above, which stays the parent
                e['form_of'] = parent
            else:
                parent = e['id']
                if stem: e['stem'] = stem
        else: e['parent'] = parent
        entries.append(e)
    # witnesses
    def find_ia(l):
        xr = l['rule']                                   # IA boxes are in the unrotated scan; l['o'] is our centre there
        ox, oy = l['o']
        cand = [k for k in ia.get(l['p'], []) if k[2] < oy < k[4] and ((k[1] + k[3]) / 2 < ox + 600) == (l['col'] == 'L' or True)]
        cand = [k for k in cand if abs((k[1] + k[3]) / 2 - ox) < 700]
        return clean(' '.join(k[0] for k in sorted(cand, key=lambda k: k[1])))
    cache = f'{WORK}/reread.json'
    if os.path.exists(cache):
        rr = json.load(open(cache))
    else:
        jobs = {}
        for e in entries:
            l = lines[e['line']]
            jobs.setdefault(l['p'], []).append((f"{l['p']}{l['col']}{l['i']}", l['col'], l['b']))
        rr = {}
        with Pool(14) as pool:
            for out in pool.imap_unordered(reread, jobs.items(), chunksize=4):
                rr.update(out)
        json.dump(rr, open(cache, 'w'), ensure_ascii=False)
    for e in entries:
        l = lines[e['line']]; sub = e['kind'] == 'sub'
        wit = {'T': e['hw']}
        for name, text in (('IA', find_ia(l)), ('T2', re.sub(r"^[\s.`'’‘,_:;|।]+", '', rr.get(f"{l['p']}{l['col']}{l['i']}", '')))):
            h = head(text, sub) or (head(text, not sub) if text else None)
            if h: wit[name] = h[0]
        e['wit'] = wit
    # main headwords in full, for the order check
    by_id = {e['id']: e for e in entries}
    def full(e, hw):
        if e['kind'] == 'sub' and e.get('parent'):
            par = by_id[e['parent']]
            return (par.get('stem') or par['hw']) + hw
        return hw
    for e in entries:
        w = e['wit']; votes = Counter(norm(v) for v in w.values())
        best, n = votes.most_common(1)[0]
        if n >= 2:
            e['status'] = 'ok' if norm(w['T']) == best else 'probable'
            agree = [v for v in w.values() if norm(v) == best]
            e['hw'] = la(max(agree, key=lambda v: v.endswith('्')))      # keep a final virama if any witness has it
        else:
            e['status'] = 'check'
    # alphabetical order: only to choose among witnesses that disagree
    mains = [e for e in entries if e['kind'] == 'main']
    keys = [sortkey(e['hw']) for e in mains]
    fixed = 0
    for i in range(1, len(mains) - 1):
        e = mains[i]
        lo, hi = keys[i - 1], keys[i + 1]
        if lo <= hi and not (lo <= keys[i] <= hi):
            e['order'] = False
            if e['status'] == 'check':
                alts = [v for v in e['wit'].values() if lo <= sortkey(la(v)) <= hi]
                if alts:                                 # another witness fits between the neighbours
                    e['hw'] = la(alts[0]); keys[i] = sortkey(e['hw']); e['status'] = 'probable'; fixed += 1; del e['order']
    for e in entries:
        e['full'] = full(e, e['hw'])
        e['iast'] = sanscript.transliterate(e['full'], sanscript.DEVANAGARI, sanscript.IAST)
    json.dump(dict(lines=lines, entries=entries, skipped_pages=skipped), open(f'{WORK}/entries.json', 'w'), ensure_ascii=False)
    st = Counter((e['kind'], e['status']) for e in entries)
    print('lines', len(lines), 'entries', len(entries), dict(Counter(e['kind'] for e in entries)))
    print('status', dict(st)); print('order fixed', fixed, 'out of order left', sum(1 for e in entries if e.get('order') is False))
    print('layout/pattern conflicts', dict(conflicts)); print('pages without columns (skipped):', skipped)
    print('no gender tag', sum(1 for e in entries if not e['genders']), 'witness counts', dict(Counter(len(e['wit']) for e in entries)))


if __name__ == '__main__':
    main()
