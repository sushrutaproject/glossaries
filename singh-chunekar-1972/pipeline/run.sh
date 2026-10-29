#!/usr/bin/env bash
# Rebuild everything from your own copy of the scan.
#
#   ./run.sh path/to/Singh_and_Chunekar_1972.pdf
#
# The PDF is the Internet Archive item Singh-Chunekar-1972 (568 pages):
#   https://archive.org/details/Singh-Chunekar-1972
#
# Outputs (in ./out):  brhattrayi_glossary.sqlite, Brhattrayi_Glossary_Search.html  (full text: keep private)
#                      public/data/*  and  public/index.html                    (concordance only)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PDF=$(realpath "${1:?usage: run.sh book.pdf}")
export GLOSSARY_WORK=${GLOSSARY_WORK:-$PWD/work} GLOSSARY_OUT=${GLOSSARY_OUT:-$PWD/out}
export TESSDATA_PREFIX=${TESSDATA_PREFIX:-$PWD/tessdata} GLOSSARY_PDF=$PDF
mkdir -p "$GLOSSARY_WORK" "$GLOSSARY_OUT"

# 1. Tesseract models (tessdata 'fast-int' Latin + Devanagari scripts; tessdata_best Sanskrit)
if [ ! -f "$TESSDATA_PREFIX/script/Latin.traineddata" ]; then
  B=https://raw.githubusercontent.com/tesseract-ocr
  mkdir -p "$TESSDATA_PREFIX/script"
  curl -sSLf -o "$TESSDATA_PREFIX/script/Latin.traineddata"      $B/tessdata/main/script/Latin.traineddata
  curl -sSLf -o "$TESSDATA_PREFIX/script/Devanagari.traineddata" $B/tessdata/main/script/Devanagari.traineddata
  curl -sSLf -o "$TESSDATA_PREFIX/hin.traineddata"               $B/tessdata/main/hin.traineddata
  curl -sSLf -o "$TESSDATA_PREFIX/san_best.traineddata"          $B/tessdata_best/main/san.traineddata
  # tesseract needs its config files next to the models
  SYS=$(dirname "$(find /usr /opt /usr/local -name eng.traineddata -path '*tessdata*' 2>/dev/null | head -1)")
  ln -sfn "$SYS/configs" "$TESSDATA_PREFIX/configs"
fi

# 2. OCR all pages (parallel; about 30-40 minutes on two cores)
seq 1 568 | xargs -P "$(nproc)" -n1 "$HERE/ocr_page.sh"
python3 "$HERE/ocr_index.py"          # Latin index: one column at a time

# 3. Entries, headword reconciliation, citations, database, pages
cd "$GLOSSARY_WORK"
python3 "$HERE/parse.py"
python3 "$HERE/index_fix.py"
python3 "$HERE/build.py"
python3 "$HERE/assemble.py"
python3 "$HERE/make_public.py" "$GLOSSARY_OUT/public" "$GLOSSARY_OUT/public/index.html"
echo "done: $GLOSSARY_OUT"
