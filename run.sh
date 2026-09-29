#!/usr/bin/env bash
# Cross-platform launcher for the Typing Test project.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

show_help() {
  cat <<'EOF'
Typing Test launcher

Usage:
  ./run.sh [command] [options]

With no command, a guided setup asks for each test option step by step.

Commands:
  terminal [--time SECONDS|unlimited | --words COUNT|unlimited]
           [--content words|numbers|punctuation|mixed] [--capitalization lower|capitalized|random]
           [--custom-text "TEXT"]
      Start the interactive terminal typing test. Default: 60 seconds.
      Esc or Ctrl+C saves current progress and exits. Enter inserts a newline.
      Examples: ./run.sh terminal --time 30 --content mixed --capitalization random
                ./run.sh terminal --words unlimited --content numbers
                ./run.sh terminal --custom-text $'First line\nSecond line'

  history
      Show saved terminal WPM and accuracy graphs plus recent results.

  web [PORT]
      Serve the browser typing test at http://localhost:PORT.
      Default port: 8000. Stop the server with Ctrl+C.
      Example: ./run.sh web 8080

  help, --help, -h
      Show this help text.

The browser test contains normal words, numbers, punctuation, mixed content,
capitalization, custom text, unlimited modes, live WPM graphs, and browser
history. Terminal results are saved in data/typing_results.json.
EOF
}

command="${1:---setup}"
case "$command" in
  --setup)
    exec python3 typing_test.py --setup
    ;;
  terminal)
    shift || true
    exec python3 typing_test.py "$@"
    ;;
  history)
    exec python3 typing_test.py --history
    ;;
  web)
    shift || true
    port="${1:-8000}"
    if ! [[ "$port" =~ ^[0-9]+$ ]] || (( port < 1 || port > 65535 )); then
      echo "Port must be a number from 1 to 65535." >&2
      exit 2
    fi
    echo "Browser test: http://localhost:$port"
    echo "Press Ctrl+C to stop the web server."
    exec python3 -m http.server "$port" --directory web
    ;;
  help|--help|-h)
    show_help
    ;;
  *)
    echo "Unknown command: $command" >&2
    echo >&2
    show_help >&2
    exit 2
    ;;
esac
