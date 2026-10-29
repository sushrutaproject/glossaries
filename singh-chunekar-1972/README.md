# Singh & Chunekar, *Glossary of Vegetable Drugs in Bṛhattrayī* (1972): concordance

Thakur Balwant Singh and K. C. Chunekar, *Glossary of Vegetable Drugs in Brhattrayi*.
Chowkhamba Sanskrit Studies 77. Varanasi: Chowkhamba Sanskrit Series Office, 1972. 474 + xxiv pp.

The glossary lists every plant name in the Carakasaṃhitā, Suśrutasaṃhitā and Aṣṭāṅgahṛdaya,
in Nāgarī order, with the authors' botanical identification and every place each name occurs.
This folder makes that apparatus searchable.

**Search it online:** <https://sushrutaproject.github.io/glossaries/singh-chunekar-1972/>
**Scan:** Internet Archive, [`Singh-Chunekar-1972`](https://archive.org/details/Singh-Chunekar-1972)

## What is here

| | |
|---|---|
| Entries | 1,848 (with 2,187 headwords) |
| Saṃhitā citations, parsed to text / sthāna / chapter / verse | 30,342 (C.S. 11,412, S.S. 9,462, A.H. 9,468) |
| Entries with a botanical identification in the heading | 286 |
| Entries discussing further botanical names | 332 |
| Distinct botanical names | 669 |

The book is still in copyright, so the repository holds **index data only**: headwords, page numbers,
botanical names and citations. The authors' discussion is not included. The search page shows each
entry's own region of the printed page, served live from the Internet Archive through
[IIIF](https://iiif.io), so the discussion can be read in the original.

## Files

`data/concordance.json`: everything, one object per entry:

```json
{
  "id": 112,
  "headwords": [{"deva": "अशोक", "iast": "aśoka", "status": "ok"}],
  "book_pages": [26, 26], "pdf_pages": [50, 50],
  "scan": "https://archive.org/details/Singh-Chunekar-1972/page/n49/mode/1up",
  "identification": ["Saraca indica Linn."],
  "also_discussed": [],
  "citations": {"C.S.": "Su. 4. 47; Vi. 8. 151.", "S.S.": "Su. 6. 28; …", "A.H.": "Ci. 3. 10; 21. 34."},
  "scan_regions": [{"pdf_page": 50, "iiif_region": "pct:0,69.0,100,18.14"}]
}
```

plus `refs`: every citation as `[entry_id, text, sthana, chapter, verse]`.

`data/entries.csv`: one row per entry (headwords, pages, botanical names, citation strings, scan link).
`data/citations.csv`: one row per citation, for questions such as *which plants does the glossary cite at C.S. Sū. 4.47?*

**Scan images.** `pdf_pages` are the page numbers of the archive.org PDF (568 pages; book page = PDF page − 24).
The IIIF image service for PDF page *p* is

```
https://iiif.archive.org/image/iiif/3/Singh-Chunekar-1972%2F{zip}%2F{dir}%2F{file}_{p−1, 4 digits}.jp2
```

(see `docs/singh-chunekar-1972/index.html` for the full string). Append `/{iiif_region}/1000,/0/default.jpg`
to get the image of one entry.

**Sthāna abbreviations:** Sū, Ni, Vi, Śā, In, Ci, Ka, Si, U. Caraka Ci. 1 is cited by pāda as `1-1`, `1-2` and so on.

## How it was made

1. **OCR.** All 568 pages were OCRed with Tesseract 5 using the Latin-script and Devanāgarī-script models, which
   keep IAST diacritics. The two-column Latin index was read one column at a time.
2. **Entries.** Headword lines were recognised by layout: a Devanāgarī word followed by spaced roman capitals at the left margin.
3. **Headwords.** Each Devanāgarī headword was re-read with the Sanskrit (tessdata_best), Hindi and Devanāgarī-script models.
   The reading whose transliteration best matched the roman capitals was kept, and the two were merged letter by letter.
   Diacritics come from the Devanāgarī; known OCR slips in the capitals (J/I, Ī/T and so on) are corrected.
   In doubtful cases, the book's own Sanskrit index, printed in regular type, served as a second witness.
4. **Citations.** The C.S./S.S./A.H. paragraphs were parsed. A missing sthāna carries over from the previous group,
   as in the book.
5. **Botanical names.** Names from the book's Latin index (`Genus species Author`) were matched to the entries on
   the indexed pages. Binomials of indexed genera in the heading lines were added directly.

The code is in [`pipeline/`](pipeline/). With your own copy of the PDF:

```bash
pip install -r pipeline/requirements.txt     # also needs tesseract ≥ 5 and poppler-utils
pipeline/run.sh path/to/Singh-Chunekar-1972.pdf
```

This also builds a full-text database and search page for private study (`out/`, ignored by git).

## Reliability

Every headword has a `status`:

- **ok** (1637): the Devanāgarī and roman readings agree letter for letter.
- **probable** (336): they differ by one letter.
- **check** (214): they disagree. The IAST is usually right, but the Devanāgarī often is not, mostly in conjuncts and ऋ-mātrā in bold type.
  Check the scan.

Citation numbers come from OCR of small type. Parsing errors are rare but possible (e.g. a dropped `Ci.`).
Check the scan before quoting. Botanical names keep the book's own (1972) nomenclature and spellings,
including occasional OCR slips in the authority.

Corrections are very welcome as [issues](https://github.com/sushrutaproject/glossaries/issues) or pull requests.

## How to cite

Cite the book for the scholarship, and this repository for the data:

> Singh, Thakur Balwant, and K. C. Chunekar. 1972. *Glossary of Vegetable Drugs in Brhattrayi*. Varanasi: Chowkhamba Sanskrit Series Office.
>
> The Sushruta Project. 2026. "Singh & Chunekar 1972: concordance." https://github.com/sushrutaproject/glossaries
