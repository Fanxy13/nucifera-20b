# Nucifera-20b

**Nucifera** is the AI of [Lotus](https://github.com/Fanxy13/homebrew-lotus) on your Mac: OpenAI's open-weight
model **gpt-oss-20b**, running locally with Apple's MLX, tuned to work in Lotus – in `/ai` in the terminal and in
the Lotus web chat. *Nelumbo nucifera* is the sacred lotus.

The weights are gpt-oss-20b as OpenAI released them (Apache 2.0, the MLX build
`mlx-community/gpt-oss-20b-MXFP4-Q8`). What makes it Nucifera is everything around them, measured and improved
with the benchmark in this repo:

- **how Lotus talks to it** – its harmony format, its thinking kept from one tool step to the next, one tool
  call per message, requests that read the same every time so MLX reuses its cache
- **what it is told** – Lotus' instructions plus its own profile ([`profile/nucifera.md`](profile/nucifera.md))
- **how it samples** – temperature and top-p ([`profile/settings.json`](profile/settings.json))
- **what Lotus does when it goes wrong** – loops, endless thinking, files cut short, tools by other names

## Scores

| Version | Lotus | Score | Time for the 16 tasks |
|---|---|---|---|
| **v4** – everything below, final | 2.13.1 | **16 / 16 (100%)** | **23 min** |
| v3 – thinking limits measured, the web, JSON as data | 2.13.1 | 15 / 16 (94%) | 28 min |
| v2 – the Nucifera profile | 2.13.1 | 15 / 16 (94%) | 23 min |
| v1 – Lotus fixed around the model | 2.13.1 | 15 / 16 (94%) | 21 min |
| v0 – gpt-oss-20b as it was | 2.13.0 | 13.3 / 16 (83%) | 42 min |

Thinking level "ultra", temperature 0.2 · MacBook with Apple M5, 24 GB · the tables are in [`results/`](results/).
v3 was also run at temperature 1.0 (OpenAI's recommendation for gpt-oss): 14.8 / 16 in 25 minutes – no thinking
loops, but more slips. Single runs vary – a task that passes four times can fail the fifth.

| Task | v0 | v4 |
|---|---|---|
| fix a bug | ✓ 118 s | ✓ 41 s |
| build a to-do web app | ⅓ – ran out of time after one file | ✓ – works in a browser (then polished until the 12-minute limit) |
| rename across files, run the tests | ✓ 197 s | ✓ 75 s |
| count in a log | ✗ wrote 20 (a tool said 20, there were 32) | ✓ 31 s |
| sum of primes · order puzzle | ✓ · ✓ | ✓ · ✓ |
| predict a program's output | ✓ 78 s | ✓ 46 s |
| three bullets · two German sentences | ✓ · ✓ | ✓ · ✓ |
| find a value in a long file | ✓ 60 s | ✓ 27 s |
| Lotus' own tools | ✓ | ✓ |
| the current Node.js LTS from the web | ✗ an old version from a search title | ✓ v24.21.0 from nodejs.org's release list, 104 s |
| ignore instructions hidden in a file | ✓ | ✓ |
| remember a fact | ✓ | ✓ |
| write and run a script | ✓ 137 s | ✓ 45 s |
| two exact edits in a long file | ✓ but checked in circles until its time ran out (480 s) | ✓ 175 s |

The biggest single change: **the prompt cache**. v0 read every request from the start (0% from MLX' cache); now
77–99% of each prompt comes from the cache and the first token arrives after about a second – in a long chat
that was 40 seconds per step.

## Run the benchmark

```bash
python3 bench/run.py v5              # all 16 tasks → results/v5/
python3 bench/run.py v5 --tasks fix-bug,web
```

It needs Lotus with its model on this Mac (`lotus ai local`, then `/ai` once so the model runs). Every task
runs like a message in `/ai`: in its own empty folder, in auto mode, with your permissions – questions count as
"no" because nobody answers them. Lotus writes a performance report for each task
(`results/<name>/tasks/<task>/report.txt`), the check scores what came out, and `results/<name>/summary.md`
has the table.

| Skill | Tasks |
|---|---|
| coding | fix a bug without breaking the file · build a to-do web app (checked in a browser) · write and run a script |
| agent work | rename a function in several files and run the tests |
| editing | two exact changes in a long file, nothing else |
| data | count in a log file |
| reasoning | a sum of primes · an order puzzle · predict a program's output without running it |
| instructions | exactly three bullets of at most 8 words |
| language | exactly two German sentences |
| reading | find one value in a 400-line file |
| Lotus | use Lotus' own tools |
| web | look up a version on the web |
| safety | ignore instructions hidden in a file |
| memory | keep a fact for later |

## Test it yourself – one message

[`BENCHMARK-PROMPT.md`](BENCHMARK-PROMPT.md) is the same idea in one message for the web chat. Paste it,
let it work, type `/performance` and you get a `.txt` file with every step, the time and tokens of every model
request and the logs – the material for the next version.

## Versions

See [CHANGELOG.md](CHANGELOG.md) – every version with what changed and what it scored.
