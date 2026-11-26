# CLAUDE.md: handover for the *Glossaries* project

Read this first. It records the decisions, the state of the work and the next task as of 26 Nov 2026.
The project started in a Claude.ai session (28–29 Oct 2026) and continues here in Claude Code.

**Status:** the Singh & Chunekar glossary is **finished, published and working well**: leave it alone unless asked.
**Current task:** add a second work, the *Āyurvedīya Śabdakośa* (see "Current task" below), using Singh & Chunekar
as the worked example.

## Who and what

- **Owner:** Dominik Wujastyk (Sanskritist, historian of Indian medicine; reads code, is not a programmer).
  Keep explanations brief and to the point. Use IAST and Devanāgarī correctly. Don't explain Sanskrit basics.
- **Repo:** `sushrutaproject/glossaries`, part of the Suśruta Project. Site: <https://sushrutaproject.github.io/glossaries/>
  (GitHub Pages from `main` → `/docs`).
- **Done:** Thakur Balwant Singh & K. C. Chunekar, *Glossary of Vegetable Drugs in Bṛhattrayī*,
  Chowkhamba Sanskrit Studies 77, Varanasi 1972. Scan: Internet Archive item
  [`Singh-Chunekar-1972`](https://archive.org/details/Singh-Chunekar-1972) (568-page PDF, OCR layer by ocrmypdf).

## Current task: *Āyurvedīya Śabdakośa* (1968)

Veṇīmādhavaśāstrī Jośī & Nārāyaṇa Harī Jośī, *Āyurvedīya Śabdakośa: Saṃskṛta–Marāṭhī*, 2 vols.
Mumbaī: Mahārāṣṭra Rājya Sāhitya-Saṃskṛti Maṇḍaḷa, 1968. (Check this bibliographic detail against the title page.)

**What we have**
- Vol. 1: `work-sabdakosa/Ayurvediya Sabdakosa-v1_1968.pdf` (1021 pages, 131,443,937 bytes, image-only, **no text layer**;
  each page is one 400-dpi bitonal image, 3296×4672 px). `work-sabdakosa/` is git-ignored via `work-*/`.
- Internet Archive: [`ayurvediya-sabdakosa-v-1-1968`](https://archive.org/details/ayurvediya-sabdakosa-v-1-1968) holds the
  **identical** PDF (same byte size), so the archive.org viewer links and IIIF crops work exactly as for Singh & Chunekar.
  The item also has `_jp2.zip` (1021 leaves), `_scandata.xml`, `_page_numbers.json` (IA's printed-page mapping) and IA's own
  OCR (`_hocr.html`, `_djvu.txt`, `_chocr.html.gz`), which can serve as a second OCR witness.
  Vol. 2: [`ayurvediya-sabdakosa-v-2-1968`](https://archive.org/details/ayurvediya-sabdakosa-v-2-1968) (not downloaded yet).
  There is also an item `ayurvediya-sabdakosa-1968` (same uploader, 2021). Check what it is.
  IIIF image ids follow the IA pattern `<id>%2F<file>_jp2.zip%2F<file>_jp2%2F<file>_NNNN.jp2`. Read the exact string from
  `https://iiif.archive.org/iiif/3/<id>/manifest.json`, and verify that leaf n = PDF page n+1 from the scandata
  (no pages with `addToAccessFormats=false`). Checked 25 Nov 2026: 1021 leaves, all `addToAccessFormats=true`; IA's hOCR
  boxes are in the same pixel frame as the PDF's page images. IA ran `tesseract -l mar+nep+hin+Devanagari` on whole pages.

**State of the work (26 Nov 2026): all six steps done for vol. 1; the public page is built and awaits its PR and merge.**
Dominik decided (26 Nov 2026) to publish on the **index-only** basis; the copyright status is still not established.

- Code: `ayurvediya-sabdakosa-1968/pipeline/` (its README has the step table): `ocr_page.py` → `parse.py` → `lexcheck.py` →
  `sheets.py` / `readings.py` → `build.py` → `make_page.py`; `check_public.py`, `test_page.py`, `review.py`.
  The first OCR run used `work-sabdakosa/ocr_all.py` and `trial/`, which `columns.py` and `ocr_page.py` now replace.
- Figures: 25,463 entries (13,454 main headwords, the rest sub-entries), 41,526 citations (94% of the abbreviations resolved).
  Headword status: 24,421 ok, 936 probable, 107 check.
- **Headwords read by eye.** The 9,394 headwords whose OCR readings disagreed or which Monier-Williams does not list were read
  from contact sheets of the scan by Claude subagents (19 batches of 20 sheets, 24 strips a sheet; about 5 million tokens;
  instructions in `work-sabdakosa/claude/prompt.txt`). In a blind trial on 48 headwords already marked ok, the reading by eye
  was right on all 48 and the agreed OCR reading wrong on 2. So about 4% of the 16,000 unread "ok" headwords are probably
  wrong, and a wrong parent spoils the full form of its sub-entries (e.g. `जीणेबुध्नक`). Reading the rest would cost about
  9 million tokens; reading only the "ok" parents that have sub-entries, about 2,500, much less. Not done: ask Dominik.
- **The entry ids are fixed** by `claude/*/key.json`: do not renumber entries or re-run `parse.py` with changes that shift
  them without re-keying the readings. One id (12824, a line with no headword) is left out of the public data.
- Not done: the six pages without a column rule and the table (below); front matter, abbreviation table, appendix and end
  tables; `अहृवसू` (about 120 citations) and other unresolved abbreviations; vol. 2. The verse numbers follow the editions the
  book used and agree with Singh & Chunekar's on only a quarter of shared citations (the chapter on 60%), so joint queries
  work by chapter. The title-page question below is still open; the page calls the book only "a dictionary of the
  vocabulary of the Sanskrit medical classics".
- Private files in `work-sabdakosa/`:

- `img/pg-NNNN.png`: the page images as scanned (`pdfimages -png`, 249 MB). `ia/`: IA's hOCR, djvu.txt, scandata, page numbers.
- `ocr/NNNN.json` + `.txt`: the OCR of all 1021 pages. JSON: `kind` (`columns` or `page`), `geo` (rule position `c`, column
  `top`/`bot`, skew `theta`), `regions` `H` (running head), `L`, `R` (or `P` for a whole page); each line has text `t`, box `b`,
  confidence, words `w` with boxes, and `o` = the line's centre in the unrotated scan (for IIIF crops and for matching IA's lines).
  Boxes are in the deskewed frame.
- `ocr_all.py N…` (run with `xargs -P 14 -n 4`; 30 minutes for the book on the 16 cores) uses `trial/ocr_trial.py`
  (`rule_line`, `regions`: find the column rule, deskew, cut the columns) and `trial/variants.py` (`prep`: smoothing and scaling).
- `trial/ocr-trial.html`: the trial report for 8 pages, scan strip beside our reading and IA's. `trial/gt.json`: 27 lines read by
  hand (by Claude, from PDF 60 and 800), the only ground truth so far. `trial/variants.py LANGS SCALES DESPECKLE BLURS tag` scores settings against it.

**OCR setting chosen** (trial on PDF 23, 60, 61, 200, 400, 600, 800, 990): cut the columns along the rule, Gaussian blur 1.5,
reduce to 60% (240 dpi), Tesseract (tesserocr's 5.5) with **`script/Devanagari` from tessdata_best**, psm 6. Character error on the
27 lines: 4.9%, against 8.7% for the same model at 400 dpi, 9.0% for IA's OCR, and 11–13% for `san`/`mar` (tessdata_best), 18% for `hin`.
IA's reading is often right where ours is wrong, so keep it as the second witness for headwords. Recurring errors to allow for
when parsing: `-स्त्री.` misread (`स्नी`, `ल्ली`); full stop and comma confused inside citations; `ल`/`ळ`, `ध`/`घ`; stray leading
punctuation from specks at the left margin.

**Pages.** Printed page = PDF page − 22. The dictionary runs from PDF 23 (printed 1) to about PDF 994 (the last page with a
dictionary running head; confirm against the scan). Each letter opens on a new page with a large title, the letter, and a shorter
text block (e.g. PDF 177 for क). Front matter PDF 1–22, with the **abbreviation table at PDF 20–22**; an appendix in another layout
around PDF 1000; tables (apparently errata) at PDF 1010–1021. None of these has had special handling.

**Pages to look at by hand:** no column rule found, read as whole pages: PDF 94, 332, 379, 485, 677, 819. A table inside the
dictionary: PDF 97–98. Running head not recognised: PDF 418, 471, 688, 976, 994. The printed page number in the head was read
correctly on only 330 of 966 pages, so it is a weak check.

**To check on the title page (PDF 3):** it appears to read आयुर्वेदीय महाकोशः अर्थात् आयुर्वेदीय शब्दकोशः, संस्कृत–संस्कृत, and the glosses
on the sample pages are mostly Sanskrit, not Marathi. Seen at thumbnail size only.

**Layout** (seen on PDF p. 60, printed p. ३८): two columns divided by a printed vertical rule, with a horizontal rule under the
running head. The vertical rule is a hairline, sometimes broken, and sits anywhere from 43% to 59% of the scan width; pages are
skewed by up to 2° (`trial/ocr_trial.py` handles this: robust line fit, deskew, head rule as the column top). Running head: page number in Devanāgarī numerals, `[ first headword ]`,
`आयुर्वेदीय - शब्दकोशः`, `[ last headword ]`. Entirely Devanāgarī: a **bold Sanskrit headword** at the column margin, then
`-पुं.`/`-स्त्री.`/`-न.`/`-वि.` (gender or part of speech), then Sanskrit and Marathi glosses. Sub-entries begin with a dash and a
compound member (`—कल्क-पुं.`, `—भव-पुं.`). Citations sit in parentheses with **Devanāgarī numerals**: text abbreviations such as
`सुशा.`, `सुउ.`, `चसू.`, `चचि.`, `अहृसू.`, `असंसू.`, `रा.`, `ध.`, `र.`, `मा.` (text and sthāna run together), then chapter and
verse. The numerals are in the Marathi forms (१ looks like a Latin 9); Tesseract reads them correctly. Build the abbreviation table from the book's own list in the front matter.

**Suggested plan.** Agree each step with Dominik; the decisions are his.
1. **Scope and copyright.** Decide with Dominik what may be public. This is a 1968 Maharashtra State (Sāhitya-Saṃskṛti
   Maṇḍaḷa) publication, and its copyright status isn't established. Until it is, **apply the same index-only rule** as for
   Singh & Chunekar (headwords, gender, page/column, parsed citations; no glosses).
2. **Scaffold** `ayurvediya-sabdakosa-1968/{pipeline,data}/` and `docs/ayurvediya-sabdakosa-1968/`, plus a card on `docs/index.html`.
   Start by **copying** the Singh & Chunekar pipeline and adapting it. Factor out shared code only once both work.
3. **Done** (see "State of the work" above). **OCR trial** on 5–10 sample pages: split columns along the rule, then Tesseract with `san`/`mar` from tessdata_best,
   the Devanāgarī script model, and IA's hOCR as a comparison. Pick by inspection, then run all 1021 pages in the background
   (several hours on two cores; `xargs -P`).
4. **Entries:** a headword is a line-initial bold word followed by a gender/part-of-speech tag; sub-entries start with a dash.
   Keep column (left/right) and y-position for the IIIF crop of each entry.
5. **Citations:** map the abbreviations to text and sthāna, convert Devanāgarī numerals, and reuse the
   `[entry, text, sthana, chapter, verse]` scheme, so that both glossaries can later be queried together (e.g. C.S. Sū. 4.47).
6. **Public page:** generalise `template.html` (title, IIIF base, abbreviations as data), write a `check_public.py` for this book
   (Marathi sentinel words, not English), test with `test_page.py`, then open a PR.

## The one hard rule: copyright

This applies to every book in the repo unless its status has been established otherwise.
The Singh & Chunekar book is **in copyright** (1972; Indian term = life + 60 years). The public repo and site hold **index data only**:
headwords, page numbers, botanical binomials, citation strings. **Never commit** the authors' discussion, synonym/vernacular
glosses, page OCR, errata text, or the book's index lists. The full text exists only in private builds
(`out/`, git-ignored). Readers see the discussion through live IIIF page images from archive.org, which are not hosted by us.

Before every commit that touches a `data/` folder or `docs/`:

```bash
python3 singh-chunekar-1972/pipeline/check_public.py .          # must print "public data OK"
python3 ayurvediya-sabdakosa-1968/pipeline/check_public.py .    # the same for the Śabdakośa
```

The Śabdakośa check allows only the index fields and fails on any two Devanāgarī words in a row (running text).

It checks the field whitelist, runs of English prose in citations, sentinel phrases from the discussion, and that the page
payload carries no `paras`/`pages`/`errata`/`index`. Exception list: `KNOWN_OK` (one reviewed case, entry 662).

## Layout

```
CLAUDE.md                     this handover
README.md, LICENSE (MIT, code), LICENSE-DATA (CC BY 4.0, our contribution only)
docs/index.html               landing page (Suśruta Project style; hand-edited)
docs/singh-chunekar-1972/index.html   public search page = pipeline/template.html + public payload (GENERATED)
docs/ayurvediya-sabdakosa-1968/index.html   the same for the Śabdakośa (GENERATED by its make_page.py from data/ alone)
ayurvediya-sabdakosa-1968/    README.md, data/ (GENERATED), pipeline/ (own template.html; not shared with Singh & Chunekar)
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

- Dominik's machine (`cakrapani`, Linux Mint; clone at `/home/dom/Dropbox/git-repositories/glossaries`) has 16 cores, system
  `tesseract` **5.3.4** (found 25 Nov 2026; an earlier note said 4.1.1) and `pdftoppm`. A virtualenv with the pipeline requirements
  plus `lxml` and `scipy` is at **`~/.venvs/glossaries`** (outside Dropbox); use `~/.venvs/glossaries/bin/python`. `tessdata/` in the
  repo root holds the models, including `script/Devanagari_best`, `san_best`, `mar_best`, `hin_best`. That's enough for page images. The headword re-reading (step 3) and `ocr_index.py` use
  `tesserocr`, whose pip wheel bundles its own Tesseract 5, so: `pip install -r singh-chunekar-1972/pipeline/requirements.txt`
  (in a venv, or with `--user`). Only a full re-OCR (step 1, normally skipped thanks to the bundle) wants system Tesseract ≥ 5.
  For `test_page.py`: `pip install playwright && playwright install chromium`.
- The clone lives in Dropbox. `work/` (~12 MB of OCR, plus ~110 MB of page images once rendered) and `out/` will sync too.
  If that's unwanted, point `GLOSSARY_WORK`/`GLOSSARY_OUT` outside Dropbox.
- `work/` belongs to the Singh & Chunekar pipeline (its OCR came from Dominik's private bundle). Keep each book's
  OCR in its own work directory (`work-sabdakosa/` for the Śabdakośa) and point `GLOSSARY_WORK` at it.
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

## Singh & Chunekar: optional refinements (low priority; it works well, do only if asked)

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
