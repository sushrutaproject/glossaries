"""Contact sheets of headword lines, for reading by eye (by Claude): 24 numbered strips to a sheet, 20 sheets to a batch.

  python sheets.py            the headwords whose status is not 'ok' and that have no reading yet

Writes $GLOSSARY_WORK/claude/bNN/sheet-NN.png and key.json ({sheet: [entry ids]}).  The reader writes
bNN/readings.json ({sheet: [24 readings]}); readings.py brings these into entries.json.  Private: page images.
"""
import glob, json, os, random
from PIL import Image, ImageDraw, ImageFont
from columns import WORK, regions

PER, BATCH = 24, 20


def done():
    """entry ids that already have a reading"""
    ids = set()
    for kf in glob.glob(f'{WORK}/claude/*/key.json'):
        rf = kf.replace('key.json', 'readings.json')
        if not os.path.exists(rf): continue
        K, R = json.load(open(kf)), json.load(open(rf))
        for sh, es in K.items():
            if len(R.get(sh, [])) == len(es): ids.update(es)
    return ids


def main():
    d = json.load(open(f'{WORK}/entries.json')); L = d['lines']
    have = done()
    todo = [e for e in d['entries'] if e['status'] != 'ok' and e['id'] not in have]
    todo.sort(key=lambda e: (L[e['line']]['p'], e['id']))
    strips, page, regs = [], None, None
    for e in todo:                                         # cut the strips page by page
        l = L[e['line']]
        if l['p'] != page: page, regs = l['p'], regions(l['p'])[0]
        im, ox, oy = regs[l['col']]
        st = im.crop((0, max(0, l['b'][1] - oy - 8), im.width, l['b'][3] - oy + 8))
        strips.append((e['id'], st.resize((int(st.width * 40 / st.height), 40)).crop((0, 0, 530, 40))))
    random.seed(100); random.shuffle(strips)               # shuffled: the reader gets no help from the alphabet
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
    n = 0
    for b in range(0, len(strips), PER * BATCH):
        name = f'b{b // (PER * BATCH) + 1:02d}'; os.makedirs(f'{WORK}/claude/{name}', exist_ok=True); key = {}
        part = strips[b:b + PER * BATCH]
        for s in range(0, len(part), PER):
            chunk = part[s:s + PER]
            sheet = Image.new('L', (570, len(chunk) * 44), 255); dr = ImageDraw.Draw(sheet)
            for i, (eid, st) in enumerate(chunk):
                sheet.paste(st, (38, i * 44 + 2)); dr.text((3, i * 44 + 12), str(i + 1), fill=0, font=font)
                dr.line((0, i * 44 + 43, 570, i * 44 + 43), fill=200)
            sn = f'sheet-{s // PER + 1:02d}'; sheet.save(f'{WORK}/claude/{name}/{sn}.png'); key[sn] = [eid for eid, _ in chunk]; n += 1
        json.dump(key, open(f'{WORK}/claude/{name}/key.json', 'w'))
        print(name, len(key), 'sheets', len(part), 'headwords')
    print(len(strips), 'headwords on', n, 'sheets')


if __name__ == '__main__':
    main()
