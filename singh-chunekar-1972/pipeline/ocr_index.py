"""Re-OCR the two-column Latin/English index (PDF 499-515) one column at a time.

Automatic page segmentation sometimes floats the page numbers away from their
names; reading each column as a single block keeps every row together.
Overwrites $GLOSSARY_WORK/ocr/NNN.txt for those pages (left column, then right).
"""
import os
import numpy as np
from PIL import Image
import tesserocr

WORK = os.environ.get('GLOSSARY_WORK', 'work')
TESS = os.environ.get('TESSDATA_PREFIX', 'tessdata').rstrip('/') + '/'

def rule_line(im):
    """x position of the printed column rule as a straight line x = a*y + b
    (the scans are slightly skewed, so a vertical cut would clip page numbers)"""
    a = 255 - np.asarray(im.convert('L'), dtype=np.int32)       # ink = high
    h, w = a.shape
    lo, hi = int(w * 0.40), int(w * 0.60)
    ys, xs = [], []
    for y0 in range(int(h * 0.12), int(h * 0.94) - 150, 150):
        prof = a[y0:y0 + 150, lo:hi].sum(axis=0)
        if prof.max() > 3 * np.median(prof) + 1:
            ys.append(y0 + 75); xs.append(lo + int(np.argmax(prof)))
    if len(xs) < 3:
        return 0.0, w / 2
    ys, xs = np.array(ys), np.array(xs)
    keep = np.abs(xs - np.median(xs)) < 25                      # drop bands where text won
    k, c = np.polyfit(ys[keep], xs[keep], 1)
    return k, c

def columns(im):
    """left and right column images, blanking everything across the rule"""
    k, c = rule_line(im)
    arr = np.asarray(im.convert('L')).copy()
    h, w = arr.shape
    xr = (k * np.arange(h) + c).astype(int)
    left, right = arr.copy(), arr.copy()
    cols = np.arange(w)[None, :]
    left[cols >= (xr - 3)[:, None]] = 255
    right[cols <= (xr + 5)[:, None]] = 255
    x0, x1 = int(xr.min()) - 3, int(xr.max()) + 5
    return Image.fromarray(left[:, :x1]), Image.fromarray(right[:, x0:])

def main():
    api = tesserocr.PyTessBaseAPI(path=TESS, lang='script/Latin+script/Devanagari',
                                  psm=tesserocr.PSM.SINGLE_BLOCK)
    for p in range(499, 516):      # (the Sanskrit index reads better with automatic layout)
        im = Image.open(f'{WORK}/img/pg-{p:03d}.png')
        parts = []
        for col in columns(im):
            api.SetImage(col)
            parts.append(api.GetUTF8Text())
        open(f'{WORK}/ocr/{p:03d}.txt', 'w').write('\n'.join(parts))
    api.End()

if __name__ == '__main__':
    main()
