# Daily Brief runbook

Instructions for the scheduled run that publishes one edition every morning.
Follow them in order. The reader is Sid, a frontend developer in Vancouver,
reading on his iPhone around 9am Pacific.

## Where things live

- Source and history: the GitHub repository **Sid-Agnihotri/daily-brief**
  (branch `main`). Every edition ever published is in `editions/`, and
  `data/progress.json` is the log of everything learned.
- Hosting: GitHub Pages serves `main` at
  **https://sid-agnihotri.github.io/daily-brief/**. A push is live within a
  minute or two.
- `index.html` is generated: a copy of the newest edition. Never edit it by
  hand.

## What an edition is

Four stories, one per track, published as one page:

| Track id   | Name                  | Covers |
|------------|-----------------------|--------|
| `quantum`  | Quantum computing     | Qubits to fault tolerance, plus the industry |
| `systems`  | Software engineering  | The full picture of building an app: networking, APIs, databases, caching, scaling, DevOps, CI/CD, cloud, observability, reliability, security |
| `ai`       | AI                    | How models work, prompting, RAG, tool use, MCP, agents, fine-tuning, evals, serving, plus industry news |
| `wildcard` | Wildcard              | A surprising fact, new research, or something delightfully random |

Days alternate between two modes:

- **Learn day.** Each of the three main tracks advances to its *next stop* in
  `data/progress.json`. Find the single best existing article on that concept,
  read it fully, then explain it in your own words, building on what has
  already been learned. The wildcard is a fascinating piece of recent research
  or a striking fact.
- **News day.** For each track, find the most significant news since the
  previous news day (normally the last 48 hours; widen to 7 days if it's
  quiet). Explain what happened, why it matters, and connect it to stops
  already learned. The wildcard is a new research result from the past week
  or two.

## Steps

0. **Get the repo.** Attach `Sid-Agnihotri/daily-brief` with push access
   and clone it. Work inside the clone.

1. **Get the plan.** Run `python3 build.py status`.
   - If `already_published_today` is `true`, stop. Do not publish twice.
   - Use `next_mode`, `next_day`, `next_stops`, `learned_so_far`,
     `wildcard_titles_so_far` and `recent_source_urls` from the output.

2. **Research.** Use web search and fetch the pages you'll rely on; read the
   full article, not just the search snippet.
   - Learn days: prefer the canonical explainer for the concept (well-known
     essays, official docs, respected engineering blogs, classic papers with a
     readable companion). One primary source per story, plus up to two
     supporting links.
   - News days: prefer primary sources (company or lab announcement, the
     paper, the release notes, the postmortem) over aggregators.
   - Never reuse a URL in `recent_source_urls`, and never repeat a wildcard
     topic already in `wildcard_titles_so_far`.
   - Verify every number, date and name you print against what you fetched.

3. **Write `editions/<today>.html`.** Copy the structure of the newest
   edition file exactly: the same `<head>` (fonts, home-screen icon,
   `../assets/style.css`), the three marker pairs
   `<!--NAV:START--><!--NAV:END-->`, `<!--MAP:START--><!--MAP:END-->` (inside
   the masthead) and `<!--FOOT:START--><!--FOOT:END-->` (end of `<main>`),
   and the same classes. Leave the markers empty; `build.py` fills them. Link
   to other site files with relative paths starting with `../`; `build.py`
   rewrites them for the home-page copy.
   - Masthead: `.dateline` with the long date, an `h1` like
     “Day N: <theme of the day>”, and a one-paragraph `.lede` naming all four
     stories.
   - Each story is `<article class="story" id="<track>" data-track="<track>">`
     with, in order: `.kicker`, `h2`, `.dek`, body, one or more `<figure>`s,
     `.keep` (“Worth keeping”, exactly three bullets), `.source` card, and on
     learn days `.nextstop` naming the following stop.
   - Kicker text: learn day “Quantum computing, stop 2 of 12”; news day
     “Quantum computing news”; wildcard just “Wildcard”.
   - Every story needs at least one visual: an inline SVG diagram, a chart, a
     timeline (`ol.timeline`), a comparison table (`table.compare`), or bars
     (`.bars`, `.stack`). Aim for one interactive element per edition (a
     stepper, slider or simulation) with its script inline at the bottom of
     the page, wrapped in an IIFE, no external libraries.
   - Diagrams: inline SVG, `viewBox` at most 340 wide so text stays legible on
     a phone, colours only through the classes `svg-ink`, `svg-muted`,
     `svg-c`, `svg-stroke-*`, `svg-paper` or `var(--…)`, so light and dark
     mode both work. Label things directly instead of using legends. Mark
     illustrative numbers as illustrative.
   - No hotlinked images.

4. **Log it.** Append an entry to `editions` in `data/progress.json`:
   ```json
   {
     "date": "YYYY-MM-DD", "day": N, "mode": "learn" | "news",
     "title": "Day N: …", "file": "editions/YYYY-MM-DD.html",
     "items": [
       {"track": "quantum", "stop": "<stop id, learn days only>", "anchor": "quantum",
        "title": "<the story h2>",
        "takeaways": ["<the three Worth keeping bullets, verbatim>"],
        "sources": [{"title": "…", "by": "…", "url": "https://…"}]}
     ]
   }
   ```
   News items and the wildcard have no `stop`. On a learn day, if a concept
   turns out to need two days, add a new stop to that track's `syllabus`
   right after the current one; never reorder or remove stops already learned.

5. **Build and check.** Run `python3 build.py`. It refuses to build if
   anything is inconsistent; fix and rerun. Then open `index.html` at 390px
   wide with Playwright in light and dark mode. Check that nothing overflows
   sideways, every diagram reads clearly, and the console shows no script
   errors (font loading failures in the sandbox are expected).

6. **Publish.** Commit everything and push to `main`:
   `git add -A && git commit -m "Day N: <title>" && git push`.
   If the push is rejected because `main` moved, `git pull --rebase` and push
   again. Then fetch the site URL and confirm it shows today's `h1` (Pages can
   take a minute or two to update).

7. **Tell Sid.** Finish with a short message: the link, then one line per
   story title.

## Writing rules

- Explain in your own words. Quote at most once per source, under 15 words,
  and only when the exact wording matters. Never reproduce paragraphs.
- Plain, direct sentences. Sentence case everywhere. No all-caps labels, no
  emoji, no filler such as “in today’s fast-paced world.”
- Lead each story with what it is and why it matters, then the mechanism.
- Build on earlier stops: name the concept learned before and show how the
  new one extends it.
- Be honest about uncertainty: say when something is disputed, early, or
  a company's own claim.
- Each story should take roughly 4 to 6 minutes to read on a phone.
