#!/usr/bin/env python3
"""
section_grid.py

given length, tempo, meter, ostinato cycle length, and a recursive structure
pattern, output a bar grid with timestamps for every section node in the tree.

usage:
  python3 section_grid.py \
      --length-sec 240 --tempo 80 --meter 5/4 --ostinato-bars 4 \
      --top abacaba --sub "A=aaba,B=aabc,C=aabc"

  optional deeper levels:
      --subsub "a=alpha beta,b=alpha beta gamma"  (lowercase to greek)

output:
  a tree view followed by a flat leaf list. each entry shows the node label,
  its bar range, and its time range (m:ss to m:ss).

assumptions:
  beats per bar = numerator of meter. seconds per bar = (60 / tempo) * beats_per_bar.
  this assumes the meter denominator's note value receives the beat. the logic is
  responsible for adjusting if a compound meter wants a different beat unit.
"""

import argparse
import sys
from dataclasses import dataclass, field

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
    n, d = s.split("/")
    return int(n), int(d)


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
        # values are space-separated greek tokens
        out[k.strip()] = [t for t in v.strip().split() if t]
    return out


def build_tree(
    top: str,
    subs: dict[str, str],
    subsubs: dict[str, list[str]] | None = None,
    sub3s: dict[str, list[str]] | None = None,
) -> Node:
    """
    build the recursive tree.
    top: string of uppercase letters, e.g. "abacaba" (parsed as A B A C A B A).
    subs: mapping uppercase letter (lowercase form) to sub-pattern string of
          lowercase letters, e.g. {'A':'aaba'}.
    subsubs: mapping lowercase letter to list of greek tokens (third level).
    sub3s: mapping greek token to list of roman numeral tokens (fourth level).
    """
    root = Node(label="root", path="root")
    for top_letter in top:
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
    distribute total_bars among leaves so that:
    - each leaf is an integer number of ostinato cycles (>= 1)
    - all occurrences of the same uppercase letter at the top level have
      identical leaf bar counts (the "shape preserved" rule from the logic)
    - within an occurrence, sub-leaves get equal cycles (extras distributed
      to first leaves within the occurrence if not divisible)
    returns (actual_total_bars, mismatch) where mismatch = actual - requested.
    """
    leaves = collect_leaves(root)
    if not leaves:
        return 0, 0
    total_cycles = total_bars // ostinato_bars

    # group top-level nodes by letter and verify equal leaf counts per letter
    occurrences_by_letter: dict[str, list[Node]] = {}
    K_by_letter: dict[str, int] = {}
    for top_node in root.children:
        L = top_node.label
        leaves_here = collect_leaves(top_node)
        if L in K_by_letter and K_by_letter[L] != len(leaves_here):
            raise ValueError(
                f"shape mismatch: letter {L} has occurrences with different "
                f"leaf counts ({K_by_letter[L]} vs {len(leaves_here)}). "
                f"the 'shape preserved' rule requires equal sub-pattern shapes."
            )
        K_by_letter[L] = len(leaves_here)
        occurrences_by_letter.setdefault(L, []).append(top_node)
    N_by_letter = {L: len(v) for L, v in occurrences_by_letter.items()}

    # solve: find cycles_per_leaf[L] >= 1 (integer) such that
    # sum(N[L] * K[L] * cpl[L]) == total_cycles, or as close as possible.
    cpl: dict[str, int] = {L: 1 for L in N_by_letter}
    weight: dict[str, int] = {L: N_by_letter[L] * K_by_letter[L] for L in N_by_letter}
    current = sum(weight[L] * cpl[L] for L in cpl)
    if current > total_cycles:
        raise ValueError(
            f"not enough cycles ({total_cycles}) to give every leaf at least 1 cycle "
            f"(minimum needed: {current}). increase length, reduce ostinato cycle size, "
            f"or reduce recursion depth."
        )
    # greedy: add one cpl at a time to the letter whose weight fits without overshoot,
    # preferring smallest-weight letters for finer granularity.
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
    mismatch = current - total_cycles  # 0 if exact, negative if undershoot

    # assign bars to leaves; within an occurrence, give equal cycles to each leaf
    bar_cursor = 0
    for top_node in root.children:
        L = top_node.label
        leaves_here = collect_leaves(top_node)
        for leaf in leaves_here:
            cycles = cpl[L]
            bars = cycles * ostinato_bars
            leaf.start_bar = bar_cursor
            leaf.end_bar = bar_cursor + bars
            bar_cursor += bars

    # propagate up
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


def fmt_time(sec: float) -> str:
    m = int(sec // 60)
    s = sec - m * 60
    if abs(s - round(s)) < 1e-6:
        return f"{m}:{int(round(s)):02d}"
    return f"{m}:{s:05.2f}"


def render_tree(root: Node, sec_per_bar: float, indent: int = 0, lines: list[str] | None = None) -> list[str]:
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--length-sec", type=float, required=True)
    ap.add_argument("--tempo", type=float, required=True, help="beats per minute")
    ap.add_argument("--meter", required=True, help="e.g. 5/4 or 7/8")
    ap.add_argument("--ostinato-bars", type=int, default=4, help="number of bars per ostinato cycle")
    ap.add_argument("--top", required=True, help="top-level pattern string, e.g. abacaba")
    ap.add_argument("--sub", default="", help="sub assignments, e.g. A=aaba,B=aabc,C=aabc")
    ap.add_argument("--subsub", default="", help="third-level assignments, e.g. a=alpha beta,b=alpha beta gamma")
    ap.add_argument("--sub3", default="", help="fourth-level assignments, e.g. alpha=i ii,beta=i ii iii")
    args = ap.parse_args()

    bps, _denom = parse_meter(args.meter)
    sec_per_bar = (60.0 / args.tempo) * bps
    total_bars = round(args.length_sec / sec_per_bar)

    subs = parse_kv_csv(args.sub) if args.sub else {}
    subsubs = parse_subsub(args.subsub) if args.subsub else None
    sub3s = parse_subsub(args.sub3) if args.sub3 else None

    root = build_tree(args.top, subs, subsubs, sub3s)
    try:
        actual_bars, bar_mismatch = assign_bars(root, total_bars, args.ostinato_bars)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    print(f"# section grid")
    print()
    print(f"length: {args.length_sec} seconds · tempo: {args.tempo} bpm · meter: {args.meter}")
    print(f"seconds per bar: {sec_per_bar:.4f} · target bars: {total_bars} · "
          f"actual bars: {actual_bars} · ostinato cycle: {args.ostinato_bars} bars")
    if bar_mismatch != 0:
        actual_sec = actual_bars * sec_per_bar
        print(f"note: actual length is {actual_sec:.2f} seconds "
              f"({bar_mismatch:+d} bars vs target). nudge tempo to land on target.")
    print()
    print("## tree")
    print()
    for line in render_tree(root, sec_per_bar):
        print(line)
    print()
    print("## leaves")
    print()
    for line in render_leaves(root, sec_per_bar):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
