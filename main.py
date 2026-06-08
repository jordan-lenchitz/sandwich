from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import subprocess
import os
import sys
from jinja2 import Template

app = FastAPI()

# Simple HTML template as a string
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Sandwich 🥪</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; padding: 40px; background: #fafafa; color: #333; text-transform: lowercase; }
        .container { max-width: 900px; margin: auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
        h1 { margin-top: 0; font-weight: 800; font-size: 2.5rem; }
        p { color: #666; font-size: 1.1rem; }
        a { color: #4CAF50; text-decoration: none; }
        a:hover { text-decoration: underline; }
        textarea { 
            width: 100%; 
            height: 120px; 
            padding: 15px; 
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; 
            border: 2px solid #eee; 
            border-radius: 8px; 
            font-size: 1rem;
            transition: border-color 0.2s;
            box-sizing: border-box;
            text-transform: none; /* Keep input as typed */
        }
        textarea:focus { outline: none; border-color: #4CAF50; }
        button { 
            background: #4CAF50; 
            color: white; 
            padding: 12px 24px; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            margin-top: 15px; 
            font-size: 1rem; 
            font-weight: 600;
            transition: background 0.2s;
            text-transform: lowercase;
        }
        button:hover { background: #45a049; }
        h2 { margin-top: 30px; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        pre { 
            background: #1e1e1e; 
            color: #d4d4d4; 
            padding: 20px; 
            border-radius: 8px; 
            overflow-x: auto; 
            white-space: pre-wrap; 
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.95rem;
            line-height: 1.5;
            text-transform: none; /* Keep output as generated */
        }
        .examples { margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; }
        .examples h3 { color: #888; font-size: 0.9rem; text-transform: lowercase; letter-spacing: 1px; }
        .example-list { display: flex; flex-wrap: wrap; gap: 10px; list-style: none; padding: 0; }
        .example-cmd { 
            cursor: pointer; 
            background: #eee; 
            padding: 6px 12px; 
            border-radius: 20px; 
            font-size: 0.85rem; 
            font-family: monospace;
            transition: background 0.2s;
            text-transform: lowercase;
        }
        .example-cmd:hover { background: #ddd; }
    </style>
</head>
<body>
    <div class="container">
        <h1>sandwich 🥪</h1>
        <p>a music theory <a href="https://github.com/jordan-lenchitz/sandwich">toolkit</a> with an emphasis on tritone subs and recursion</p>
        
        <form method="post" action="/run">
            <label style="display:block; margin-bottom:10px; font-weight:600;">command (e.g. parse, key, subs, generate):</label>
            <textarea id="command" name="command" placeholder="parse 'c4 d4 e4 f4 g4' --format text">{{ command }}</textarea>
            <button type="submit">run command</button>
        </form>

        {% if output %}
        <h2>output</h2>
        <pre>{{ output }}</pre>
        {% endif %}

        <div class="examples">
            <h3>try these:</h3>
            <div class="example-list">
                <span class="example-cmd" onclick="setCmd('parse &quot;c4 d4 e4 f4 g4&quot; --format text')">parse melody</span>
                <span class="example-cmd" onclick="setCmd('key &quot;c d e f g a b&quot;')">guess key</span>
                <span class="example-cmd" onclick="setCmd('subs &quot;c e g bb&quot;')">tritone subs</span>
                <span class="example-cmd" onclick="setCmd('harmonize &quot;c4 e4 g4 a4&quot; --format text')">harmonize</span>
                <span class="example-cmd" onclick="setCmd('generate &quot;ab c eb g | ab c d f&quot; --form ABAB')">generate song</span>
                <span class="example-cmd" onclick="setCmd('negative &quot;c e g&quot; --key C')">negative harmony</span>
                <span class="example-cmd" onclick="setCmd('modulate &quot;C major&quot; &quot;Gb major&quot;')">modulate</span>
            </div>
        </div>
    </div>
    <script>
        function setCmd(cmd) {
            document.getElementById('command').value = cmd;
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_index():
    return Template(HTML_TEMPLATE).render(command="", output="")

@app.post("/run", response_class=HTMLResponse)
async def run_command(command: str = Form(...)):
    allowed_subcommands = ["parse", "grid", "subs", "key", "harmonize", "generate", "negative", "modulate"]
    
    # Strip leading 'python3 sandwich.py' if the user accidentally included it
    cmd_to_run = command.strip()
    if cmd_to_run.startswith("python3 sandwich.py"):
        cmd_to_run = cmd_to_run[len("python3 sandwich.py"):].strip()
    elif cmd_to_run.startswith("python sandwich.py"):
        cmd_to_run = cmd_to_run[len("python sandwich.py"):].strip()
    elif cmd_to_run.startswith("sandwich.py"):
        cmd_to_run = cmd_to_run[len("sandwich.py"):].strip()

    import shlex
    try:
        parts = shlex.split(cmd_to_run)
    except Exception as e:
        return Template(HTML_TEMPLATE).render(command=command, output=f"Error parsing command: {str(e)}")

    if not parts or parts[0] not in allowed_subcommands:
        return Template(HTML_TEMPLATE).render(command=command, output="Error: Invalid or disallowed command. Available: " + ", ".join(allowed_subcommands))

    try:
        # Run the command using subprocess
        # Set PYTHONPATH to current dir so sandwich.py can find its modules
        env = os.environ.copy()
        env["PYTHONPATH"] = os.getcwd()
        
        full_command = [sys.executable, "sandwich.py"] + parts
        result = subprocess.run(full_command, capture_output=True, text=True, timeout=30, env=env)
        output = result.stdout
        if result.stderr:
            output += "\\n--- Error Output ---\\n" + result.stderr
        if not output:
            output = "(No output)"
    except Exception as e:
        output = f"Error executing command: {str(e)}"

    return Template(HTML_TEMPLATE).render(command=command, output=output)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
