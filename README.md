# Daily Brief

A daily four-story brief: quantum computing, software engineering, AI, and a
wildcard. Days alternate between **learn days**, which move one stop further
along a curriculum for each topic, and **news days**.

Live at https://sid-agnihotri.github.io/daily-brief/

- `index.html` is always the latest edition.
- `learned.html` maps progress along each topic line, with the takeaways from
  every stop.
- `archive.html` lists every edition.

## How it's put together

- `data/progress.json` is the single source of truth: each topic's syllabus
  and a log of every edition.
- `editions/YYYY-MM-DD.html` holds one hand-written edition each. Once
  published, an edition never changes.
- `build.py` fills in the navigation, progress map and footer of each edition,
  then generates the home page, the archive and the learned page. It uses only
  the Python standard library.
- `RUNBOOK.md` is the checklist the scheduled run follows each morning.

```sh
python3 build.py status     # what the next edition should cover
python3 build.py check      # validate data and edition files
python3 build.py            # rebuild everything
```
