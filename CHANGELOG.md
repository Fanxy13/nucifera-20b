# Changelog

Every version of Nucifera: what changed, why (what the benchmark showed), and what it scored. The scores are
from `bench/run.py` on a MacBook (Apple M5, 24 GB) with gpt-oss-20b (MLX, MXFP4) on the thinking level
"ultra" – the full tables are in [`results/`](results/).

## v4 – the final run of this round

**16 / 16 (100%) · 23 minutes** (temperature 0.2, as Lotus is set up)

- `write_file` keeps the line break at the end of a file the model writes again (at temperature 1.0 the careful
  edit lost it)
- the profile: the answer of a command is checked before it is used – "the newest version has the highest number"
  (at temperature 1.0 its own script picked an older LTS)
- after a thinking loop, more variety (temperature ≥ 1.0) for the rest of the answer, and the model is told it
  repeated itself – at 0.2 the to-do app failed in v3 because the model fell into the same loop seven times

## v3 – limits from measurements, the web, data

**15 / 16 (94%) · 28 minutes** – and at temperature 1.0: 14.8 / 16, 25 minutes

- **Thinking limits measured.** A step that helps rarely needs more than 10,000 characters of thinking; at about
  18 tokens per second the old limit for ultra (44,000) was ten minutes. Now 6,000 (quick) to 22,000 (ultra).
- **Search that does not give up.** When DuckDuckGo refuses, its plain version is asked. "Nothing found" and "the
  services did not answer" are no longer reported as "is this Mac online?".
- **Pages and data.** A page built by JavaScript says so (nodejs.org's download page: 300 KB of HTML, 940
  characters of text – the model read it 200 characters at a time); reading past the end says there is nothing
  more; a large JSON file comes with its beginning and how to process it with `curl | python3` (300 KB of raw JSON
  made it think for minutes); `search_files` on a web address points to `fetch_url`.
- **The profile:** data is processed with a command, not read by eye.
- **For every AI in Lotus:** search results are often old – the newest version comes from the project's own
  release list; when something cannot be found, say so – never guess, never copy an example.
- **The benchmark got stricter:** the web task is checked against nodejs.org's real release list (v0 to v2 wrote
  an old version or the example from the prompt and only passed the old check).
- The temperature goes with every request, so it can be set and tested without starting the model again.
- In v3 the to-do app failed: at temperature 0.2 the model repeated "Use a CSS variable for container margin top.
  Use a CSS variable for …" – Lotus caught it seven times, and seven times it fell into the same loop (fixed in v4).

## v2 – the Nucifera profile

**15 / 16 (94%) · 23 minutes**

- Its own instructions ([profile/nucifera.md](profile/nucifera.md)): think briefly, never draft files in the
  thinking, one step at a time, trust the tools, check once, short notes between steps, exactly the asked form.
- The model now went to nodejs.org's release list itself – the web task failed only because this Mac was offline
  for a moment (the model said so instead of guessing).
- gpt-oss keeps its reasoning level when Lotus lets it go on: changing it changed the top of the prompt, and the
  model read 12,000 tokens again (25 seconds).
- The instructions carry the date, not the time – the same all day, so they come from the cache in a new chat too.

## v1 – Lotus fixed around the model

**15 / 16 (94%) · 21 minutes – half the time of v0** (scored 16 / 16 with the old, softer web check)

- **The prompt cache works.** The tool list is sent in the same order every time: 77–99% of each prompt from
  MLX' cache, the first token after about a second instead of 6–8.
- **Its thinking comes back** with each tool call, one call per message, as gpt-oss' chat template expects.
- **Loops are stopped:** the same tool call with nothing changed is not run again (the third time ends the tools);
  thinking that repeats itself or goes on too long is cut off and the model is told to act.
- **No more lost files:** `write_file` that would replace a long file with a few lines is refused.
- **Tools by other names** (`open_file`, `bash`, `functions.read_file`) run as the right tool.
- **`search_files` gives the real count** – "32 matching lines in 1 file", not "20".
- `/performance` in Lotus: the report of a conversation that this benchmark keeps for every task.

## v0 – gpt-oss-20b in Lotus 2.13.0 (the starting point)

**13.33 / 16 (83%) · 42 minutes for the 16 tasks**

What the benchmark and the performance reports showed:

- **No prompt cache at all.** Every model request read the whole conversation again (0% from MLX' cache) – the
  tool list in each request came in a different order (a Swift dictionary has none), so the start of the prompt
  was never the same twice. About 450 tokens per second to read on this Mac: 40 seconds before the first word in
  a long conversation.
- **Endless thinking.** The to-do app: 315 seconds of thinking before the first file, then the time was up. In a
  real chat the model thought for 17 minutes and repeated "Now we need to modify script accordingly. Ok." 145 times.
- **A misleading tool.** `search_files` stopped at 20 matches per file and said "20 matching lines" – the model
  wrote 20 into the answer; there were 32.
- **Checking in circles.** The careful edit was exactly right, then the model searched and read the same file
  again and again until its time ran out.
- **Old facts from the web.** A search result title ("Node.js 24.11.0 (LTS)") taken as the newest version.
- **Losing its plan.** Lotus did not give gpt-oss its own thinking back with its tool calls, so it started over
  after every step.
