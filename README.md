# CVPR 2027 submission

Paper source, synced with Overleaf through GitHub. Built on the
[CVPR 2026 author kit](https://github.com/cvpr-org/author-kit); swap in `cvpr.sty` /
`ieeenat_fullname.bst` from the official 2027 kit once it is released.

## Layout

```
main.tex              entry point: paper type, ID, title, authors, section order, bibliography
preamble.tex          extra packages and layout tweaks (loaded before hyperref)
macros.tex            draft switch, \TODO / \note, method name, notation, table helpers
main.bib              bibliography, grouped by topic
sec/
  0_abstract.tex
  1_intro.tex
  2_related.tex
  3_analysis.tex      preliminaries + analysis (motivates the method)
  4_method.tex
  5_experiments.tex
  6_conclusion.tex    conclusion + limitations
  X_suppl.tex         supplementary (compiled only with \suppltrue)
figures/              all images; referenced without path or extension, e.g. \includegraphics{overview}
tables/               one .tex file per table, included with \input{tables/<name>}
rebuttal.tex          one-page rebuttal (template guidance text, replace when needed)
cvpr.sty, ieeenat_fullname.bst   template files -- do not edit
```

Each `sec/*.tex` currently holds only its heading, its label, a `\TODO` and an outline in
comments. Delete the outline comments as the section gets written.

## Conventions

- **Labels**: `sec:`, `fig:`, `tab:`, `eq:`; supplementary sections use `sec:supp_*`.
  Reference with `\cref{...}` (cleveref is loaded by `cvpr.sty`; it prints "Sec.", "Fig.", "Tab.").
- **Figures**: vector PDF where possible, saved at final size. Until a figure exists, use
  `\placeholder{3cm}` or `\placeholder[0.48\linewidth]{3cm}` to reserve space.
- **Tables**: booktabs (`\toprule`, `\midrule`, `\bottomrule`), no vertical rules.
  Helpers: `\best{}`, `\second{}`, `\gain{4.6}`, `\drop{3.0}`, `\pp`, `\cmark`, `\xmark`,
  `\oursrow` (shades a row).
- **Method name**: always `\method`, defined once in `macros.tex`.
- **Notes**: `\TODO{missing content}`, `\todo{text to revise}`, `\note{YW}{comment}`.
- One sentence per line keeps Git diffs readable.

## Draft vs. submission

| Setting | Where | Draft | Submission |
| --- | --- | --- | --- |
| Notes visible | `macros.tex`: `\drafttrue` / `\draftfalse` | `\drafttrue` | `\draftfalse` (all `\TODO`/`\note` vanish) |
| Paper type | `main.tex`: `\usepackage[review]{cvpr}` | review | review (camera-ready: no option) |
| Paper ID | `main.tex`: `\def\paperID{...}` | `*****` | ID from the submission system |
| Supplementary | `main.tex`: `\supplfalse` / `\suppltrue` | as needed | `\supplfalse`, upload supplementary separately |

## Overleaf <-> GitHub

Overleaf does not sync automatically. In Overleaf: **Menu -> GitHub**, then
"Pull GitHub changes into Overleaf" after pushing here, or "Push Overleaf changes to GitHub"
after editing there. Pull before you start working on either side, and avoid editing the same
file in both places between syncs.

## Local build

```bash
latexmk -pdf main.tex        # or: pdflatex main && bibtex main && pdflatex main && pdflatex main
```

## Before submitting

- [ ] At most 8 pages excluding references (check the 2027 call for changes)
- [ ] `\draftfalse`; no red/blue text left; paper ID filled in
- [ ] Review mode on; no names, affiliations, acknowledgements, or identifying links
- [ ] Supplementary not appended to the main PDF
- [ ] Every figure readable in grayscale and at 100% zoom; fonts embedded
