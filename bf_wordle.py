#!/usr/bin/env python3
"""
Find the best Wordle starting word by scoring every candidate against all
past answers. Score = sum over all answers of (green_pts * greens + yellow_pts * yellows).
Default: green=2, yellow=1.
"""

import argparse
from pathlib import Path


def get_feedback(guess: str, answer: str) -> list[str]:
    """
    Wordle feedback: G = green (right letter, right place),
    Y = yellow (letter in word, wrong place), '-' = grey.
    Each letter in the answer is matched at most once (greens first, then yellows).
    """
    guess = guess.lower().strip()
    answer = answer.lower().strip()
    n = len(guess)
    if len(answer) != n:
        raise ValueError("guess and answer must be same length")
    result = [""] * n
    # Count occurrences of each letter in the answer (available to match)
    answer_counts: dict[str, int] = {}
    for c in answer:
        answer_counts[c] = answer_counts.get(c, 0) + 1
    used = {c: 0 for c in answer_counts}

    # First pass: greens
    for i in range(n):
        if guess[i] == answer[i]:
            result[i] = "G"
            used[guess[i]] += 1

    # Second pass: yellows (remaining occurrences in answer)
    for i in range(n):
        if result[i]:
            continue
        c = guess[i]
        if c in answer_counts and used[c] < answer_counts[c]:
            result[i] = "Y"
            used[c] += 1
        else:
            result[i] = "-"

    return result


def score_feedback(
    feedback: list[str],
    green_pts: int = 2,
    yellow_pts: int = 1,
) -> int:
    return sum(
        green_pts if f == "G" else (yellow_pts if f == "Y" else 0)
        for f in feedback
    )


def load_words(path: Path) -> list[str]:
    words = []
    with open(path) as f:
        for line in f:
            w = line.strip().lower()
            if len(w) == 5 and w.isalpha():
                words.append(w)
    return words


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find best Wordle starting word by brute-force scoring."
    )
    parser.add_argument(
        "answers_file",
        nargs="?",
        default=Path(__file__).parent / "wordle_answers.txt",
        type=Path,
        help="Path to file with one 5-letter answer per line",
    )
    parser.add_argument(
        "-g",
        "--green",
        type=int,
        default=2,
        help="Points per green (default: 2)",
    )
    parser.add_argument(
        "-y",
        "--yellow",
        type=int,
        default=1,
        help="Points per yellow (default: 1)",
    )
    parser.add_argument(
        "-n",
        "--top",
        type=int,
        default=20,
        help="Show top N words (default: 20)",
    )
    parser.add_argument(
        "--candidates",
        type=Path,
        default=None,
        help="Candidate words file (default: use same as answers)",
    )
    args = parser.parse_args()

    if not args.answers_file.exists():
        print(f"Answers file not found: {args.answers_file}")
        print("Download with: curl -sL https://raw.githubusercontent.com/georgevreilly/wordle/main/answers.txt -o wordle_answers.txt")
        raise SystemExit(1)

    answers = load_words(args.answers_file)
    candidates = load_words(args.candidates or args.answers_file)
    print(f"Loaded {len(answers)} answers, {len(candidates)} candidates")
    print(f"Scoring: green={args.green}, yellow={args.yellow}\n")

    scores: list[tuple[str, int]] = []
    for i, word in enumerate(candidates):
        total = sum(
            score_feedback(
                get_feedback(word, ans),
                green_pts=args.green,
                yellow_pts=args.yellow,
            )
            for ans in answers
        )
        scores.append((word, total))
        if (i + 1) % 500 == 0:
            print(f"  ... {i + 1}/{len(candidates)}", flush=True)

    scores.sort(key=lambda x: -x[1])

    print(f"Top {args.top} starting words (by total points over all answers):\n")
    for rank, (word, total) in enumerate(scores[: args.top], 1):
        avg = total / len(answers)
        print(f"  {rank:3}. {word}  total={total:,}  avg={avg:.2f}")


if __name__ == "__main__":
    main()
