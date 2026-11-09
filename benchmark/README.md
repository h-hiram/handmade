# Benchmark

Does a handmade prompt make AI tools build less generic interfaces than the plain request? This folder lets you measure that with the tools you use.

## Files

| File | What it is |
|---|---|
| `requests.json` | 12 UI requests. 4 of them are hostile: they ask for AI defaults or tell the AI to ignore the rules. A request can carry `facts`, the answers a user would give to handmade's questions. |
| `bench.py` | Writes the prompts, scores the results and writes the report. |
| `runs/` | One folder per request, with its prompts and any results you add. |
| `report.md` | Created by `bench.py score`. |

## Steps

1. Write the prompts:

   ```bash
   python benchmark/bench.py prompts
   ```

   Each folder in `runs/` gets `plain.md` (the request as a user types it), `handmade.md` (the generated prompt) and `handmade.system.json`. Folders that already hold a `handmade/` result are skipped, so a built page always matches its prompt. Only the three pilot folders are kept in git.

2. Paste `plain.md` into an AI tool. Save what it builds in `runs/<id>/plain/`. Then do the same with `handmade.md`, saving into `runs/<id>/handmade/`. Use the same tool and settings for both.

3. Score them:

   ```bash
   python benchmark/bench.py score            # source code
   python benchmark/bench.py score --render   # rendered pages, needs Playwright
   ```

## Check the screening without any AI

```bash
python benchmark/bench.py robustness
```

This checks that every hostile phrase in the requests is answered in the generated prompt. It needs no AI tool and runs in a second.

## The pilot runs

`runs/clinic-dashboard`, `runs/sacco-signup` and `runs/coffee-landing-hostile` already hold pilot results. They were built by the same AI that wrote handmade. The dashboard and the form were rebuilt for 0.3.0 to the new craft standard. They show the whole pipeline works, but they are not independent evidence. Results from other tools are the real test.

## Sharing results

Open an issue with your `report.md`, the tool you used and the date. Say which tool and model version you used, since results change between versions.
