"""Page geometry for the Ayurvediya Sabdakosa scan: find the printed column rule, deskew, cut the two columns.

Environment: GLOSSARY_WORK (default ./work-sabdakosa) holds img/pg-NNNN.png, the page images exactly as in the PDF
(pdfimages -png; 3296 x 4672 px, 400 dpi, bitonal); TESSDATA_PREFIX (default ./tessdata).
"""
import os
import numpy as np
from PIL import Image, ImageFilter

WORK = os.path.abspath(os.environ.get('GLOSSARY_WORK', 'work-sabdakosa'))
TESS = os.path.abspath(os.environ.get('TESSDATA_PREFIX', 'tessdata')) + '/'
COLW = 1250                      # px at 400 dpi: a column is about 1160 wide
FIRST, LAST = 23, 994            # PDF pages of the dictionary proper; printed page = PDF page - 22


def rule_line(a):
    """printed column rule as x = k*y + c, and its top and bottom y.  a: ink array (1 = ink)"""
    h, w = a.shape
    lo, hi, B = int(w * 0.30), int(w * 0.70), 60
    ys, xs = [], []
    for y0 in range(0, h - B, B // 2):
        blk = a[y0:y0 + B, lo:hi]
        prof = blk.sum(axis=0)
        prof = prof + np.roll(prof, 1) + np.roll(prof, -1)       # the rule drifts a pixel or two in a band
        x = int(np.argmax(prof))
        # a rule: nearly every row inked, and thin (not the black scanner border)
        if prof[x] > 1.6 * B and blk[:, max(0, x - 25):x + 25].mean() < 0.35:
            ys.append(y0 + B // 2); xs.append(lo + x)
    ys, xs = np.array(ys), np.array(xs)
    for _ in range(4):                                   # robust fit: a skewed rule drifts up to 100 px down the page
        k, c = np.polyfit(ys, xs, 1)
        r = np.abs(xs - (k * ys + c))
        keep = r <= max(6, 3 * np.median(r))
        if keep.all():
            break
        ys, xs = ys[keep], xs[keep]
    return float(k), float(c), int(ys.min() - B // 2), int(ys.max() + B // 2)


def regions(p):
    """{'L','R'}: (PIL image, x offset, y offset) for the two columns of PDF page p"""
    im = Image.open(f'{WORK}/img/pg-{p:04d}.png').convert('L')
    arr = np.asarray(im).copy()
    ink = (arr < 128).astype(np.int32)
    k, c, top, bot = rule_line(ink)
    h, w = arr.shape
    theta = 0.0
    if abs(k) > 0.003:                                    # skewed page: turn it until the rule is vertical
        import math
        theta = math.atan(k)
        for sign in (1, -1):
            rot = im.rotate(sign * math.degrees(theta), resample=Image.BICUBIC, fillcolor=255)
            a2 = np.asarray(rot).copy(); i2 = (a2 < 200).astype(np.int32)   # turning greys a hairline rule: keep it
            k2, c2, t2, b2 = rule_line(i2)
            if abs(k2) < abs(k) / 3:
                arr, ink, k, c, top, bot = a2, i2, k2, c2, t2, b2
                break
        else:
            theta = 0.0
    # exact ends of the rule: follow it past small breaks, and stop at the horizontal rule under the running head
    def has_rule(y):
        x = int(k * y + c)
        return ink[y:y + 6, x - 4:x + 5].sum() > 0
    def is_hrule(y):
        x = int(k * y + c)
        if y < 60 or ink[y:y + 6, x - 400:x + 400].max(axis=0).mean() <= 0.9:
            return False
        return ink[y - 50:y - 14, x - 400:x + 400].mean() < 0.3      # a thin line, not the black edge of the scan
    y = top + 100; gap = 0
    while y > 6 and gap < 45 and not is_hrule(y - 6):
        y -= 3
        gap = 0 if has_rule(y) else gap + 3
    top = y + gap
    for y in range(top, max(250, top - 1100), -3):         # a faint or broken rule: the head rule is the real top
        if is_hrule(y - 6):                                # (above y = 250 there is only the black edge of the scan)
            top = y
            break
    y = bot - 100; gap = 0
    while y < h - 12 and gap < 45:
        y += 3
        gap = 0 if has_rule(y) else gap + 3
    bot = min(h, y - gap + 70)                             # the last line can hang below the rule
    xr = (k * np.arange(h) + c).astype(int)
    cols = np.arange(w)[None, :]
    left, right = arr.copy(), arr.copy()
    left[(cols >= (xr - 4)[:, None]) | (cols < (xr - COLW)[:, None])] = 255
    right[(cols <= (xr + 6)[:, None]) | (cols > (xr + COLW)[:, None])] = 255
    xl0, xl1 = max(0, int(xr[top:bot].min()) - COLW), int(xr[top:bot].max())
    xr0, xr1 = int(xr[top:bot].min()), min(w, int(xr[top:bot].max()) + COLW)
    return {
        'L': (Image.fromarray(left[top:bot, xl0:xl1]), xl0, top),
        'R': (Image.fromarray(right[top:bot, xr0:xr1]), xr0, top),
    }, dict(k=k, c=c, top=top, bot=bot, w=w, h=h, theta=theta)


def prep(im, scale, despeckle, blur):
    if despeckle:
        from scipy import ndimage
        a = np.asarray(im) < 128
        lab, n = ndimage.label(a, structure=np.ones((3, 3)))
        sizes = ndimage.sum(a, lab, range(1, n + 1))
        small = np.isin(lab, 1 + np.where(sizes < despeckle)[0])
        arr = np.asarray(im).copy(); arr[small] = 255
        im = Image.fromarray(arr)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    if scale != 1:
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    return im
