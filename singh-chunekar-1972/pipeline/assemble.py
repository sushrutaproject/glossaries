"""Add errata to data.json and write the offline HTML search page."""
import os, json, re, sqlite3
OUT = os.environ.get('GLOSSARY_OUT', 'out')
WORK = os.environ.get('GLOSSARY_WORK', 'work')
PDF_NAME = 'Singh_and_Chunekar_-_Glossary_of_Vegetable_Drugs_in_Brihattrayi_1972_ocr.pdf'

def parse_errata():
    rows, page = [], None
    for p in range(563, 569):
        try:
            lines = open(f'{WORK}/ocr/{p:03d}.txt').readlines()
        except FileNotFoundError:
            continue
        for line in lines:
            t = line.strip()
            if not t or re.match(r'^(ERRATA|Page\s+Line|\d{3}$)', t):
                continue
            m = re.match(r'^(\d{1,3})\s+(\d{1,2}|after\s+\w+|last|[Ff]oot\s*note)\s*[-—:]?\s+(.+)$', t)
            if m:
                page = m.group(1)
                rows.append([page, m.group(2), m.group(3)])
                continue
            m = re.match(r'^(\d{1,2}|after\s+\w+)\s+(Add|Delete|Correct|Read|Omit|Change|Replace|Put|Insert)(.*)$', t)
            if m and page:
                rows.append([page, m.group(1), m.group(2) + m.group(3)])
            elif rows:
                rows[-1][2] += ' ' + t
    return rows

PAGES_RE = re.compile(r'((?:[‘\']?\d{1,3}(?:\s*\(\s*\d\s*\))?[,.;:]?\s*)+)$')

def parse_index(first, last, kind):
    """index lines 'Name 12, 34 (2),' with wrapped names / page lists -> [kind, name, [pages]]"""
    items, pending = [], ''
    for p in range(first, last + 1):
        for line in open(f'{WORK}/ocr/{p:03d}.txt'):
            t = line.strip()
            if not t or re.fullmatch(r'\d{3}', t) or (t.isupper() and not re.search(r'\d', t)):
                continue
            m = PAGES_RE.search(t)
            if m and m.start() == 0:                  # continuation of a page list
                if items and not pending:
                    items[-1][2] += re.findall(r'\d{1,3}(?!\s*\))', m.group(1))
                continue
            if m:
                name = (pending + ' ' + t[:m.start()]).strip(' ,;')
                pages = [x for x in re.findall(r'\d{1,3}(?!\s*\))', m.group(1)) if 1 <= int(x) <= 474]
                if len(name) >= 3 and pages:
                    items.append([kind, re.sub(r'\s+', ' ', name), pages])
                pending = ''
            elif re.match(r'^[A-Z][a-z]+ [a-z]{3,}', t) and re.match(r'^[A-Z][a-z]+ [a-z]{3,}', pending):
                pending = t        # a new binomial: the previous one lost its page numbers
            else:
                pending = (pending + ' ' + t).strip() if len(pending) < 60 else t
    return items

def main():
    d = json.load(open(f'{OUT}/data.json'))
    d['errata'] = parse_errata()
    d['index'] = parse_index(499, 515, 'Latin/English') + parse_index(516, 558, 'Sanskrit/Indian')
    db0 = sqlite3.connect(f'{OUT}/brhattrayi_glossary.sqlite')
    db0.execute('DROP TABLE IF EXISTS book_index')
    db0.execute('CREATE TABLE book_index (kind TEXT, name TEXT, book_pages TEXT)')
    db0.executemany('INSERT INTO book_index VALUES (?,?,?)',
                    [(k, n, ', '.join(p)) for k, n, p in d['index']])
    db0.commit()
    db = sqlite3.connect(f'{OUT}/brhattrayi_glossary.sqlite')
    db.execute('DROP TABLE IF EXISTS errata')
    db.execute('CREATE TABLE errata (book_page TEXT, line TEXT, correction TEXT)')
    db.executemany('INSERT INTO errata VALUES (?,?,?)', d['errata'])
    db.commit()
    html = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template.html')).read()
    blob = json.dumps(d, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    html = (html.replace('__DATA__', blob).replace('__PDF__', PDF_NAME)
            .replace('__SUBTITLE__', 'searchable OCR edition (private research copy)'))
    open(f'{OUT}/Brhattrayi_Glossary_Search.html', 'w').write(html)
    print('errata', len(d['errata']), 'html bytes', len(html))

if __name__ == '__main__':
    main()
