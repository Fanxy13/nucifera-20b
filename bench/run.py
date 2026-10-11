#!/usr/bin/env python3
"""Runs the Nucifera benchmark with the AI of Lotus and the model on this Mac.

  python3 bench/run.py v1                       all tasks → results/v1/
  python3 bench/run.py v1 --tasks fix-bug,web   some of them
  python3 bench/run.py v1 --effort high         another thinking level (default: Lotus' setting)

It needs Lotus (LOTUS_ROOT, default ~/.local/share/lotus) and its model on this Mac running (start /ai once,
or lotus ai local). Every task runs like a message in /ai: in its own empty folder, with the tools of Lotus in
auto mode, and nothing of yours is touched – its memory and state stay in the task's folder. Lotus writes a
performance report for every task (/performance); the check scores what came out.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tasks import TASKS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()


def settings():
    """Lotus' settings (KEY='value' lines)."""
    f = Path(os.environ.get("XDG_CONFIG_HOME") or HOME / ".config") / "lotus" / "settings.zsh"
    out = {}
    if f.exists():
        for line in f.read_text().splitlines():
            m = re.match(r"^(\w+)='(.*)'$", line)
            if m:
                out[m.group(1)] = m.group(2)
    return out


def build(lotus):
    """The AI program of that Lotus, built once into bench/.build (not into Lotus' own cache)."""
    sources = sorted((lotus / "lib" / "ai").glob("*.swift"))
    digest = hashlib.sha1(b"".join(p.read_bytes() for p in sources)).hexdigest()[:12]
    out = ROOT / "bench" / ".build" / f"lotus-ai-{digest}"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        print("Building the AI program of Lotus (about a minute) …", flush=True)
        r = subprocess.run(["xcrun", "swiftc", "-Onone", "-parse-as-library", "-swift-version", "5", "-o", str(out)] + [str(p) for p in sources],
                           capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit("Could not build it:\n" + r.stderr[-2000:])
    return out


def toolkit(lotus):
    """The Lotus tools of the features that are on (the same list /ai gets)."""
    script = 'source $LOTUS_ROOT/lib/core.zsh; lotus_load; source $LOTUS_ROOT/lib/cmd/aitools.zsh; lotus_ai_toolkit >/dev/null && print -r -- $REPLY'
    r = subprocess.run(["zsh", "-fc", script], capture_output=True, text=True, env={**os.environ, "LOTUS_ROOT": str(lotus)})
    path = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    return path if path.startswith("/") else ""


def lotus_version(lotus):
    m = re.search(r"LOTUS_VERSION=([\d.]+)", (lotus / "lib" / "core.zsh").read_text())
    return m.group(1) if m else "?"


def web_chat_busy():
    f = HOME / ".local" / "state" / "lotus" / "ai-server.now"
    try:
        return bool(json.loads(f.read_text()).get("run"))
    except Exception:
        return False


class Result:
    """What came out of a task: the answer, the steps, the numbers."""

    def __init__(self, data, output, binary):
        self.output, self.binary = output, binary
        msgs = data.get("messages", [])
        self.events = [e for m in msgs if m.get("role") == "assistant" for e in m.get("events", [])]
        if not msgs:
            self.events = Result.from_output(output)      # a Lotus without /performance: what it printed
        # the answer: the text after the last step (gpt-oss also writes short notes between its steps)
        last_tool = max((i for i, e in enumerate(self.events) if e.get("type") == "tool"), default=-1)
        self.answer = "".join(e.get("text", "") for e in self.events[last_tool + 1:] if e.get("type") == "text")
        self.tools = [e for e in self.events if e.get("type") == "tool"]

    @staticmethod
    def from_output(output):
        """The steps and the answer from the terminal output of /ai (● Tool(args) · ⎿ result · ● text)."""
        labels = {"List", "Read", "Write", "Edit", "Search", "Run", "Web", "Fetch", "Remember", "View", "Lotus status", "Weather", "Theme",
                  "Open", "Find app", "Install", "Music", "Clock", "Keep awake", "Features", "Minecraft", "Remove BG"}
        text = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", output).replace("\r", "\n")
        events, answer = [], []
        for line in text.split("\n"):
            m = re.match(r"^● (.+?)(?:\((.*)\))?$", line)
            if m and m.group(1) in labels:
                events.append({"type": "tool", "name": m.group(1), "detail": m.group(2) or ""})
                answer = []
            elif line.startswith("  ⎿"):
                events.append({"type": "result", "text": line[4:].strip()})
            elif line.startswith("● "):
                answer = [line[2:]]
            elif answer and not line.startswith(("✻", "  ⎿")):
                answer.append(line[2:] if line.startswith("  ") else line)
        if answer:
            events.append({"type": "text", "text": "\n".join(answer).strip()})
        return events

    def tool_names(self):
        return [t.get("name", "") for t in self.tools]

    def used(self, label):
        return any(t.get("name", "") == label for t in self.tools)

    def numbers(self):
        ev = self.events
        summary = next((e for e in reversed(ev) if e.get("type") == "answer"), {})
        models = [e for e in ev if e.get("type") == "model"]
        results = [e for e in ev if e.get("type") == "result"]
        infos = [e.get("text", "") for e in ev if e.get("type") == "info"]
        prompt = sum(max(0, m.get("prompt", 0)) for m in models)
        cached = sum(max(0, m.get("cached", 0)) for m in models)
        return {
            "secs": round(float(summary.get("secs", ev[-1].get("t", 0) if ev else 0)), 1),
            "thinking_secs": round(float(summary.get("thought", 0)), 1),
            "outcome": summary.get("outcome", "none"),
            "steps": len(self.tools),
            "failed_steps": sum(1 for x in results if x.get("error")),
            "model_requests": len(models),
            "prompt_tokens": prompt,
            "cache_percent": round(cached * 100 / prompt) if prompt else 0,
            "written_tokens": sum(int(m.get("wrote", 0)) for m in models),
            "thinking_chars": sum(int(m.get("thinking", 0)) for m in models),
            "go_on": sum(1 for i in infos if i.startswith("↻")),
            "loops": sum(1 for x in results if "The same as before" in x.get("text", "") or "stopped the tools" in x.get("text", "")),
            "overthought": sum(1 for i in infos if "thought for a long time" in i or "went in circles" in i),
            "cut_short": sum(1 for x in results if x.get("text", "").startswith("Not written: it would replace")),
            "tools": self.tool_names(),
        }


def scrub(folder):
    """No home folder or temporary folder in what is kept (the results are public): ~ and $TMPDIR instead."""
    tmp = os.path.realpath(os.environ.get("TMPDIR", "/tmp")).rstrip("/")
    for f in Path(folder).rglob("*"):
        if f.is_file() and f.suffix in (".txt", ".json", ".md"):
            t = f.read_text(errors="replace")
            new = t.replace(tmp, "$TMPDIR").replace(tmp.replace("/private", "", 1), "$TMPDIR").replace(str(HOME), "~")
            if new != t:
                f.write_text(new)


def write_summary(out, summary):
    (out / "results.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    lines = [f"# Nucifera benchmark – {summary['name']}", "",
             f"{summary['date']} · Lotus {summary['lotus']} · {summary['model']} · thinking {summary['effort']} · temperature {summary.get('temperature', '?')}", "",
             f"**Score: {summary['score']} / {summary['max']} ({summary['percent']}%)** · {summary['secs']:.0f} s in all", "",
             "| Task | Skill | Score | Time | Steps | Cache | Note |", "|---|---|---|---|---|---|---|"]
    for x in summary["tasks"]:
        lines.append(f"| {x['id']} | {x['skill']} | {x['score']} | {x['wall_secs']:.0f} s | {x['steps']} | {x['cache_percent']}% | {x['note'].replace('|', '/').replace(chr(10), ' ')[:160]} |")
    (out / "summary.md").write_text("\n".join(lines) + "\n")


def rescore(name):
    out = ROOT / "results" / name
    summary = json.loads((out / "results.json").read_text())
    work = Path(os.environ.get("TMPDIR", "/tmp")) / f"nucifera-bench-{name}"
    tasks = {t.id: t for t in TASKS}
    for x in summary["tasks"]:
        report = out / "tasks" / x["id"] / "report.txt"
        try:
            data = json.loads(Path(str(report) + ".json").read_text())
        except Exception:
            data = {}
        output = (report.parent / "output.txt").read_text() if (report.parent / "output.txt").exists() else ""
        builds = sorted((ROOT / "bench" / ".build").glob("lotus-ai-*"))
        r = Result(data, output, str(builds[-1]) if builds else "")
        score, note = tasks[x["id"]].check(str(work / x["id"]), r)
        if x.get("timed_out"):
            note = "timed out – " + note
        if score != x["score"]:
            print(f"  {x['id']}: {x['score']} → {round(score, 2)} ({note})")
        x["score"], x["note"] = round(score, 2), note
    total = sum(x["score"] for x in summary["tasks"])
    summary["score"], summary["percent"] = round(total, 2), round(total * 100 / max(1, len(summary["tasks"])))
    write_summary(out, summary)
    scrub(out)
    print(f"Score {summary['score']} / {summary['max']} ({summary['percent']}%)")


def main():
    ap = argparse.ArgumentParser(description="The Nucifera benchmark")
    ap.add_argument("name", help="a name for this run, e.g. v1 – results go to results/<name>/")
    ap.add_argument("--tasks", default="", help="only these tasks (comma-separated ids)")
    ap.add_argument("--effort", default="", help="low, medium, high, max or ultra (default: Lotus' setting)")
    ap.add_argument("--temp", default="", help="the creativity (temperature) of the model (default: Lotus' setting)")
    ap.add_argument("--lotus", default=os.environ.get("LOTUS_ROOT", str(HOME / ".local/share/lotus")), help="the Lotus to use")
    ap.add_argument("--url", default="http://127.0.0.1:18765/v1", help="the model server")
    ap.add_argument("--rescore", action="store_true", help="score a finished run again (after a check changed), without the model")
    args = ap.parse_args()
    if args.rescore:
        return rescore(args.name)

    lotus = Path(args.lotus).expanduser().resolve()
    conf = settings()
    model_id = conf.get("LOTUS_AI_LOCAL", "gpt-oss-20b")
    model = HOME / ".local/share/lotus/llm" / model_id
    effort = args.effort or conf.get("LOTUS_AI_EFFORT", "high")
    temp = args.temp or conf.get("LOTUS_AI_TEMP", "0.6")
    try:
        urllib.request.urlopen(args.url + "/models", timeout=3).read()
    except Exception:
        sys.exit(f"The model server does not answer at {args.url} – start /ai once (or lotus ai local), then run this again.")
    binary = build(lotus)
    tools = toolkit(lotus)
    version = lotus_version(lotus)
    out = ROOT / "results" / args.name
    if out.exists():
        shutil.rmtree(out)
    work = Path(os.environ.get("TMPDIR", "/tmp")) / f"nucifera-bench-{args.name}"
    shutil.rmtree(work, ignore_errors=True)
    chosen = [t for t in TASKS if not args.tasks or t.id in args.tasks.split(",")]
    print(f"Nucifera benchmark {args.name}: {len(chosen)} tasks · Lotus {version} · {model_id} · thinking {effort} · temperature {temp}", flush=True)

    results = []
    for task in chosen:
        while web_chat_busy():
            print("  (the web chat is answering – waiting)", flush=True)
            time.sleep(15)
        d = work / task.id
        state = work / ".state" / task.id
        d.mkdir(parents=True)
        state.mkdir(parents=True)
        if task.setup:
            task.setup(str(d))
        report = out / "tasks" / task.id / "report.txt"
        report.parent.mkdir(parents=True, exist_ok=True)
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(HOME), "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8",
            "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
            "LOTUS_ROOT": str(lotus), "LOTUS_VERSION": version, "LOTUS_STATE": str(state), "LOTUS_AI_STATE": str(state),
            "LOTUS_CACHE": str(HOME / ".cache/lotus"),
            "LOTUS_AI_PROVIDER": "openai", "LOTUS_AI_URL": args.url, "LOTUS_AI_MODEL": str(model), "LOTUS_AI_OPENAI_KEY": "local",
            "LOTUS_AI_LABEL": f"{model_id} · on this Mac", "LOTUS_AI_CONTEXT": conf.get("LOTUS_AI_CONTEXT", "32768"),
            "LOTUS_AI_EFFORT": effort, "LOTUS_AI_TEMP": temp, "LOTUS_AI_ENHANCE": "off", "LOTUS_AI_TOOLS": "1", "LOTUS_AI_PERM_MODE": "auto",
            # what the AI may do: as you set it up in Lotus (questions count as "no" here – nobody answers them)
            **{k: conf.get(k, v) for k, v in {"LOTUS_AI_PERM_READ": "allow", "LOTUS_AI_PERM_READ_OUT": "ask", "LOTUS_AI_PERM_WRITE": "ask",
                                              "LOTUS_AI_PERM_WRITE_OUT": "ask", "LOTUS_AI_PERM_RUN": "ask", "LOTUS_AI_PERM_WEB": "allow",
                                              "LOTUS_AI_PERM_LOTUS": "ask"}.items()},
            "LOTUS_AI_MEMORY": str(d / ".memory.md"), "LOTUS_AI_TOOLKIT": tools,
            "LOTUS_LOG": str(state / "lotus.log"), "LOTUS_LOG_LEVEL": "debug", "LOTUS_AI_PERFORMANCE": str(report),
        }
        print(f"  {task.id:<15} {task.skill:<13}", end="", flush=True)
        started = time.time()
        try:
            p = subprocess.run([str(binary), "--once", task.prompt], cwd=d, env=env, capture_output=True, text=True, timeout=task.timeout)
            output = p.stdout + p.stderr
            timed_out = False
        except subprocess.TimeoutExpired as e:
            output = (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
            timed_out = True
        wall = round(time.time() - started, 1)
        try:
            data = json.loads(Path(str(report) + ".json").read_text())
        except Exception:
            data = {}
        r = Result(data, output, str(binary))
        try:
            score, note = task.check(str(d), r)
        except Exception as e:
            score, note = 0, f"the check failed: {e}"
        if timed_out:
            note = f"timed out after {task.timeout} s – " + note
        n = r.numbers()
        (report.parent / "output.txt").write_text(re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", output))
        results.append({"id": task.id, "skill": task.skill, "score": round(score, 2), "note": note, "wall_secs": wall, "timed_out": timed_out, **n})
        mark = "pass" if score >= 1 else "part" if score > 0 else "FAIL"
        print(f"{mark:<5} {score:>4.2f}  {wall:>6.1f}s  {n['steps']:>2} steps  cache {n['cache_percent']:>3}%  {note}", flush=True)

    total = sum(x["score"] for x in results)
    summary = {
        "name": args.name, "date": time.strftime("%Y-%m-%d %H:%M"), "lotus": version, "model": model_id, "effort": effort, "temperature": temp,
        "score": round(total, 2), "max": len(results), "percent": round(total * 100 / max(1, len(results))),
        "secs": round(sum(x["wall_secs"] for x in results), 1), "tasks": results,
    }
    write_summary(out, summary)
    scrub(out)
    print(f"\nScore {summary['score']} / {summary['max']} ({summary['percent']}%) · {summary['secs']:.0f} s · results/{args.name}/summary.md")


if __name__ == "__main__":
    main()
