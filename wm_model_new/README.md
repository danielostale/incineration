# `wm` — Miami-Dade MSW model (Section 5), Stage 0

Modular, paper-readable implementation of the deterministic **physical +
monetary accounting** model. Tronco: revised §5.4.1 (awareness `A` **and**
convenience `Ψ`, dual flow-to-stock). Stage 0 only — no optimisation.

## Read it like the paper
One module per agent; each method's docstring carries the LaTeX equation and
its number. Suggested reading order = the physical network:

| module | paper | agent / role |
|---|---|---|
| `wm/forms.py` | §5.4 | assumed closed forms ρ, θ, sorting (eqs 3,4,8) |
| `wm/agents/households.py` | §5.1.1.1 | Households (H) |
| `wm/agents/small_commercial.py` | §5.1.1.2 | Small Commercial (SC) |
| `wm/agents/large_generators.py` | §5.1.1.3 | Large Generators (LG) |
| `wm/agents/generator_base.py` | §5.4 | shared generator equations (3,4,6,8,9) |
| `wm/agents/municipality.py` | §5.5/§5.4.1 | MUN; laws of motion (10a,10b), eq 51 |
| `wm/agents/haulers.py` | §5.5.1 | Haulers (HAUL); eqs 13-14 |
| `wm/agents/transfer_station.py` | §5.5.2 | Transfer station (pass-through) |
| `wm/agents/treatment.py` | §5.6 | Treatment (T): separation, MRF, CMP, WTE, LF (eqs 22-40) |
| `wm/agents/government.py` | §5.6.8 | Government/Regulator (GOV) |
| `wm/agents/environment.py` | §5.10 | Environment (ENV); emissions & damages (eqs 65-73) |
| `wm/closure.py` | §5.7/§5.11 | mass balance (eq 55), transfers, diversion (56-57) |
| `wm/simulate.py` | §5.1 | the year-by-year recursion + stock laws of motion |

> The docstrings use `$...$`/`$$...$$` LaTeX. Render them nicely with VS Code
> (autoDocstring/Markdown preview), Jupyter (`?Households`), or `pdoc wm`.

## Run
```bash
python -m wm.run            # -> outputs_endogenous.csv + closure report
pytest -q                  # closure test
```
Inputs live in `data/` (the three CSVs). Endogenous series are computed, never
read.

## Scenarios
- **WTE rebuild:** set `K_WTE > 0` in `data/timeseries_exog.csv` for the online
  years (e.g. 1.4 Mt/yr from 2027).
- **Mechanical sorting:** raise `sep_share` (param) above 0.
- **Turn off convenience** (revert to pre-revision): set `use_convenience = 0`.

## Caveat
Numbers are synthetic placeholders; functional forms (`wm/forms.py`) are
assumed, consistent with the sign restrictions in the text but not unique.
Replace data and forms incrementally; closure must keep holding.
