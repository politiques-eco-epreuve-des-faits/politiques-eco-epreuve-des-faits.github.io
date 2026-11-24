# Routine mensuelle : textes de la veille (repo politiques-eco-epreuve-des-faits/politiques-eco-epreuve-des-faits.github.io)

Routine créée le 18/11/2026 : trig_018B4W9jWZuuc4Lqf4CfKTGz (https://claude.ai/code/routines/trig_018B4W9jWZuuc4Lqf4CfKTGz), Opus 5.5, connecteur Claude Docs seulement.
Calendrier proposé : le 16 de chaque mois, 05:30 UTC, sur le repo `politiques-eco-epreuve-des-faits/politiques-eco-epreuve-des-faits.github.io`.
Elle ouvre une pull request ; elle ne pousse jamais sur `main`. Fusionner la PR = publier.
Les graphiques OCDE sont actualisés à part par `.github/workflows/charts.yml` (le 2 du mois).

---

## Prompt (à coller dans la routine)

You maintain a public tracker for the next edition of a French economics textbook. Work only on this repository.
Create a branch `claude/veille-YYYY-MM`, make the changes below, and open a pull request. Never push to `main`.

**Step 0: academic sweep (fixed list, read before any web search).** `routines/flux.json` holds every NBER working paper, CEPR discussion paper and article in the AER, Econometrica, QJE, JPE, REStud, JEL, JEP and Annual Review of Economics, saved each Monday by `.github/workflows/feeds.yml` (the feeds themselves only go back one to two weeks). Read the title and abstract of every item whose `collecte` date is on or after the 16th of last month (the previous run). Keep only those that bear on a specific message of `_data/ch6.yml` (note which one). For a kept item without an abstract, read it on its `url` or at `https://api.openalex.org/works/doi:{DOI}`.
Add each kept item to `_data/ch6_publications.yml` (date, ref, url, type, avis citer | mentionner | suivre | écarter, ou = part and page, motif = one sentence in French with the number and its comparison point). Also add the main French and international institutional publications found in the step below. Items that touch no message are not listed. Do not edit `routines/flux.json`.

**Chapter 6 passages.** Open `_data/ch6.yml`. For each entry, search for publications since the entry's `maj_le` date that bear on its `message`, in this order: French institutions (CAE, Institut français d'économie (ex-OFCE and CEPII), IPP, Insee, Dares, DG Trésor, Banque de France, Conseil national de productivité, Haut-commissariat à la Stratégie et au Plan, Cour des comptes, Sénat and Assemblée reports, SGPI), international institutions (OECD, IMF, ECB, European Commission), then NBER/CEPR/SSRN working papers and journals. Rules:
- Keep a study only if it changes, confirms with new data, or contradicts the message, and only after reading the number in the source itself (page or URL). Never use a search snippet. At most two new items per entry per month.
- Edit only that entry: add the finding to `donnees` (one sentence, number with its comparison point and source), change `verdict` (tient | renforcé | nuancé | contredit | nouveau) only if the evidence clearly moves it, update `brouillon` (French, short sentences, French decimal comma, citations as « (Auteur, année) »), add the full reference to `references`, and set `maj_le` to today.
- Never add text from the textbook. The `message` field is a paraphrase; do not change it. Do not add new entries; propose them in the PR description instead.
- For competing positions in the public debate (part 4), add rows to `_data/ch6_partis.yml` (debat, position, qui, chiffre; `rapport: soutien` when the position agrees with the textbook).
- Do not edit charts, scripts or workflows.

In the pull request description, list each changed entry in one line (what changed and why) and flag any verdict change. If nothing new meets these rules, open no pull request and say so.
