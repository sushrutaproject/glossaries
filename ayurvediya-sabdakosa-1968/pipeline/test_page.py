"""Smoke test for a search page (public or private), with the Internet Archive
IIIF server replaced by crops of the local page images, so it works offline.

    python3 test_page.py PAGE.html QUERY [screenshot.png]

Needs: playwright (python) with chromium, and $GLOSSARY_WORK/img/pg-NNN.png.
Prints JavaScript errors (network errors for web fonts are harmless).
"""
import io, os, re, sys
from urllib.parse import unquote
from PIL import Image
from playwright.sync_api import sync_playwright

WORK = os.environ.get('GLOSSARY_WORK', 'work')
page_path, query = os.path.abspath(sys.argv[1]), sys.argv[2]
shot = sys.argv[3] if len(sys.argv) > 3 else 'test_page.png'

def iiif(route):
    u = unquote(route.request.url)
    m = re.search(r'_(\d{4})\.jp2/pct:([\d.]+),([\d.]+),([\d.]+),([\d.]+)/', u)
    if not m:
        return route.abort()
    p = int(m.group(1)) + 1
    im = Image.open(f'{WORK}/img/pg-{p:04d}.png'); W, H = im.size
    x, y, w, h = map(float, m.group(2, 3, 4, 5))
    c = im.crop((int(x / 100 * W), int(y / 100 * H), int((x + w) / 100 * W), int((y + h) / 100 * H)))
    b = io.BytesIO(); c.convert('RGB').save(b, 'JPEG')
    route.fulfill(body=b.getvalue(), content_type='image/jpeg')

with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page(viewport={'width': 1300, 'height': 1000})
    errors = []
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.route('https://iiif.archive.org/**', iiif)
    pg.goto('file://' + page_path); pg.wait_for_timeout(600)
    pg.fill('#q', query); pg.wait_for_timeout(300)
    n = pg.locator('.item[data-id]').count()
    if n:
        pg.click('.item[data-id]'); pg.wait_for_timeout(1200)
    pg.screenshot(path=shot)
    br.close()
print(f'{n} result(s) for {query!r}; screenshot {shot}; JS errors: {errors or "none"}')
sys.exit(1 if errors or not n else 0)
