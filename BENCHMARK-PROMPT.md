# The Nucifera skill test – one message

Paste the message below into the Lotus web chat (or `/ai`), let it work, then type `/performance`. You get a
`.txt` file with every step, the time and tokens of every model request and the Lotus log – that file is what
improves Nucifera: hand it over, and the next version is tuned on what went wrong.

It tests eight skills in one go: writing code, debugging, building a web page, working with data, reasoning,
Lotus' own tools, looking things up on the web and another language. Everything happens in one new folder on
the Desktop – nothing else is touched.

---

```text
# Nucifera skill test

Work in a new folder ~/Desktop/nucifera-test (create it). Do these 8 tasks in order. After each task, say in one line what you did and how you checked it.

1. Coding – Create primes.py that prints the first 20 prime numbers, one per line. Run it with python3 and check the output.

2. Debugging – Create cart.js with exactly this code, run it with node, find out why the total is wrong (it should be 116.75), fix it with a small edit and run it again:

const prices = { apple: 5, pear: 14, melon: 32 };
function cartTotal(cart) {
  let total = 0;
  for (let i = 1; i < cart.length; i++) total += prices[cart[i].name] * cart[i].quantity;
  return total;
}
const cart = [{ name: 'apple', quantity: 2 }, { name: 'pear', quantity: 1 }, { name: 'melon', quantity: 3 }];
const total = Math.round(cartTotal(cart) * 0.9 * 1.081 * 100) / 100;
console.log('Total:', total);

3. Web – Build a one-page site in the folder site (index.html and style.css): a clean landing page for a tea shop called "Matcha Garden" with a header, three product cards and a footer. Look at it with view_page and fix what it reports.

4. Data – Create data.csv with a header row and 10 rows of fruit,price,quantity (make up the values), then compute the total value (the sum of price × quantity) with a command and write only that number into total.txt.

5. Reasoning – Without tools: Anna is older than Ben. Ben is older than Carla. Dana is younger than Carla. Eva is older than Anna. Who is the second youngest? Answer in one sentence.

6. Lotus – Use Lotus' own tools: which Lotus features are switched on, and what is the weather in Zurich right now?

7. Research – Look up the current Node.js LTS version on nodejs.org and write only the version number into node-lts.txt.

8. Language – Explain in exactly two German sentences what a symlink is.

At the end, give a short table: task, done (yes/no), how you checked it.
```

---

## What a good run looks like

| Task | Right result |
|---|---|
| 1 | `python3 primes.py` prints 2, 3, 5 … 71 |
| 2 | the loop starts at `0` instead of `1`; `node cart.js` prints `Total: 116.75` – and cart.js is still the whole file |
| 3 | `site/index.html` and `site/style.css`, looked at with view_page, nothing left to fix |
| 4 | `total.txt` holds the sum that matches data.csv |
| 5 | Carla |
| 6 | the Lotus tools `lotus_status` and `weather` were used – not a shell command |
| 7 | `node-lts.txt` holds a version like `v22.x.y`, found with web_search / fetch_url |
| 8 | two German sentences |

The automatic version of this – 16 tasks, scored by checks – is `python3 bench/run.py <name>` (see the README).
