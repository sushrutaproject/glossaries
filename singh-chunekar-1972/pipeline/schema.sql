-- Glossary of Vegetable Drugs in Bṛhattrayī (Singh & Chunekar 1972) — OCR database
CREATE TABLE entries (
  id INTEGER PRIMARY KEY,          -- running number in book (Nāgarī) order
  headword_iast TEXT,              -- IAST; several headwords joined by ' / '
  headword_deva TEXT,              -- Devanāgarī as read by OCR
  headword_plain TEXT,             -- diacritic-free, lower case (for easy matching)
  ocr_status TEXT,                 -- ok | probable | check  (headword agreement of the two scripts)
  pdf_page_start INTEGER, pdf_page_end INTEGER,
  book_page_start TEXT, book_page_end TEXT,
  identification TEXT,             -- botanical name / synonyms / vernaculars before the references
  refs_cs TEXT, refs_ss TEXT, refs_ah TEXT,   -- citation strings for Caraka, Suśruta, Aṣṭāṅgahṛdaya
  discussion TEXT,                 -- the authors' discussion
  full_text TEXT
);
CREATE TABLE headwords (entry_id INTEGER, n INTEGER, iast TEXT, deva TEXT, plain TEXT, status TEXT);
CREATE TABLE refs (entry_id INTEGER, text TEXT, sthana TEXT, chapter TEXT, verse TEXT);
CREATE TABLE pages (pdf_page INTEGER PRIMARY KEY, book_page TEXT, section TEXT, text TEXT);
CREATE INDEX refs_idx ON refs(text, sthana, chapter, verse);
CREATE INDEX hw_plain ON headwords(plain);
CREATE VIRTUAL TABLE entries_fts USING fts5(headword_iast, headword_deva, headword_plain,
  identification, discussion, full_text, content='entries', content_rowid='id',
  tokenize='unicode61 remove_diacritics 2');
CREATE VIRTUAL TABLE pages_fts USING fts5(text, content='pages', content_rowid='pdf_page',
  tokenize='unicode61 remove_diacritics 2');
