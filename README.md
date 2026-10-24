# Foglalj helyet :)

A courtyard built in workshops, together with the people who live there: the yard of the homeless shelter at
Alföldi utca 6, Budapest VIII. Placemaking project, October 2026.

Sandrini Anna Lena · Szekeres Dávid · Rosenberg-Hagymásy Lilla

## The website (`web/`)

A three.js site in Hungarian (English on the switch), with three tabs:

- **A te udvarod**: everything the workshops made, set out at once. Drag the furniture about, turn it, walk round in
  first person (W A S D), switch to night.
- **Idővonal**: the eight workshops on a timeline with a picture over every stop; each one halfway through (people at
  work) and finished (the space in use), with its materials and cost.
- **Bemutató**: the 7-minute presentation (site analysis, interviews, concept, four workshops, the opening).

Run it locally from `web/` with any static server, for example:

```
python -m http.server 8617
```

then open http://localhost:8617. (Opened as a file it can't load the model.)

- `index.html`: the whole viewer (one file).
- `phases.json` / `phases.hu.json`: the stages, their texts (English / Hungarian), people, camera views and costs.
- `presentation.json`: the slides.
- `model/`: the yard exported from the Rhino model (`scripts/export_web.py`).
- `presentation/`: slide pictures and the window-pattern texture.
- `audio/`: the music (credits below).

## Scripts (`scripts/`)

IronPython 2.7 scripts that build each workshop into the Rhino 7 model (`build_*.py`, run inside Rhino through
`au6_build.py`), and Python 3 scripts: `export_web.py` (model → `web/model`), `workshop_pdf.py` (the A3 sheet of the
workshops).

## Docs (`docs/`)

`cost_plan.md` (materials and cost per workshop) and `Alfoldi6_workshopok_A3.pdf` (the workshops on one A3 sheet).

`presentation/Foglalj_helyet_bemutato.pdf`: the project presentation (19 slides, Hungarian): site analysis, the
conversations, the concept and the eight workshops. `Foglalj_helyet_bemutato.html` is the same deck as a web page
(open it from inside the repository so the pictures load).

## Not in this repository

- The Rhino model (`rhino/*.3dm`, about 195 MB each: over GitHub's file size limit).
- The raw survey photos (`photos/`): the site only uses a selection, with faces and number plates blurred.

## Credits

- „Flamenco sample” by FranciscoKeep, Wikimedia Commons, [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/).
- „JRPG Piano” by Joth, OpenGameArt, CC0.
- Street context from OpenStreetMap (© OpenStreetMap contributors, ODbL).
