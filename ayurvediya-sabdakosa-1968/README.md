# Āyurvedīya Śabdakośa, vol. 1 (1968): index of headwords and citations

Veṇīmādhavaśāstrī Jośī & Nārāyaṇa Harī Jośī, *Āyurvedīya Śabdakośa*, vol. 1.
Mumbaī: Mahārāṣṭra Rājya Sāhitya-Saṃskṛti Maṇḍaḷa, 1968.
Scan: Internet Archive, [`ayurvediya-sabdakosa-v-1-1968`](https://archive.org/details/ayurvediya-sabdakosa-v-1-1968).

**Search page:** <https://sushrutaproject.github.io/glossaries/ayurvediya-sabdakosa-1968/>

## What is here

Index data only. The glosses of the dictionary are **not** transcribed: the search page shows each entry's piece of the
page image live from the Internet Archive.

| file | contents |
|---|---|
| `data/concordance.json` | 25,463 entries and 41,526 citations, with the fields below |
| `data/entries.csv` | one row per entry: headword (IAST and Devanāgarī), status, kind, parent, gender, page, column, scan link |
| `data/citations.csv` | one row per citation: entry, text, sthāna, chapter, verse, commentator |

An entry is a main headword or a sub-entry (printed as `-मर्मन्` under its headword; given here in full, joined without
sandhi). Citations use the text codes of the Singh & Chunekar concordance (`C.S.`, `S.S.`, `A.H.`) and add `A.S.`, `K.S.`,
`Rā.N.`, `Dh.N.`, `R.R.S.` and others. Chapter and verse numbers are the book's own.

## How reliable

- The pages were read by OCR (Tesseract 5, `script/Devanagari`), each headword three times, and checked against the
  Monier-Williams word list. The 9,400 headwords that this left in doubt were then read from the scan by Claude (an AI
  model); these have `read: eye`. **No headword has been proofread by a person.**
- Status: `ok` 24,421 (the reading has independent support), `probable` 936, `check` 107. A trial suggests that a few per
  cent of the `ok` headwords that were not read by eye are still wrong.
- About 6% of the citation abbreviations could not be resolved, and those citations are missing.
- Six pages (book pp. 72, 310, 357, 463, 655, 797), the front matter, the appendix and the tables are not included.

Corrections are welcome as GitHub issues. Please cite the book itself for its scholarship.
