"""Private review page: a random sample of entries per headword status, each with the scan strip of its first line,
the headword as read, the three witnesses and the parsed citations -> $GLOSSARY_WORK/out/review.html

  python review.py [N per status, default 40] [seed]
"""
import base64, html, io, json, random, sys
from collections import defaultdict
from columns import WORK, regions

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    random.seed(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    d = json.load(open(f'{WORK}/out/full.json')); lines = json.load(open(f'{WORK}/entries.json'))
    L, raw = lines['lines'], {e['id']: e for e in lines['entries']}
    refs = defaultdict(list)
    for r in d['refs']: refs[r[0]].append(r[1:])
    pick = []
    for st in ('ok', 'probable', 'check'):
        pick += random.sample([e for e in d['entries'] if e['headword']['status'] == st], n)
    cache = {}
    rows = {st: [] for st in ('ok', 'probable', 'check')}
    for e in sorted(pick, key=lambda e: e['id']):
        l = L[raw[e['id']]['line']]
        if l['p'] not in cache: cache[l['p']] = regions(l['p'])[0]
        im, ox, oy = cache[l['p']][l['col']]
        strip = im.crop((0, max(0, l['b'][1] - oy - 8), im.width, l['b'][3] - oy + 8))
        strip = strip.resize((strip.width // 2, strip.height // 2)).convert('1')
        buf = io.BytesIO(); strip.save(buf, 'PNG', optimize=True)
        cs = '; '.join(' '.join(x for x in (r[4], r[0], r[1], r[2] + ('.' + r[3] if r[3] else '')) if x) for r in refs[e['id']])
        w = ' · '.join(f'{k}: {html.escape(v)}' for k, v in e['witnesses'].items())
        rows[e['headword']['status']].append(
            f'<tr><td><img src="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"></td>'
            f'<td><div class="hw">{html.escape(e["headword"]["deva"])} <span>{html.escape(e["headword"]["iast"])}</span> '
            f'<em>{" ".join(e["gender"])}</em> <small>{e["kind"]}, p. {e["book_page"]} {e["column"]}</small></div>'
            f'<div class="w">{w}</div><div class="c">{html.escape(cs) or "—"}</div>'
            f'<div class="r">{html.escape(" | ".join(e["raw_citations"]))}</div></td></tr>')
    body = ''.join(f'<h2>Status “{st}” ({n} at random)</h2><table>{"".join(rows[st])}</table>' for st in rows)
    open(f'{WORK}/out/review.html', 'w').write(PAGE.replace('%BODY%', body))

PAGE = """<!doctype html><meta charset="utf-8"><title>Śabdakośa entries: review sample</title>
<style>body{font:15px/1.5 system-ui,sans-serif;max-width:1150px;margin:1.5em auto;padding:0 16px;color:#1c2333}
h2{border-bottom:2px solid #e8a33d;margin-top:2em} td{vertical-align:top;padding:8px 10px 8px 0;border-top:1px solid #eee}
img{max-width:520px;height:auto;display:block}
.hw{font:20px/1.4 "Noto Serif Devanagari",serif} .hw span{font:italic 16px Georgia,serif;margin-left:.5em}
.hw em{font-style:normal;color:#1f3a5f;font-size:15px;margin-left:.5em} .hw small{font:12px system-ui;color:#889;margin-left:.6em}
.w{font:14px "Noto Serif Devanagari",serif;color:#777} .c{font-size:14px;color:#1f3a5f} .r{font:13px "Noto Serif Devanagari",serif;color:#999}
</style><h1>Āyurvedīya Śabdakośa: sample of parsed entries</h1>
<p>Private file. The strip is the first line of the entry in the scan. Below the headword: the three readings
(T = our OCR, IA = archive.org, T2 = second pass), the citations as parsed (blue), and the same as read (grey).
Sub-entries show the full form: parent headword + member.</p>%BODY%"""
if __name__ == '__main__': main()
