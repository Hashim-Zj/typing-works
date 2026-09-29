#!/usr/bin/env python3
"""A local typing test for the terminal.

Run ``python typing_test.py`` for a 60-second test, or use --words 25 for a
word-count test.  Results are appended to typing_results.json.
"""

from __future__ import annotations

import argparse
import curses
import json
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORDS_FILE = ROOT / "words.json"
RESULTS_FILE = ROOT / "data" / "typing_results.json"
FALLBACK_WORDS = "python typing speed keyboard accuracy practice focus coding computer program terminal progress result improve learn test".split()
PUNCTUATION = ". , ! ? ; : - ' \" ( )".split()


def load_words() -> list[str]:
    """Load clean local words; the test never needs an internet connection."""
    try:
        data = json.loads(WORDS_FILE.read_text(encoding="utf-8"))
        data = data.get("words", []) if isinstance(data, dict) else data
        words = [word.lower().strip() for word in data if isinstance(word, str)]
        words = [word for word in words if word.isalpha() and 2 <= len(word) <= 14]
        if words:
            return list(dict.fromkeys(words))
    except (OSError, json.JSONDecodeError):
        pass
    return FALLBACK_WORDS


def make_prompt(word_count: int, content: str = "words", capitalization: str = "lower", custom_text: str = "") -> str:
    """Build a Monkeytype-style prompt without requiring an online service."""
    if content == "custom":
        return custom_text
    words = load_words()
    tokens: list[str] = []
    for _ in range(word_count):
        kind = random.choice(("words", "numbers", "punctuation")) if content == "mixed" else content
        if kind == "numbers":
            token = str(random.randint(0, 9999))
        elif kind == "punctuation":
            token = random.choice(words) + random.choice(PUNCTUATION)
        else:
            token = random.choice(words)
        if capitalization == "capitalized":
            token = token[:1].upper() + token[1:]
        elif capitalization == "random" and random.choice((True, False)):
            token = token[:1].upper() + token[1:]
        tokens.append(token)
    return " ".join(tokens)


@dataclass
class Session:
    prompt: str
    mode: str
    limit: int | None
    content: str = "words"
    capitalization: str = "lower"
    custom_text: str = ""
    typed: str = ""
    started_at: float | None = None
    samples: list[float] = field(default_factory=list)

    def elapsed(self, now: float | None = None) -> float:
        if self.started_at is None:
            return 0.0
        return max(0.0, (now or time.monotonic()) - self.started_at)

    def mismatches(self) -> int:
        return sum(a != b for a, b in zip(self.typed, self.prompt)) + max(0, len(self.typed) - len(self.prompt))

    def correct_chars(self) -> int:
        return sum(a == b for a, b in zip(self.typed, self.prompt))

    def accuracy(self) -> float:
        return 100.0 if not self.typed else (self.correct_chars() / len(self.typed)) * 100

    def error_rate(self) -> float:
        return 0.0 if not self.typed else (self.mismatches() / len(self.typed)) * 100

    def gross_wpm(self, now: float | None = None) -> float:
        seconds = self.elapsed(now)
        return 0.0 if seconds <= 0 else len(self.typed) / 5 / (seconds / 60)

    def net_wpm(self, now: float | None = None) -> float:
        seconds = self.elapsed(now)
        return 0.0 if seconds <= 0 else self.correct_chars() / 5 / (seconds / 60)

    def progress(self) -> float | None:
        if self.limit is None and self.content != "custom":
            return None
        return min(100.0, len(self.typed) / len(self.prompt) * 100)

    def done(self, now: float) -> bool:
        time_finished = self.mode == "time" and self.limit is not None and self.started_at is not None and self.elapsed(now) >= self.limit
        prompt_finished = self.content == "custom" and len(self.typed) >= len(self.prompt)
        words_finished = self.mode == "words" and self.limit is not None and len(self.typed) >= len(self.prompt)
        return time_finished or prompt_finished or words_finished

    def result(self) -> dict:
        ended = time.monotonic()
        duration = self.elapsed(ended)
        stamp = datetime.now()
        return {
            "timestamp": stamp.isoformat(timespec="seconds"),
            "date": stamp.date().isoformat(),
            "time": stamp.strftime("%H:%M:%S"),
            "mode": self.mode,
            "target_words": self.limit if self.mode == "words" else None,
            "content": self.content,
            "capitalization": self.capitalization,
            "duration_seconds": round(duration, 2),
            "total_time_sec": round(duration, 2),  # compatible with old preview data
            "typed_characters": len(self.typed),
            "correct_characters": self.correct_chars(),
            "errors": self.mismatches(),
            "accuracy": round(self.accuracy(), 2),
            "average_accuracy": round(self.accuracy(), 2),
            "error_rate": round(self.error_rate(), 2),
            "wpm": round(self.net_wpm(ended), 2),
            "average_wpm": round(self.net_wpm(ended), 2),
            "gross_wpm": round(self.gross_wpm(ended), 2),
            "wpm_samples": [round(value, 2) for value in self.samples],
        }


def save_result(result: dict) -> None:
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        history = json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
        history = history if isinstance(history, list) else []
    except (OSError, json.JSONDecodeError):
        history = []
    history.append(result)
    RESULTS_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")


def add_text(stdscr: curses.window, y: int, x: int, text: str, attr: int = 0) -> None:
    height, width = stdscr.getmaxyx()
    if 0 <= y < height and x < width:
        try:
            stdscr.addnstr(y, max(0, x), text, max(0, width - x - 1), attr)
        except curses.error:
            pass


def render(stdscr: curses.window, session: Session, now: float) -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    elapsed = session.elapsed(now)
    remaining = max(0.0, session.limit - elapsed) if session.mode == "time" and session.limit is not None and session.started_at else 0.0
    title = " TYPING TEST "
    add_text(stdscr, 0, max(0, (width - len(title)) // 2), title, curses.A_BOLD | curses.color_pair(4))
    limit_text = "unlimited" if session.limit is None else str(session.limit)
    mode_text = f"{limit_text}s countdown" if session.mode == "time" else f"{limit_text} words"
    add_text(stdscr, 2, 2, f"Mode: {mode_text} | {session.content} | {session.capitalization}    Esc/Ctrl+C: save & exit", curses.color_pair(4))
    time_text = f"Time left: {remaining:05.1f}s" if session.mode == "time" and session.limit is not None else f"Elapsed: {elapsed:05.1f}s"
    add_text(stdscr, 4, 2, f"{time_text}   WPM: {session.net_wpm(now):5.1f}   Accuracy: {session.accuracy():5.1f}%   Error rate: {session.error_rate():4.1f}%")
    bar_width = max(10, width - 4)
    progress = session.progress()
    filled = round(bar_width * progress / 100) if progress is not None else 0
    add_text(stdscr, 6, 2, "[" + "=" * filled + " " * (bar_width - filled) + "]", curses.color_pair(2))
    progress_text = "unlimited" if progress is None else f"{progress:5.1f}%"
    add_text(stdscr, 7, 2, f"Progress: {progress_text}  |  {len(session.typed)}/{len(session.prompt)} characters  |  Errors: {session.mismatches()}")
    add_text(stdscr, 9, 2, "Type the text below. Green is correct; red is a current mismatch.", curses.color_pair(4))

    # Keep the cursor in view and draw the prompt in rows under the dashboard.
    usable = max(20, width - 4)
    start = max(0, (len(session.typed) // usable - 2) * usable)
    start -= start % usable
    visible = session.prompt[start : start + usable * max(1, height - 15)]
    for offset, char in enumerate(visible):
        index = start + offset
        y, x = 11 + offset // usable, 2 + offset % usable
        if char == "\n":
            continue
        if index < len(session.typed):
            attr = curses.color_pair(2) if session.typed[index] == char else curses.color_pair(1) | curses.A_BOLD
        elif index == len(session.typed):
            attr = curses.color_pair(3) | curses.A_UNDERLINE
        else:
            attr = curses.color_pair(4)
        add_text(stdscr, y, x, char, attr)

    graph_y = max(12, height - 3)
    if session.samples:
        values = session.samples[-min(40, width - 16):]
        maximum = max(1.0, max(values))
        blocks = "▁▂▃▄▅▆▇█"
        spark = "".join(blocks[min(7, int(value / maximum * 7))] for value in values)
        add_text(stdscr, graph_y, 2, f"Live WPM: {spark}  ({values[-1]:.1f})", curses.color_pair(3))
    add_text(stdscr, height - 1, 2, "Timer starts with your first character.", curses.color_pair(4))
    stdscr.refresh()


def run_ui(stdscr: curses.window, mode: str, limit: int | None, content: str, capitalization: str, custom_text: str) -> dict | None:
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_CYAN, -1)
    curses.init_pair(4, curses.COLOR_WHITE, -1)
    stdscr.timeout(100)
    word_count = limit if mode == "words" and limit is not None else 180
    session = Session(make_prompt(word_count, content, capitalization, custom_text), mode, limit, content, capitalization, custom_text)
    last_sample_second = -1
    try:
        while True:
            now = time.monotonic()
            if session.done(now):
                return session.result()
            if session.limit is None and session.content != "custom" and len(session.typed) >= len(session.prompt) - 50:
                session.prompt += " " + make_prompt(80, session.content, session.capitalization)
            if session.started_at is not None and int(session.elapsed(now)) != last_sample_second:
                last_sample_second = int(session.elapsed(now))
                session.samples.append(session.net_wpm(now))
            render(stdscr, session, now)
            try:
                key = stdscr.get_wch()
            except curses.error:
                continue
            if key in ("\x1b", "\x03"):
                return session.result() if session.started_at is not None else None
            if key in ("\n", "\r"):
                key = "\n"  # Enter stays a normal newline character.
            if key in ("\b", "\x7f") or key == curses.KEY_BACKSPACE:
                session.typed = session.typed[:-1]
                continue
            if isinstance(key, str) and (key.isprintable() or key == "\n") and len(session.typed) < len(session.prompt):
                if session.started_at is None:
                    session.started_at = time.monotonic()
                session.typed += key
    except KeyboardInterrupt:
        return session.result() if session.started_at is not None else None


def sparkline(values: list[float], width: int = 48) -> str:
    if not values:
        return "(no data)"
    values = values[-width:]
    top = max(1.0, max(values))
    blocks = "▁▂▃▄▅▆▇█"
    return "".join(blocks[min(7, int(value / top * 7))] for value in values)


def show_history() -> None:
    try:
        data = json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = []
    if not data:
        print("No saved test results yet.")
        return
    data = data[-20:]
    wpms = [float(item.get("wpm", item.get("average_wpm", 0))) for item in data]
    accuracies = [float(item.get("accuracy", item.get("average_accuracy", 0))) for item in data]
    print("\nTyping history (last 20 tests)")
    print(f"WPM      {sparkline(wpms)}  max {max(wpms):.1f}, avg {sum(wpms) / len(wpms):.1f}")
    print(f"Accuracy {sparkline(accuracies)}  max {max(accuracies):.1f}%, avg {sum(accuracies) / len(accuracies):.1f}%")
    print("\n  Date       Time      WPM    Accuracy   Errors")
    for item, wpm, accuracy in zip(data, wpms, accuracies):
        print(f"  {item.get('date', '-'):<10} {item.get('time', '-'):<8} {wpm:>6.1f}   {accuracy:>6.1f}%   {item.get('errors', item.get('wrong_words', 0)):>4}")


def choose(prompt: str, options: list[tuple[str, str]]) -> str:
    """Prompt until a numbered setup choice is selected."""
    print(f"\n{prompt}")
    for number, label in options:
        print(f"  {number}. {label}")
    valid = {number: value for number, value in options}
    while True:
        answer = input("Choose an option: ").strip()
        if answer in valid:
            return valid[answer]
        print("Please enter one of the listed numbers.")


def interactive_setup() -> tuple[str, int | None, str, str, str]:
    """Collect a complete test configuration for `run.sh` with no arguments."""
    print("\nTyping Test setup — press Ctrl+C before the test starts to cancel.")
    mode = choose("Step 1 of 4: choose a test mode", [("1", "time"), ("2", "words")])
    limit_label = "seconds" if mode == "time" else "words"
    limit_options = [("1", "15"), ("2", "30"), ("3", "60"), ("4", "120")] if mode == "time" else [("1", "10"), ("2", "25"), ("3", "50"), ("4", "100")]
    limit = choose(f"Step 2 of 4: choose {limit_label}", limit_options + [("5", "unlimited"), ("6", "custom")])
    if limit == "custom":
        while True:
            raw = input(f"Enter a positive number of {limit_label}: ").strip()
            if raw.isdigit() and int(raw) > 0:
                limit = raw
                break
            print("Enter a positive whole number.")
    content = choose(
        "Step 3 of 4: choose content",
        [("1", "words"), ("2", "numbers"), ("3", "punctuation"), ("4", "mixed"), ("5", "custom")],
    )
    capitalization = "lower"
    custom_text = ""
    if content == "custom":
        print("Step 4 of 4: enter custom text. Finish by entering a line containing only END.")
        lines: list[str] = []
        while True:
            line = input()
            if line == "END":
                break
            lines.append(line)
        custom_text = "\n".join(lines)
        if not custom_text:
            print("No custom text entered; using normal words.")
            content = "words"
    else:
        capitalization = choose(
            "Step 4 of 4: choose capitalization",
            [("1", "lower"), ("2", "capitalized"), ("3", "random")],
        )
    return mode, None if limit == "unlimited" else int(limit), content, capitalization, custom_text


def main() -> None:
    parser = argparse.ArgumentParser(description="A real-time terminal typing test")
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("--time", metavar="SECONDS|unlimited", default="60", help="countdown test length, or unlimited (default: 60)")
    choice.add_argument("--words", metavar="COUNT|unlimited", help="finish after this many words, or unlimited")
    parser.add_argument("--content", choices=("words", "numbers", "punctuation", "mixed", "custom"), default="words", help="prompt content type")
    parser.add_argument("--capitalization", choices=("lower", "capitalized", "random"), default="lower", help="letter casing for generated prompts")
    parser.add_argument("--custom-text", help="text to type; supports new lines entered with Enter")
    parser.add_argument("--setup", action="store_true", help="open the guided test setup")
    parser.add_argument("--history", action="store_true", help="show saved terminal performance graph")
    args = parser.parse_args()
    if args.history:
        show_history()
        return
    try:
        if args.setup:
            mode, limit, args.content, args.capitalization, custom_text = interactive_setup()
        else:
            mode, raw_limit = ("words", args.words) if args.words is not None else ("time", args.time)
            if raw_limit == "unlimited":
                limit = None
            else:
                try:
                    limit = int(raw_limit)
                except ValueError:
                    parser.error("test length must be a positive number or 'unlimited'")
                if limit < 1:
                    parser.error("test length must be at least 1")
            custom_text = args.custom_text or ""
            if args.custom_text is not None:
                args.content = "custom"
            if args.content == "custom" and not args.custom_text:
                parser.error("--content custom needs --custom-text 'your text'")
    except KeyboardInterrupt:
        print("\nSetup cancelled.")
        return
    try:
        result = curses.wrapper(run_ui, mode, limit, args.content, args.capitalization, custom_text)
    except curses.error as error:
        raise SystemExit(f"Your terminal does not support the interactive UI: {error}") from error
    if result is None:
        print("\nTest ended before typing began; no result was saved.")
        return
    save_result(result)
    print("\nResult saved")
    print(f"Net WPM: {result['wpm']:.1f} | Gross WPM: {result['gross_wpm']:.1f} | Accuracy: {result['accuracy']:.1f}% | Error rate: {result['error_rate']:.1f}%")
    print(f"Characters: {result['correct_characters']}/{result['typed_characters']} correct | Errors: {result['errors']} | Time: {result['duration_seconds']:.1f}s")
    if result["wpm_samples"]:
        print("Live WPM graph: " + sparkline(result["wpm_samples"]))


if __name__ == "__main__":
    main()
