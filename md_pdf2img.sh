#!/usr/bin/env bash
set -euo pipefail

fmt="png"
dpi="200"
inplace="0"
insert="1"

print_help() {
  cat <<'EOF'
Nutzung
  md_pdf2img.sh DATEI.md

Schalter
  --inplace        Markdown Datei direkt ändern
  --format png     Ausgabeformat
  --format jpg     Ausgabeformat, braucht imagemagick
  --dpi 200        Raster DPI für pdftoppm
  --no-insert      Keine neuen Bildzeilen einfügen

Beispiel
  ./md_pdf2img.sh --inplace --format png --dpi 250 kolloquium.md
EOF
}

if [[ $# -lt 1 ]]; then
  print_help
  exit 2
fi

md=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --format)
      fmt="${2:-}"
      shift 2
      ;;
    --dpi)
      dpi="${2:-}"
      shift 2
      ;;
    --inplace)
      inplace="1"
      shift
      ;;
    --no-insert)
      insert="0"
      shift
      ;;
    -h|--help)
      print_help
      exit 0
      ;;
    *)
      md="$1"
      shift
      ;;
  esac
done

if [[ -z "$md" ]]; then
  echo "Fehler keine Markdown Datei angegeben" >&2
  exit 2
fi

if [[ ! -f "$md" ]]; then
  echo "Fehler Datei nicht gefunden $md" >&2
  exit 2
fi

if ! command -v pdftoppm >/dev/null 2>&1; then
  echo "Fehler pdftoppm fehlt, Paket poppler installieren" >&2
  exit 2
fi

if ! command -v gawk >/dev/null 2>&1; then
  echo "Fehler gawk fehlt, Paket gawk installieren" >&2
  exit 2
fi

fmt_lc="$(printf '%s' "$fmt" | tr 'A-Z' 'a-z')"
if [[ "$fmt_lc" == "jpeg" ]]; then
  fmt_lc="jpg"
fi

if [[ "$fmt_lc" != "png" && "$fmt_lc" != "jpg" ]]; then
  echo "Fehler Format nur png oder jpg" >&2
  exit 2
fi

if [[ "$fmt_lc" == "jpg" ]]; then
  if ! command -v magick >/dev/null 2>&1; then
    echo "Fehler magick fehlt, Paket imagemagick installieren oder png nutzen" >&2
    exit 2
  fi
fi

md_dir="$(cd "$(dirname "$md")" && pwd)"
tmp_list="$(mktemp)"
tmp_out="$(mktemp)"

cleanup() {
  rm -f "$tmp_list" "$tmp_out"
}
trap cleanup EXIT

gawk '
{
  line=$0
  while (match(line, /src="[^"]+\.pdf"/)) {
    p=substr(line, RSTART+5, RLENGTH-6)
    print p
    line=substr(line, RSTART+RLENGTH)
  }

  line=$0
  while (match(line, /`[^`]+\.pdf`/)) {
    p=substr(line, RSTART+1, RLENGTH-2)
    print p
    line=substr(line, RSTART+RLENGTH)
  }

  line=$0
  while (match(line, /\([^)]+\.pdf\)/)) {
    p=substr(line, RSTART+1, RLENGTH-2)
    print p
    line=substr(line, RSTART+RLENGTH)
  }
}
' "$md" | sort -u > "$tmp_list"

while IFS= read -r rel; do
  [[ -z "$rel" ]] && continue

  if [[ "$rel" = /* ]]; then
    pdf="$rel"
  else
    pdf="$md_dir/$rel"
  fi

  if [[ ! -f "$pdf" ]]; then
    echo "Hinweis PDF fehlt $pdf" >&2
    continue
  fi

  base="${pdf%.pdf}"

  if [[ "$fmt_lc" == "png" ]]; then
    pdftoppm -r "$dpi" -png -f 1 -l 1 -singlefile "$pdf" "$base" >/dev/null
  else
    pdftoppm -r "$dpi" -png -f 1 -l 1 -singlefile "$pdf" "$base" >/dev/null
    magick "${base}.png" "${base}.jpg"
    rm -f "${base}.png"
  fi
done < "$tmp_list"

gawk -v fmt="$fmt_lc" -v do_insert="$insert" '
function print_img(path,    img) {
  img = path
  sub(/\.pdf$/, "." fmt, img)
  print ""
  print "![](" img ")"
}
{
  orig=$0
  line=$0

  line = gensub(/src="([^"]+)\.pdf"/, "src=\"\\1." fmt "\"", "g", line)
  print line

  if (do_insert == "1") {
    tmp=orig
    while (match(tmp, /src="[^"]+\.pdf"/)) {
      p=substr(tmp, RSTART+5, RLENGTH-6)
      done[p]=1
      tmp=substr(tmp, RSTART+RLENGTH)
    }

    tmp=orig
    while (match(tmp, /`[^`]+\.pdf`/)) {
      p=substr(tmp, RSTART+1, RLENGTH-2)
      if (!(p in done)) {
        print_img(p)
        done[p]=1
      }
      tmp=substr(tmp, RSTART+RLENGTH)
    }

    tmp=orig
    while (match(tmp, /\([^)]+\.pdf\)/)) {
      p=substr(tmp, RSTART+1, RLENGTH-2)
      if (!(p in done)) {
        print_img(p)
        done[p]=1
      }
      tmp=substr(tmp, RSTART+RLENGTH)
    }
  }
}
' "$md" > "$tmp_out"

if [[ "$inplace" == "1" ]]; then
  cp "$tmp_out" "$md"
  echo "Fertig Markdown aktualisiert $md"
else
  out_md="${md%.md}_img.md"
  cp "$tmp_out" "$out_md"
  echo "Fertig neue Datei $out_md"
fi