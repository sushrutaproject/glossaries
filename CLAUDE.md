# CLAUDE.md: handover for the *Glossaries* project

Read this first. It records the decisions, the state of the work and the open tasks as of 25 Nov 2026.
The project started in a Claude.ai session (28–29 Oct 2026) and continues here in Claude Code.

## Who and what

- **Owner:** Dominik Wujastyk (Sanskritist, historian of Indian medicine; reads code, is not a programmer).
  Keep explanations brief and to the point. Use IAST and Devanāgarī correctly. Don't explain Sanskrit basics.
- **Repo:** `sushrutaproject/glossaries`, part of the Suśruta Project. Site: <https://sushrutaproject.github.io/glossaries/>
  (GitHub Pages from `main` → `/docs`).
- **First (so far only) glossary:** Thakur Balwant Singh & K. C. Chunekar, *Glossary of Vegetable Drugs in Bṛhattrayī*,
  Chowkhamba Sanskrit Studies 77, Varanasi 1972. Scan: Internet Archive item
  [`Singh-Chunekar-1972`](https://archive.org/details/Singh-Chunekar-1972) (568-page PDF, OCR layer by ocrmypdf).

## The one hard rule: copyright

The book is **in copyright** (1972; Indian term = life + 60 years). The public repo and site hold **index data only**:
headwords, page numbers, botanical binomials, citation strings. **Never commit** the authors' discussion, synonym/vernacular
glosses, page OCR, errata text, or the book's index lists. The full text exists only in private builds
(`out/`, git-ignored). Readers see the discussion through live IIIF page images from archive.org, which are not hosted by us.

Before every commit that touches `singh-chunekar-1972/data/` or `docs/`:

```bash
python3 singh-chunekar-1972/pipeline/check_public.py .     # must print "public data OK"
```

It checks the field whitelist, runs of English prose in citations, sentinel phrases from the discussion, and that the page
payload carries no `paras`/`pages`/`errata`/`index`. Exception list: `KNOWN_OK` (one reviewed case, entry 662).

## Layout

```
CLAUDE.md                     this handover
README.md, LICENSE (MIT, code), LICENSE-DATA (CC BY 4.0, our contribution only)
docs/index.html               landing page (Suśruta Project style; hand-edited)
docs/singh-chunekar-1972/index.html   public search page = pipeline/template.html + public payload (GENERATED)
singh-chunekar-1972/
  README.md                   user-facing description, figures, reliability, how to cite
  data/concordance.json       public data (entries + refs), entries.csv, citations.csv   (GENERATED)
  pipeline/                   all code (see below)
```

`docs/singh-chunekar-1972/index.html` and `data/*` are **generated**. Never hand-edit them; change the template or the code and
regenerate. The page's look (PR #1, "Suśruta style": navy header, saffron accent, Spectral / IBM Plex Sans / Noto Serif
Devanagari) lives in `pipeline/template.html`, which serves **both** the public page and the private full-text page.
`D.public` switches modes: the public mode hides the "Full text" and "Other pages" tabs and the PDF link, and shows binomials.

## Pipeline (`singh-chunekar-1972/pipeline/`)

| step | script | what it does | time |
|---|---|---|---|
| 1 | `ocr_page.sh N` | pdftoppm 300 dpi grey → Tesseract 5, `script/Latin+script/Devanagari`; psm 6 for glossary (PDF 25–498) and errata (562–568), psm 3 elsewhere → `work/ocr/NNN.txt/.tsv` | ~35 min, all pages |
| 2 | `ocr_index.py` | re-reads the Latin index (PDF 499–515) column by column, splitting along the skewed printed rule | 2 min |
| 3 | `parse.py` | headword detection from TSV layout; re-reads each Devanāgarī headword with `san_best`, `hin`, `script/Devanagari` via tesserocr; merges with the roman capitals letter by letter → `work/entries.json` | ~10 min |
| 4 | `index_fix.py` | second witness from the book's Sanskrit index (exact roman match only) | seconds |
| 5 | `build.py` | splits each entry into identification / references / discussion; parses citations; entry scan regions; **private** SQLite (`out/brhattrayi_glossary.sqlite`) + `out/data.json` | 1 min |
| 6 | `assemble.py` | errata, both book indexes → **private** `out/Brhattrayi_Glossary_Search.html` | seconds |
| 7 | `make_public.py DEST SITE` | public concordance (binomials from the Latin index + direct recognition) + public page | seconds |
| — | `run.sh book.pdf` | all of the above, including model download | |
| — | `check_public.py`, `test_page.py PAGE QUERY [png]` | leak check; offline browser smoke test (IIIF mocked from local images) | |

Environment variables: `GLOSSARY_WORK` (default `./work`), `GLOSSARY_OUT` (`./out`), `TESSDATA_PREFIX` (`./tessdata`),
`GLOSSARY_PDF`. Use absolute paths. The scripts can then run from any directory.

To regenerate the public files after changing code or template (OCR already done), from the repo root:

```bash
export GLOSSARY_WORK=$PWD/work GLOSSARY_OUT=$PWD/out TESSDATA_PREFIX=$PWD/tessdata
P=singh-chunekar-1972/pipeline
python3 $P/build.py && python3 $P/assemble.py
python3 $P/make_public.py out/public out/public/index.html
cp out/public/data/* singh-chunekar-1972/data/ && cp out/public/index.html docs/singh-chunekar-1972/index.html
python3 $P/check_public.py . && python3 $P/test_page.py docs/singh-chunekar-1972/index.html tagara
```

**Baseline (25 Nov 2026):** this sequence, run on the bundled OCR, reproduces the committed `concordance.json` and the public
page byte for byte. After a code change, `git diff --stat` on the generated files therefore shows exactly what your change did.

If you change `parse.py`, re-run from step 3 (`parse.py` → `index_fix.py` → `build.py` …). `index_fix.py` edits
`entries.json` in place, so always run it straight after `parse.py`.

### Setting up locally

- Dominik's machine (`cakrapani`, Linux Mint; clone at `/home/dom/Dropbox/git-repositories/glossaries`) has system
  `tesseract` **4.1.1** and `pdftoppm`. That's enough for page images. The headword re-reading (step 3) and `ocr_index.py` use
  `tesserocr`, whose pip wheel bundles its own Tesseract 5, so: `pip install -r singh-chunekar-1972/pipeline/requirements.txt`
  (in a venv, or with `--user`). Only a full re-OCR (step 1, normally skipped thanks to the bundle) wants system Tesseract ≥ 5.
  For `test_page.py`: `pip install playwright && playwright install chromium`.
- The clone lives in Dropbox. `work/` (~12 MB of OCR, plus ~110 MB of page images once rendered) and `out/` will sync too.
  If that's unwanted, point `GLOSSARY_WORK`/`GLOSSARY_OUT` outside Dropbox.
- `work/` belongs to the Singh & Chunekar pipeline. A second book (e.g. *Āyurvedīya Śabdakośa*, 1968) needs its own folder and
  its own work directory, such as `ayurvediya-sabdakosa-1968/` and `work-sabdakosa/`. Don't mix its OCR into `work/ocr/`.
- Models: `run.sh` downloads them from raw.githubusercontent.com (Latin and Devanāgarī script models, `hin`, and tessdata_best
  `san` saved as `san_best`) and symlinks the system `configs/` folder into `tessdata/`. Without that symlink the TSV output
  is silently skipped.
- **Skip the 35-minute OCR:** Dominik has `glossary_work_bundle.zip` (private: it contains full-text OCR). Unzip it in the repo root
  to get `work/ocr/` and `work/entries.json`. Then put the PDF at `work/book.pdf`, render images
  (`pdftoppm -r 300 -gray -png work/book.pdf work/img/pg`, a few minutes) and run steps 2–7. `work/`, `out/`, `tessdata/`, PDFs
  and `*.sqlite` are git-ignored: keep them that way.

## Key facts and conventions

- **Pages:** book page = PDF page − 24. archive.org viewer leaf `n{pdf−1}`. IIIF image for PDF page *p*:
  `https://iiif.archive.org/image/iiif/3/Singh-Chunekar-1972%2F<zip>%2F<dir>%2F<file>_{p−1:04d}.jp2/{region}/{w},/0/default.jpg`
  (full string in `template.html`, constant `IIIF`). Canvases are 2854×4773 px (600 dpi); entry crops use `pct:0,y,100,h`
  computed from 300-dpi OCR coordinates (`build.py: segments`; `PAGE_H=2387`, `TEXT_TOP=150`, `LINE_H=52`).
- **Headword status:** `ok` 1637, `probable` 336, `check` 214, out of 2187 headwords in 1848 entries. In `check` cases the
  IAST is usually right and the Devanāgarī often wrong (bold conjuncts, ṛ-mātrā).
- **Citations:** 30,342 (C.S. 11,412 · S.S. 9,462 · A.H. 9,468) as `[entry_id, text, sthana, chapter, verse]`;
  sthāna codes Sū Ni Vi Śā In Ci Ka Si U; Caraka Ci. 1 as `1-1`…`1-4`. A missing sthāna inherits from the previous group.
  Sanity check: C.S. Sū. 4.47 returns exactly Caraka's ten *vedanāsthāpana* drugs.
- **Botanical names:** 286 entries with identification, 332 with further names discussed, 669 distinct. Nomenclature and
  spellings are the book's (1972).
- Commits end with the Co-Authored-By line. Work on a branch and open a PR. PR #1 was merged by the owner.

## Open tasks (suggested order)

1. **Corrections layer.** No mechanism yet. Proposal: `singh-chunekar-1972/corrections.csv`
   (`entry_id, field, old, new, source, note`) applied at the end of `build.py`, so that corrections survive re-runs. Then work through
   the 214 `check` headwords against the IIIF crops (a small review page listing crop + current reading would help).
2. **Four missed headwords** (folded into the previous entry): entry 361 → KĀKODU(DU)MBARIKĀ (p. 89); 914 → NĀDEYĪ (p. 222);
   1597 → ŚITIVĀ(-MĀ)RAKA (p. 398); 1652 → ŚLEṢMĀTAKĪ (p. 413). The causes are a heading glued to the previous line, and
   trailing junk `ा`/`ल्‍` (ZWJ). See `parse.py: stage1` (`JUNK_TOK`, split-heading logic).
3. **Citation lines lost:** entries 461 and 1141 (`S. S. CI.`: the `REF_START` look-ahead needs `[A-Z][a-zI]`); 669, 684, 902
   (lines with notes like "(both Jaṭā and Māṃsī)" are rejected by the `PROSE` guard in `build.py`). Extract the citations and drop
   the note rather than drop the line. 64 entries have no citations, mostly "See synonym…" cross-references: check a sample.
4. **Errata** (174, PDF 563–568) are only shown in the private page. They could be applied to the citations: a correction is a
   fact, but keep the errata text itself out of the public files.
5. **Supplement** (PDF 562) adds entries that are not parsed.
6. Possible extras the owner was offered: a searchable PDF with the new Devanāgarī/IAST text layer (private); linking citations
   to the Suśruta Project's own S.S. texts; further glossaries in this repo (folder per work, same pattern).

## Gotchas

- Bash `pkill -f <pattern>` can kill your own shell if the pattern appears in the command line.
- Tesseract writes nothing for `-c tessedit_create_tsv=1` if `configs/` is missing from `TESSDATA_PREFIX`. It doesn't fail.
- Scans are skewed (the left margin drifts by up to 35 px per page), so don't use fixed x thresholds.
- `fold()` (diacritic-free key) is what all matching uses; IAST output is NFC.
- The prose guard trades recall for safety. When you loosen it, rerun `check_public.py`.
