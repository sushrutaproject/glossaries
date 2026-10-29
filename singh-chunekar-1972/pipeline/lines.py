"""Shared helpers: read a tesseract TSV into ordered lines with word boxes."""
import csv, re, unicodedata

csv.field_size_limit(10**8)

def read_lines(tsv_path):
    words = []
    with open(tsv_path, encoding='utf-8') as f:
        r = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
        next(r, None)
        for row in r:
            if len(row) < 12 or row[0] != '5':
                continue
            t = row[11].strip()
            if not t:
                continue
            words.append(dict(key=(int(row[2]), int(row[3]), int(row[4])),
                              left=int(row[6]), top=int(row[7]),
                              w=int(row[8]), h=int(row[9]),
                              conf=float(row[10]), text=t))
    lines, order = {}, []
    for wd in words:
        if wd['key'] not in lines:
            lines[wd['key']] = []
            order.append(wd['key'])
        lines[wd['key']].append(wd)
    out = []
    for k in order:
        ws = lines[k]
        out.append(dict(words=ws,
                        left=min(w['left'] for w in ws),
                        top=min(w['top'] for w in ws),
                        bottom=max(w['top'] + w['h'] for w in ws),
                        right=max(w['left'] + w['w'] for w in ws),
                        text=' '.join(w['text'] for w in ws)))
    out.sort(key=lambda l: (l['top'], l['left']))
    return out

DEVA = re.compile(r'[ऀ-ॿ]')

def is_deva(s):
    return bool(DEVA.search(s))

# fix tesseract's cedilla/other look-alike diacritics to IAST dot-below forms
FIX = str.maketrans({'Ş': 'Ṣ', 'ş': 'ṣ', 'Ţ': 'Ṭ', 'ţ': 'ṭ', 'Ņ': 'Ṇ', 'ņ': 'ṇ',
                     'Ḑ': 'Ḍ', 'ḑ': 'ḍ', 'Ŗ': 'Ṛ', 'ŗ': 'ṛ', 'Ḥ': 'Ḥ',
                     'Ṁ': 'Ṃ', 'ṁ': 'ṃ', 'Ż': 'Ṅ', 'Ğ': 'G', 'ğ': 'g',
                     'Ț': 'Ṭ', 'ț': 'ṭ', 'Ș': 'Ṣ', 'ș': 'ṣ', 'Š': 'Ś', 'š': 'ś',
                     'Ä': 'Ā', 'ä': 'ā', 'Ü': 'Ū', 'ü': 'ū', 'Â': 'Ā', 'â': 'ā', 'Û': 'Ū', 'û': 'ū',
                     '{': '(', '}': ')'})

def fix_diacritics(s):
    return unicodedata.normalize('NFC', s).translate(FIX)

def fold(s):
    """Diacritic-insensitive lowercase ASCII-ish key."""
    s = unicodedata.normalize('NFD', s.lower())
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return s.replace('ı', 'i')
