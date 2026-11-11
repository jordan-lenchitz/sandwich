import html
import os
import re
from typing import Optional

from fastapi import FastAPI, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Environment, BaseLoader
from pydantic import BaseModel

from sandwich import ALLOWED_SUBCOMMANDS, execute_command

app = FastAPI(
    title="Sandwich 🥪 Music Theory Toolkit",
    description="A CLI-friendly music theory toolkit with an emphasis on tritone substitutions, functional voice-leading, and recursive form.",
    version="2.0.0",
)

jinja_env = Environment(loader=BaseLoader(), autoescape=True)


def _format_inline_md(text: str) -> str:
    """Escape HTML and render basic inline Markdown (**bold**, *italic*, `code`)."""
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
    return escaped


def render_markdown_to_html(md_text: str) -> str:
    """
    Lightweight pure-Python converter for the Markdown tables, headings, lists,
    and code blocks emitted by sandwich.py.
    """
    if not md_text:
        return ""

    lines = md_text.splitlines()
    out: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # Markdown pipe table detection
        if stripped.startswith("|") and stripped.endswith("|") and i + 1 < n:
            next_stripped = lines[i + 1].strip()
            if next_stripped.startswith("|") and "---" in next_stripped:
                headers = [c.strip() for c in stripped.strip("|").split("|")]
                out.append('<div class="table-wrap"><table class="md-table"><thead><tr>')
                for h in headers:
                    out.append(f"<th>{_format_inline_md(h)}</th>")
                out.append("</tr></thead><tbody>")
                i += 2
                while i < n and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                    cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                    out.append("<tr>")
                    for c in cells:
                        out.append(f"<td>{_format_inline_md(c)}</td>")
                    out.append("</tr>")
                    i += 1
                out.append("</tbody></table></div>")
                continue

        # Headings
        if stripped.startswith("## "):
            out.append(f"<h3>{_format_inline_md(stripped[3:])}</h3>")
            i += 1
            continue
        if stripped.startswith("# "):
            out.append(f"<h2>{_format_inline_md(stripped[2:])}</h2>")
            i += 1
            continue

        # Bullet list
        if stripped.startswith("- "):
            out.append('<ul class="md-list">')
            while i < n and lines[i].strip().startswith("- "):
                item_text = lines[i].strip()[2:]
                out.append(f"<li>{_format_inline_md(item_text)}</li>")
                i += 1
            out.append("</ul>")
            continue

        # Indented tree / histogram block (e.g. from section_grid or melody_parser)
        if line.startswith("  ") or (
            "(" in stripped and "bars " in stripped and " to " in stripped
        ):
            tree_lines = []
            while i < n and lines[i].strip() and not lines[i].strip().startswith("#") and not lines[i].strip().startswith("|"):
                tree_lines.append(html.escape(lines[i]))
                i += 1
            out.append(f'<pre class="tree-block">{chr(10).join(tree_lines)}</pre>')
            continue

        # Standard paragraph line
        out.append(f'<p class="md-p">{_format_inline_md(stripped)}</p>')
        i += 1

    return "\n".join(out)


EXAMPLES = [
    {
        "label": "parse melody",
        "cmd": 'parse "c4q d4e e4e f4q g4h"',
    },
    {
        "label": "recursive grid",
        "cmd": 'grid --length-sec 240 --tempo 80 --meter 4/4 --top ABACABA --sub "A=aaba,B=aabc,C=aabc"',
    },
    {
        "label": "guess key",
        "cmd": 'key "c d e f g a b"',
    },
    {
        "label": "tritone subs",
        "cmd": 'subs "c e g bb"',
    },
    {
        "label": "harmonize + smooth voicing",
        "cmd": 'harmonize "c4 d4 e4 f4 g4 a4 b4 c5" --voicing smooth',
    },
    {
        "label": "generate song",
        "cmd": 'generate "ab c eb g | ab c d f | ab c eb g | ab c db f" --form ABACA --voicing drop2 --rhythm bossa',
    },
    {
        "label": "negative harmony",
        "cmd": 'negative "c4 e4 g4 b4" --key C',
    },
    {
        "label": "modulate (kapustin)",
        "cmd": 'modulate "C major" "g# minor"',
    },
]


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>sandwich 🥪 | music theory toolkit</title>
    <style>
        :root {
            --bg: #f7f7f5;
            --card: #ffffff;
            --text: #1f2421;
            --muted: #606965;
            --accent: #2e7d32;
            --accent-hover: #1b5e20;
            --border: #e4e7e5;
            --code-bg: #161817;
            --code-fg: #e2e8f0;
            --err-bg: #fef2f2;
            --err-fg: #991b1b;
            --err-border: #f87171;
        }
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 32px 16px;
            background: var(--bg);
            color: var(--text);
            line-height: 1.5;
        }
        .container {
            max-width: 960px;
            margin: 0 auto;
            background: var(--card);
            padding: 36px;
            border-radius: 12px;
            border: 1px solid var(--border);
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 24px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 16px;
        }
        h1 {
            margin: 0;
            font-weight: 800;
            font-size: 2.2rem;
            letter-spacing: -0.02em;
        }
        .subtitle {
            color: var(--muted);
            font-size: 1.02rem;
            margin: 4px 0 0 0;
        }
        a { color: var(--accent); text-decoration: none; font-weight: 500; }
        a:hover { text-decoration: underline; }
        label.cmd-label {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            font-weight: 600;
            font-size: 0.92rem;
            color: var(--muted);
        }
        .kbd-hint {
            font-weight: 400;
            font-size: 0.8rem;
            color: #888;
            font-family: monospace;
        }
        textarea {
            width: 100%;
            height: 92px;
            padding: 14px 16px;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            border: 2px solid var(--border);
            border-radius: 8px;
            font-size: 0.98rem;
            background: #fcfcfb;
            color: var(--text);
            transition: border-color 0.15s;
            resize: vertical;
        }
        textarea:focus {
            outline: none;
            border-color: var(--accent);
            background: #fff;
        }
        .actions {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 12px;
            flex-wrap: wrap;
        }
        button {
            background: var(--accent);
            color: white;
            padding: 10px 22px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.95rem;
            font-weight: 600;
            transition: background 0.15s;
        }
        button:hover { background: var(--accent-hover); }
        button.secondary {
            background: #edf0ee;
            color: var(--text);
            font-weight: 500;
            padding: 8px 14px;
            font-size: 0.85rem;
        }
        button.secondary:hover { background: #dfe4e0; }
        .examples {
            margin-top: 24px;
            padding-top: 16px;
            border-top: 1px solid var(--border);
        }
        .examples-title {
            color: var(--muted);
            font-size: 0.82rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin: 0 0 10px 0;
        }
        .example-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .example-cmd {
            cursor: pointer;
            background: #f1f4f2;
            border: 1px solid var(--border);
            padding: 6px 12px;
            border-radius: 18px;
            font-size: 0.84rem;
            font-family: 'SFMono-Regular', Consolas, monospace;
            color: var(--text);
            transition: all 0.15s;
        }
        .example-cmd:hover {
            background: #e2ebe4;
            border-color: var(--accent);
        }
        .output-section {
            margin-top: 28px;
            padding-top: 20px;
            border-top: 2px solid var(--border);
        }
        .output-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .output-header h2 {
            margin: 0;
            font-size: 1.2rem;
        }
        .view-tabs {
            display: flex;
            gap: 6px;
        }
        .error-banner {
            background: var(--err-bg);
            color: var(--err-fg);
            border: 1px solid var(--err-border);
            padding: 14px 18px;
            border-radius: 8px;
            font-family: monospace;
            white-space: pre-wrap;
            margin-bottom: 16px;
        }
        .rendered-output {
            background: #fbfbfa;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px 24px;
        }
        .rendered-output h2 {
            margin-top: 0;
            font-size: 1.35rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 8px;
        }
        .rendered-output h3 {
            margin-top: 20px;
            margin-bottom: 8px;
            font-size: 1.08rem;
            color: var(--accent);
        }
        .md-p { margin: 6px 0; }
        .md-list { margin: 8px 0; padding-left: 20px; }
        .table-wrap { overflow-x: auto; margin: 12px 0 18px 0; }
        table.md-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.92rem;
            font-family: 'SFMono-Regular', Consolas, monospace;
        }
        table.md-table th, table.md-table td {
            text-align: left;
            padding: 8px 12px;
            border-bottom: 1px solid var(--border);
        }
        table.md-table th {
            background: #f1f4f2;
            font-weight: 700;
            color: var(--text);
        }
        table.md-table tr:hover td {
            background: #f6f9f6;
        }
        pre.raw-output, pre.tree-block {
            background: var(--code-bg);
            color: var(--code-fg);
            padding: 18px;
            border-radius: 8px;
            overflow-x: auto;
            white-space: pre-wrap;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.9rem;
            line-height: 1.5;
            margin: 0;
        }
        details.cli-ref {
            margin-top: 24px;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px 16px;
            background: #fafbfa;
        }
        details.cli-ref summary {
            cursor: pointer;
            font-weight: 600;
            font-size: 0.9rem;
            color: var(--muted);
        }
        .ref-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 12px;
            margin-top: 12px;
            font-size: 0.85rem;
        }
        .ref-card {
            background: white;
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 10px 12px;
        }
        .ref-card code {
            display: block;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>sandwich 🥪</h1>
                <p class="subtitle">a music theory <a href="https://github.com/jordan-lenchitz/sandwich" target="_blank" rel="noopener">toolkit</a> for tritone substitutions, functional voice-leading &amp; recursive form</p>
            </div>
        </header>

        <form id="cmd-form" method="post" action="/run">
            <label class="cmd-label" for="command">
                <span>command ({{ subcommands|join(', ') }})</span>
                <span class="kbd-hint">Ctrl/Cmd + Enter to run</span>
            </label>
            <textarea id="command" name="command" placeholder="subs &quot;c e g bb&quot;">{{ command }}</textarea>
            <div class="actions">
                <button type="submit">run command</button>
            </div>
        </form>

        <div class="examples">
            <div class="examples-title">presets (click to run):</div>
            <div class="example-list">
                {% for ex in examples %}
                <button type="button" class="example-cmd" data-cmd="{{ ex.cmd }}" onclick="runPreset(this.getAttribute('data-cmd'))">{{ ex.label }}</button>
                {% endfor %}
            </div>
        </div>

        {% if command %}
        <div class="output-section">
            <div class="output-header">
                <h2>output</h2>
                {% if stdout %}
                <div class="view-tabs">
                    <button type="button" class="secondary" onclick="toggleView('rendered')">formatted</button>
                    <button type="button" class="secondary" onclick="toggleView('raw')">raw markdown</button>
                    <button type="button" class="secondary" onclick="copyRaw()">copy</button>
                </div>
                {% endif %}
            </div>

            {% if stderr %}
            <div class="error-banner">{{ stderr }}</div>
            {% endif %}

            {% if stdout %}
            <div id="view-rendered" class="rendered-output">
                {{ rendered_html|safe }}
            </div>
            <pre id="view-raw" class="raw-output" style="display:none;">{{ stdout }}</pre>
            {% elif not stderr %}
            <pre class="raw-output">(No output)</pre>
            {% endif %}
        </div>
        {% endif %}

        <details class="cli-ref">
            <summary>cli command syntax reference</summary>
            <div class="ref-grid">
                <div class="ref-card">
                    <code>parse "&lt;notes&gt;" [--format text|lilypond|musicxml]</code>
                    Parse pitches with optional octave and duration tags (<code>w, h, q, e, s, t</code> or <code>:1.5</code>).
                </div>
                <div class="ref-card">
                    <code>grid --length-sec N --tempo BPM --meter N/D --top FORM [--sub ...]</code>
                    Build a recursive section bar/time grid preserving top-level section shapes.
                </div>
                <div class="ref-card">
                    <code>subs "&lt;pitches&gt;" | --root R --quality Q [--top N]</code>
                    Rank tritone substitution candidates by tritone preservation, root relation, and common tones.
                </div>
                <div class="ref-card">
                    <code>key "&lt;pitches&gt;"</code>
                    Score likely keys and modes by pitch fit, scale coverage, and tonic triad weight.
                </div>
                <div class="ref-card">
                    <code>harmonize "&lt;melody&gt;" [--voicing closed|drop2|drop3|smooth]</code>
                    Generate functional diatonic harmonizations and optional MIDI voice-leadings.
                </div>
                <div class="ref-card">
                    <code>generate "&lt;vamp&gt;" [--form ABACA] [--voicing ...] [--rhythm ...]</code>
                    Build multi-section progressions from a vamp using 13 pure-Python harmonic inference rules.
                </div>
                <div class="ref-card">
                    <code>negative "&lt;pitches_or_melody&gt;" --key ROOT</code>
                    Reflect pitches or melodies across the major/minor third axis of the target key.
                </div>
                <div class="ref-card">
                    <code>modulate "&lt;from_key&gt;" "&lt;to_key&gt;"</code>
                    Find pivot chords, dominant/tritone-sub approaches, and common-tone functional voice-leading.
                </div>
            </div>
        </details>
    </div>

    <script>
        function runPreset(cmd) {
            const el = document.getElementById('command');
            el.value = cmd;
            document.getElementById('cmd-form').submit();
        }
        function toggleView(mode) {
            const rendered = document.getElementById('view-rendered');
            const raw = document.getElementById('view-raw');
            if (!rendered || !raw) return;
            if (mode === 'raw') {
                rendered.style.display = 'none';
                raw.style.display = 'block';
            } else {
                rendered.style.display = 'block';
                raw.style.display = 'none';
            }
        }
        function copyRaw() {
            const raw = document.getElementById('view-raw');
            if (!raw) return;
            navigator.clipboard.writeText(raw.innerText);
        }
        document.getElementById('command').addEventListener('keydown', function(e) {
            if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                e.preventDefault();
                document.getElementById('cmd-form').submit();
            }
        });
    </script>
</body>
</html>
"""


class CommandRequest(BaseModel):
    command: str


def _render_page(command: str = "", stdout: str = "", stderr: str = "") -> str:
    template = jinja_env.from_string(HTML_TEMPLATE)
    return template.render(
        command=command,
        stdout=stdout,
        stderr=stderr,
        rendered_html=render_markdown_to_html(stdout),
        examples=EXAMPLES,
        subcommands=ALLOWED_SUBCOMMANDS,
    )


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "sandwich-app"}


@app.get("/", response_class=HTMLResponse)
async def get_index(cmd: Optional[str] = Query(default=None)):
    if cmd:
        _, stdout, stderr = execute_command(cmd)
        return _render_page(command=cmd, stdout=stdout, stderr=stderr)
    return _render_page()


@app.post("/run", response_class=HTMLResponse)
async def run_command_form(command: str = Form(default="")):
    if not command.strip():
        return _render_page(command="", stdout="", stderr="Error: Please enter a command.")
    _, stdout, stderr = execute_command(command)
    return _render_page(command=command, stdout=stdout, stderr=stderr)


@app.post("/api/run", response_class=JSONResponse)
async def run_command_api(req: CommandRequest):
    code, stdout, stderr = execute_command(req.command)
    combined = stdout
    if stderr:
        combined = f"{stdout}\n{stderr}".strip() if stdout else stderr.strip()
    return JSONResponse(
        status_code=200 if code == 0 else 400,
        content={
            "exit_code": code,
            "command": req.command,
            "stdout": stdout,
            "stderr": stderr,
            "output": combined,
        },
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
