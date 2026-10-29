#!/usr/bin/env bash
# OCR one page of the scan: ocr_page.sh N   ->  $GLOSSARY_WORK/ocr/NNN.txt + .tsv
# Glossary pages (PDF 25-498) and the supplement/errata (562-568) are single blocks (psm 6);
# the two-column indexes and front matter use automatic layout (psm 3).
set -u
p=$1; P=$(printf %03d "$p")
WORK=${GLOSSARY_WORK:-work}
PDF=${GLOSSARY_PDF:-$WORK/book.pdf}
export TESSDATA_PREFIX=${TESSDATA_PREFIX:-tessdata} OMP_THREAD_LIMIT=1
mkdir -p "$WORK/img" "$WORK/ocr"
[ -s "$WORK/ocr/$P.tsv" ] && exit 0
[ -f "$WORK/img/pg-$P.png" ] || pdftoppm -f "$p" -l "$p" -r 300 -gray -png "$PDF" "$WORK/img/pg" >/dev/null 2>&1
if { [ "$p" -ge 25 ] && [ "$p" -le 498 ]; } || [ "$p" -ge 562 ]; then psm=6; else psm=3; fi
tesseract "$WORK/img/pg-$P.png" "$WORK/ocr/$P" -l script/Latin+script/Devanagari --psm $psm \
  -c tessedit_create_tsv=1 -c tessedit_create_txt=1 >/dev/null 2>&1
