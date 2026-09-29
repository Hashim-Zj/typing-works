# Typing Test

A local typing-practice application with a full terminal interface and a browser
interface. Both show live net WPM, gross WPM, accuracy, error rate, progress, error
count, and WPM graphs.

Everything runs offline. The terminal test uses Python's bundled `curses`; the
browser test is a single self-contained HTML file with no third-party library and
no network calls.

## Features

- **Two interfaces** — a full-screen terminal test (curses) and a browser test.
- **Two test modes** — timed (seconds) or fixed word count, both with an
  `unlimited` option that keeps generating content until you stop.
- **Five content sources** — `words`, `numbers`, `punctuation`, `mixed`, and
  `custom` text for practising exact multiline material.
- **Three capitalization modes** — `lower`, `capitalized`, `random`.
- **Live metrics** — net WPM, gross WPM, accuracy, error rate, progress bar, and
  error count, refreshed while you type.
- **WPM graphs** — a live chart during the browser test, and a sparkline of your
  last 20 terminal tests via `./run.sh history`.
- **Guided setup** — running the launcher with no command walks through each
  option step by step.
- **Offline word list** — prompts come from the bundled `words.json`, with a
  built-in fallback list if it is missing or unreadable.
- **Private history** — terminal results are saved to a local JSON file; browser
  sessions stay in that browser's `localStorage` and are never uploaded.

## Tech Stack

- **Python 3.10+** — terminal UI and metrics engine, standard library only
  (`curses`, `json`, `http.server`).
- **HTML / CSS / JavaScript** — the browser test, vanilla and dependency-free.
- **Bash** and **PowerShell** — cross-platform launchers.

There are no runtime dependencies on Linux or macOS. On Windows, `curses` is
pulled in once from `requirements.txt`.

## Installation

```bash
git clone https://github.com/Hashim-Zj/typing-works.git
cd typing-works
```

Linux and macOS need nothing further. On Windows, install the terminal UI package
once:

```powershell
python -m pip install -r requirements.txt
```

## Usage

### Launcher commands

```bash
./run.sh                # guided step-by-step setup
./run.sh terminal       # start the terminal test
./run.sh history        # saved WPM / accuracy graphs and recent results
./run.sh web [PORT]     # serve the browser test (default 8000)
./run.sh help
```

On Windows the launcher is `.\run.ps1` with identical commands.

### Terminal test

```bash
./run.sh terminal --time 30                     # timed
./run.sh terminal --words 25                    # fixed word count
./run.sh terminal --time unlimited --content mixed --capitalization random
./run.sh terminal --words 50 --content numbers
./run.sh terminal --time 60 --content punctuation --capitalization capitalized
./run.sh terminal --custom-text $'First line\nSecond line'
```

Available `content` values are `words`, `numbers`, `punctuation`, `mixed`, and
`custom`. Available `capitalization` values are `lower`, `capitalized`, and
`random`.

The timer starts on your first keystroke. Enter behaves as a normal newline key,
which is what makes exact multiline custom text practical. Press **Esc** or
**Ctrl+C** to save the current result and exit. Unlimited tests keep appending
generated content until you stop them.

### Browser test

```bash
./run.sh web
```

Open the printed address, normally <http://localhost:8000>. Use the controls to
pick timed or word-count mode (including unlimited), the content source, and
capitalization. Sessions are stored only in that browser's local storage.

The browser test is also published at
<https://hashim-zj.github.io/typing-works/> — it is a single self-contained
file, so it runs straight from the page with no build step.

## Project Structure

```text
typing-works/
├── src/
│   ├── __init__.py
│   └── typing_test.py    # metrics engine (Session) and terminal UI
├── web/
│   └── index.html        # self-contained browser typing application
├── data/
│   └── typing_results.json   # saved terminal history (git-ignored)
├── typing_test.py        # terminal entry point
├── words.json            # local word list for generated prompts
├── requirements.txt      # Windows only: windows-curses
├── run.sh                # Bash launcher
└── run.ps1               # PowerShell launcher
```

## Configuration

There is no configuration file and no environment variable. Everything is
controlled through launcher arguments, and the two interfaces share nothing
except the notion of a test.

`words.json` is the only tunable data file. It may be a JSON list of words or an
object with a `words` key; entries are lowercased, filtered to alphabetic words
of 2–14 characters, and de-duplicated. If the file is missing or unusable the
built-in fallback list is used instead.

## Development

```bash
# Terminal test
./run.sh terminal --time 30

# Browser test on a different port
./run.sh web 8080

# Inspect saved terminal history
./run.sh history
```

The metrics engine lives in `Session` in `src/typing_test.py` and is
UI-independent: `elapsed`, `mismatches`, `correct_chars`, `accuracy`,
`error_rate`, `gross_wpm`, `net_wpm`, `progress`, and `result` are all computed
there, so the terminal renderer and the metrics can be tested separately.

The browser test is intentionally a single file. Keeping it self-contained is
what lets it be served by `python -m http.server` locally and published to
GitHub Pages without a build step.

## License

No license file is present yet. Add one before distributing this code.
