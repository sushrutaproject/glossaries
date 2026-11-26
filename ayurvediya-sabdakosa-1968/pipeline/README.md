# Āyurvedīya Śabdakośa, vol. 1: pipeline

Work directory: `work-sabdakosa/` (git-ignored). Set `GLOSSARY_WORK` and `TESSDATA_PREFIX` to absolute paths.
Python: `~/.venvs/glossaries/bin/python` (pipeline requirements of Singh & Chunekar, plus `lxml` and `scipy`).

| step | script | what it does | time |
|---|---|---|---|
| 0 | `pdfimages -png book.pdf img/x`, renamed `img/pg-NNNN.png` | page images as scanned (400 dpi, bitonal) | 1 min |
| 1 | `ocr_page.py N…` (`seq 1 1021 \| xargs -P 14 -n 4`) | column rule, deskew, Tesseract `script/Devanagari` (best) at 240 dpi → `ocr/NNNN.json` | 30 min |
| 2 | `parse.py` | headwords and sub-entries from line indents; three readings of each headword (ours, archive.org's hOCR in `ia/`, a second pass) → `entries.json` | 4 min (seconds once `reread.json` exists) |
| 3 | `lexcheck.py` | Monier-Williams keys (`lex/mw_keys.txt`, SLP1, one per line) confirm or correct the readings; sets the status. Edits `entries.json` in place: always run straight after `parse.py` | 1 min |
| 3a | `sheets.py` | contact sheets (24 numbered headword strips each, 20 sheets to a batch) of the headwords not yet `ok` → `claude/bNN/`. Claude reads each batch blind (instructions in `claude/prompt.txt`) and writes `claude/bNN/readings.json` | 3 min; reading 9,400 headwords took about 5 million tokens |
| 3b | `readings.py` | the readings by eye become the headwords; status from what supports them (an OCR reading, the word list). Run after `lexcheck.py` | 10 s |
| 4 | `build.py DATA_DIR` | citations (`cite.py`), scan regions; public index data in DATA_DIR, private full text in `out/full.json` | 10 s |
| 5 | `make_page.py DATA_DIR PAGE.html` | the public search page, from `concordance.json` and `template.html` alone | 2 s |
| 6 | `check_public.py` | fails if anything but index fields, or any running Devanāgarī text, is in `data/` or the page. Run before every commit of those | 2 s |
| — | `test_page.py PAGE.html QUERY` | smoke test of the page with local page images in place of archive.org (needs playwright) | |
| — | `review.py [N]` | private page with N random entries per status beside their scan strips → `out/review.html` | 20 s |

`lex/mw_keys.txt` was made from the `key` column of the Cologne `mwkeys.sqlite` (194,071 keys).
