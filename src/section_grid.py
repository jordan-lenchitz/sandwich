#!/usr/bin/env python3
"""
section_grid.py

input length, tempo, meter, ostinato cycle length, and a recursive structure pattern
output a bar grid with timestamps for every section node in the tree
"""

import argparse
import sys
from dataclasses import dataclass, field
from typing import Optional
from core import format_duration as fmt_time

GREEK_LOWER = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta"]
ROMAN_NUMERALS = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii"]


@dataclass
class Node:
    label: str          # display label, e.g. "A", "a", "alpha", "i"
    path: str           # full path from root, e.g. "A.a.alpha"
    children: list = field(default_factory=list)
    start_bar: int = 0
    end_bar: int = 0    # exclusive

    def is_leaf(self) -> bool:
        return not self.children


def parse_meter(s: str) -> tuple[int, int]:
    if "/" not in s:
        raise ValueError(f"bad meter (expected N/D, e.g. 4/4): {s!r}")
    n, d = s.split("/", 1)
    num, den = int(n), int(d)
    if num <= 0 or den <= 0:
        raise ValueError(f"meter values must be positive: {s!r}")
    return num, den


def parse_kv_csv(s: str) -> dict[str, str]:
    """parse 'A=aaba,B=aabc' into {'A': 'aaba', 'B': 'aabc'}."""
    out: dict[str, str] = {}
    for chunk in s.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" not in chunk:
            raise ValueError(f"bad assignment: {chunk!r}")
        k, v = chunk.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def parse_subsub(s: str) -> dict[str, list[str]]:
    """parse 'a=alpha beta,b=alpha beta gamma' into {'a': ['alpha','beta'], ...}"""
    out: dict[str, list[str]] = {}
    for chunk in s.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" not in chunk:
            raise ValueError(f"bad assignment: {chunk!r}")
        k, v = chunk.split("=", 1)
        out[k.strip()] = [t for t in v.strip().split() if t]
    return out


def build_tree(
    top: str,
    subs: dict[str, str],
    subsubs: Optional[dict[str, list[str]]] = None,
    sub3s: Optional[dict[str, list[str]]] = None,
) -> Node:
    """
    build the recursive tree.
    """
    root = Node(label="root", path="root")
    for top_letter in top:
        if not top_letter.strip():
            continue
        upper = top_letter.upper()
        node = Node(label=upper, path=f"{upper}")
        sub_pattern = subs.get(upper) or subs.get(top_letter)
        if sub_pattern:
            for sub_letter in sub_pattern:
                lower = sub_letter.lower()
                sub_node = Node(label=lower, path=f"{node.path}.{lower}")
                if subsubs and lower in subsubs:
                    for greek in subsubs[lower]:
                        greek_node = Node(label=greek, path=f"{sub_node.path}.{greek}")
                        if sub3s and greek in sub3s:
                            for rn in sub3s[greek]:
                                greek_node.children.append(
                                    Node(label=rn, path=f"{greek_node.path}.{rn}")
                                )
                        sub_node.children.append(greek_node)
                node.children.append(sub_node)
        root.children.append(node)
    return root


def collect_leaves(node: Node) -> list[Node]:
    if node.is_leaf():
        return [node]
    out: list[Node] = []
    for c in node.children:
        out.extend(collect_leaves(c))
    return out


def assign_bars(root: Node, total_bars: int, ostinato_bars: int) -> tuple[int, int]:
    """
    distribute total_bars among leaves while preserving identical leaf counts/durations
    for identical top-level section letters.
    """
    if ostinato_bars <= 0:
        raise ValueError("ostinato_bars must be positive")
    leaves = collect_leaves(root)
    if not leaves or root.is_leaf():
        return 0, 0
    total_cycles = total_bars // ostinato_bars

    occurrences_by_letter: dict[str, list[Node]] = {}
    K_by_letter: dict[str, int] = {}
    for top_node in root.children:
        L = top_node.label
        leaves_here = collect_leaves(top_node)
        if L in K_by_letter and K_by_letter[L] != len(leaves_here):
            raise ValueError(
                f"shape mismatch: letter {L} has occurrences with different "
                f"leaf counts ({K_by_letter[L]} vs {len(leaves_here)}). "
            )
        K_by_letter[L] = len(leaves_here)
        occurrences_by_letter.setdefault(L, []).append(top_node)
    N_by_letter = {L: len(v) for L, v in occurrences_by_letter.items()}

    cpl: dict[str, int] = {L: 1 for L in N_by_letter}
    weight: dict[str, int] = {L: N_by_letter[L] * K_by_letter[L] for L in N_by_letter}
    min_cycles_needed = sum(weight[L] * cpl[L] for L in cpl)

    # If the default/requested ostinato_bars is too large to fit min_cycles_needed into total_bars,
    # step down ostinato_bars (e.g. 4 -> 2 -> 1) so the structure fits the requested length.
    effective_ostinato = ostinato_bars
    while effective_ostinato > 1 and (total_bars // effective_ostinato) < min_cycles_needed:
        effective_ostinato -= 1
    total_cycles = total_bars // effective_ostinato
    current = min_cycles_needed

    sorted_letters = sorted(weight, key=lambda L: weight[L])
    while current < total_cycles:
        added = False
        for L in sorted_letters:
            if current + weight[L] <= total_cycles:
                cpl[L] += 1
                current += weight[L]
                added = True
                break
        if not added:
            break

    bar_cursor = 0
    for top_node in root.children:
        L = top_node.label
        leaves_here = collect_leaves(top_node)
        for leaf in leaves_here:
            cycles = cpl[L]
            bars = cycles * effective_ostinato
            leaf.start_bar = bar_cursor
            leaf.end_bar = bar_cursor + bars
            bar_cursor += bars

    def propagate(n: Node) -> tuple[int, int]:
        if n.is_leaf():
            return n.start_bar, n.end_bar
        starts, ends = [], []
        for c in n.children:
            s, e = propagate(c)
            starts.append(s)
            ends.append(e)
        n.start_bar = min(starts)
        n.end_bar = max(ends)
        return n.start_bar, n.end_bar

    propagate(root)

    actual_total_bars = bar_cursor
    bar_mismatch = actual_total_bars - total_bars
    return actual_total_bars, bar_mismatch


def bar_to_seconds(bar: int, sec_per_bar: float) -> float:
    return bar * sec_per_bar


def render_tree(root: Node, sec_per_bar: float, indent: int = 0, lines: Optional[list[str]] = None) -> list[str]:
    if lines is None:
        lines = []
    if root.label != "root":
        prefix = "  " * indent
        t1 = fmt_time(bar_to_seconds(root.start_bar, sec_per_bar))
        t2 = fmt_time(bar_to_seconds(root.end_bar, sec_per_bar))
        bar_range = f"bars {root.start_bar + 1} to {root.end_bar}"
        lines.append(f"{prefix}{root.label} ({bar_range}, {t1} to {t2})")
    for c in root.children:
        next_indent = indent if root.label == "root" else indent + 1
        render_tree(c, sec_per_bar, next_indent, lines)
    return lines


def render_leaves(root: Node, sec_per_bar: float) -> list[str]:
    leaves = collect_leaves(root)
    out = ["| leaf path | bars | time |", "|---|---|---|"]
    for n in leaves:
        if n.label == "root":
            continue
        t1 = fmt_time(bar_to_seconds(n.start_bar, sec_per_bar))
        t2 = fmt_time(bar_to_seconds(n.end_bar, sec_per_bar))
        bar_range = f"{n.start_bar + 1} to {n.end_bar}"
        out.append(f"| {n.path} | {bar_range} | {t1} to {t2} |")
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--length-sec", type=float, required=True)
    ap.add_argument("--tempo", type=float, required=True)
    ap.add_argument("--meter", required=True)
    ap.add_argument("--ostinato-bars", type=int, default=4)
    ap.add_argument("--top", required=True)
    ap.add_argument("--sub", default="")
    ap.add_argument("--subsub", default="")
    ap.add_argument("--sub3", default="")
    return ap


def run_from_args(args: argparse.Namespace) -> int:
    try:
        if args.tempo <= 0 or args.length_sec <= 0:
            raise ValueError("tempo and length-sec must be positive")
        bps, denom = parse_meter(args.meter)
        # Account for denominator relative to quarter note (tempo in BPM = quarter notes per minute)
        sec_per_bar = (60.0 / args.tempo) * bps * (4.0 / denom)
        total_bars = round(args.length_sec / sec_per_bar)

        subs = parse_kv_csv(args.sub) if args.sub else {}
        subsubs = parse_subsub(args.subsub) if args.subsub else None
        sub3s = parse_subsub(args.sub3) if args.sub3 else None

        root = build_tree(args.top, subs, subsubs, sub3s)
        actual_bars, bar_mismatch = assign_bars(root, total_bars, args.ostinato_bars)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    actual_dur = fmt_time(bar_to_seconds(actual_bars, sec_per_bar))
    target_dur = fmt_time(args.length_sec)
    print("# section grid")
    print(f"target bars: {total_bars} ({target_dur}) | actual bars: {actual_bars} ({actual_dur}) | delta: {bar_mismatch:+d} bars")
    print()
    print("## tree")
    for line in render_tree(root, sec_per_bar):
        print(line)
    print()
    print("## leaf breakdown")
    for line in render_leaves(root, sec_per_bar):
        print(line)
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    return run_from_args(args)


if __name__ == "__main__":
    raise SystemExit(main())
