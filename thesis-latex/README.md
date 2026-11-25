# HCMUT Graduation Thesis -- LaTeX Source (English-Taught Program)

This directory contains the LaTeX source for the graduation thesis of the High-Quality / English-Taught Program (OISP -- Faculty of Computer Science and Engineering, HCMUT -- VNU-HCM):

> **Design and Implementation of a Federated Learning-Based Intrusion Detection and Prevention System with Zero Trust Architecture and SDN for Hospital Networks**

## Directory Structure

```text
thesis-latex/
├── main.tex                              # Root document driver
├── hcmut-thesis.cls                      # HCMUT English thesis class (cover frames, spacing, headers)
├── references.bib                        # Verified BibTeX database (13 entries)
├── graphics/
│   ├── hcmut.png                         # University emblem
│   └── architecture-overview.png         # Overall FL-IDS + ZTA-SDN architecture diagram
├── frontmatter/
│   ├── 01_thesis_mission.tex             # Graduation Thesis Task Assignment
│   ├── 02_declaration.tex                # Declaration of Authorship
│   ├── 03_acknowledgments.tex            # Acknowledgments
│   ├── 04_abstract_en.tex                # English Abstract
│   ├── 05_tom_tat_vi.tex                 # Vietnamese Tóm tắt (bilingual requirement)
│   └── 06_acronyms.tex                   # List of Abbreviations and Acronyms
└── chapters/
    ├── ch1_introduction.tex              # Chapter 1 (complete draft)
    ├── ch2_theoretical_background.tex    # Chapter 2 outline + [TODO] markers
    ├── ch3_fl_ids.tex                    # Chapter 3 outline + [TODO] markers
    ├── ch4_zta_sdn_integration.tex       # Chapter 4 outline + [TODO] markers
    ├── ch5_experiments_evaluation.tex    # Chapter 5 outline + [TODO] markers
    └── ch6_conclusion.tex                # Chapter 6 outline + [TODO] markers
```

## Build Instructions

From inside `thesis-latex/`, run the standard 4-pass `pdflatex` + `bibtex` sequence (tested with MiKTeX / TeX Live):

```powershell
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

Or use `latexmk`:

```powershell
latexmk -pdf -interaction=nonstopmode main.tex
```

## Editing Notes for Team Members

1. **Citations:** Only cite verified keys defined in `references.bib`. Never write `@article` inside `%` comments in `references.bib` because BibTeX parses `@` inside comments as entry headers.
2. **Code spans:** Use `\texttt{...}` in `.tex` files rather than Markdown backticks.
3. **Vietnamese Proper Names & `05_tom_tat_vi.tex`:** `hcmut-thesis.cls` keeps `vntex` and `T5` encoding active while overriding LaTeX structural labels (`Chapter`, `Table of Contents`, `List of Figures`, `References`) to English.
4. **Placeholder items to update before final submission:**
   - Exact assignment/submission dates in `frontmatter/01_thesis_mission.tex`
   - VLAN Server label alignment in `graphics/architecture-overview.png` (`201` -> `210` if diagram is regenerated)
   - `[TODO]` sections and experimental metrics in `chapters/ch2_*.tex` through `chapters/ch6_*.tex`
