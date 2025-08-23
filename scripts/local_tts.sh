#!/bin/zsh
# Simple local TTS using macOS 'say'.
# Saves audio to data/voices as .m4a (AAC).

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_DIR="$REPO_ROOT/data/voices"
mkdir -p "$OUT_DIR"

VOICE=""

print_usage() {
  cat <<'USAGE'
Usage: scripts/local_tts.sh [-v VOICE] [text...]

Options:
  -v VOICE   macOS voice name (use `say -v ?` to list)

Examples:
  scripts/local_tts.sh "Привіт! Це локальна синтезація мовлення Atlas."
  scripts/local_tts.sh -v "Samantha" "Hello from local TTS!"
USAGE
}

while getopts ":v:h" opt; do
  case $opt in
    v) VOICE="$OPTARG" ;;
    h) print_usage; exit 0 ;;
    *) print_usage; exit 1 ;;
  esac
done
shift $((OPTIND-1))

TEXT=${*:-"Привіт! Це локальна синтезація мовлення Atlas."}

ts=$(date +%Y%m%d_%H%M%S)
outfile="$OUT_DIR/local_tts_${ts}.m4a"

if [[ -n "$VOICE" ]]; then
  say -v "$VOICE" -o "$outfile" --data-format=aac -- "$TEXT"
else
  say -o "$outfile" --data-format=aac -- "$TEXT"
fi

if [[ -f "$outfile" ]]; then
  echo "$outfile"
else
  echo "ERROR: Failed to create audio at $outfile" >&2
  exit 1
fi
