"""OCR pages of the Sabdakosa -> $GLOSSARY_WORK/ocr/NNNN.json + NNNN.txt

  python ocr_page.py N [N ...]        (the whole book: seq 1 1021 | xargs -P 14 -n 4 python ocr_page.py; about 30 minutes)

Setting chosen in the trial of 25 Nov 2026: Devanagari script model (tessdata_best), image smoothed and reduced to 240 dpi.
Dictionary pages (a printed column rule is found): running head H, left column L, right column R, each read as one block,
deskewed.  Other pages: whole page P, automatic layout.
Boxes are in the deskewed frame; geo.theta and each line's "o" (its centre in the original scan) lead back to the scan.
"""
import json, math, os, sys
os.environ['OMP_THREAD_LIMIT'] = '1'
import numpy as np
from PIL import Image
import tesserocr
from columns import WORK, TESS, COLW, rule_line, regions, prep

LANG, SCALE, BLUR = 'script/Devanagari_best', 0.6, 1.5

def read(api, im, ox, oy, geo):
    api.SetImage(prep(im, SCALE, 0, BLUR)); api.Recognize()
    it = api.GetIterator(); L, W = tesserocr.RIL.TEXTLINE, tesserocr.RIL.WORD
    try:
        it.GetUTF8Text(L)
    except Exception:                     # blank region: nothing recognised
        return []
    th, cx, cy = geo.get('theta', 0.0), geo['w'] / 2, geo['h'] / 2
    lines = []
    if it is None: return lines
    while True:
        if it.IsAtBeginningOf(L):
            t = (it.GetUTF8Text(L) or '').strip()
            if t:
                b = [round(x / SCALE) for x in it.BoundingBox(L)]
                b = [b[0] + ox, b[1] + oy, b[2] + ox, b[3] + oy]
                xc, yc = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
                lines.append(dict(t=t, b=b, conf=round(it.Confidence(L)), w=[],
                                  o=[round(cx + (xc - cx) * math.cos(th) + (yc - cy) * math.sin(th)),
                                     round(cy - (xc - cx) * math.sin(th) + (yc - cy) * math.cos(th))]))
        wt = (it.GetUTF8Text(W) or '').strip()
        if wt and lines:
            wb = [round(x / SCALE) for x in it.BoundingBox(W)]
            lines[-1]['w'].append([wt, wb[0] + ox, wb[1] + oy, wb[2] + ox, wb[3] + oy, round(it.Confidence(W))])
        if not it.Next(W): break
    return lines

def page(p):
    out = f'{WORK}/ocr/{p:04d}.json'
    if os.path.exists(out): return
    src = f'{WORK}/img/pg-{p:04d}.png'
    full = Image.open(src).convert('L')
    try:
        regs, geo = regions(p)
        if geo['bot'] - geo['top'] < 0.35 * geo['h']: raise ValueError('rule too short')
        kind = 'columns'
    except Exception as e:
        regs, geo, kind = None, dict(w=full.width, h=full.height, why=str(e)[:80]), 'page'
    res = dict(page=p, kind=kind, geo=geo, regions={})
    if kind == 'columns':
        with tesserocr.PyTessBaseAPI(path=TESS, lang=LANG, psm=tesserocr.PSM.SINGLE_BLOCK) as api:
            # running head: the strip above the rule, from the deskewed page
            th = geo['theta']
            rot = full.rotate(math.degrees(th), resample=Image.BICUBIC, fillcolor=255) if th else full
            if th and abs(rule_line((np.asarray(rot) < 200).astype(np.int32))[0]) > abs(math.tan(th)) / 3:
                rot = full.rotate(-math.degrees(th), resample=Image.BICUBIC, fillcolor=255)
            x0, x1 = max(0, int(geo['c']) - COLW), min(full.width, int(geo['c']) + COLW)
            y0, y1 = max(0, geo['top'] - 330), max(40, geo['top'] - 28)
            res['regions']['H'] = read(api, rot.crop((x0, y0, x1, y1)), x0, y0, geo)
            for col in 'LR':
                im, ox, oy = regs[col]
                res['regions'][col] = read(api, im, ox, oy, geo)
    else:
        with tesserocr.PyTessBaseAPI(path=TESS, lang=LANG, psm=tesserocr.PSM.AUTO) as api:
            res['regions']['P'] = read(api, full, 0, 0, geo)
    os.makedirs(f'{WORK}/ocr', exist_ok=True)
    json.dump(res, open(out + '.tmp', 'w'), ensure_ascii=False)
    os.replace(out + '.tmp', out)
    open(f'{WORK}/ocr/{p:04d}.txt', 'w').write(
        '\n\n'.join(f'[{r}]\n' + '\n'.join(l['t'] for l in ls) for r, ls in res['regions'].items()) + '\n')

if __name__ == '__main__':
    for a in sys.argv[1:]:
        try: page(int(a))
        except Exception as e: print('FAILED', a, repr(e), flush=True)
