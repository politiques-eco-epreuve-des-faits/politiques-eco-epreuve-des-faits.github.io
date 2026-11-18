# Routine mensuelle : textes de la veille (repo ajoly35/veille-politiques-economiques)

Proposition de routine cloud (claude.ai/code/routines), à créer avec l'accord d'Adrien.
Calendrier proposé : le 16 de chaque mois, 05:30 UTC, sur le repo `ajoly35/veille-politiques-economiques`.
Elle ouvre une pull request ; elle ne pousse jamais sur `main`. Fusionner la PR = publier.
Les graphiques OCDE sont actualisés à part par `.github/workflows/charts.yml` (le 2 du mois).

---

## Prompt (à coller dans la routine)

You maintain a public tracker for the next edition of a French economics textbook. Work only on this repository.
Create a branch `claude/veille-YYYY-MM`, make the changes below, and open a pull request. Never push to `main`.

**Chapter 6 passages.** Open `_data/ch6.yml`. For each entry, search for publications since the entry's `maj_le` date that bear on its `message`, in this order: French institutions (CAE, Institut français d'économie (ex-OFCE and CEPII), IPP, Insee, Dares, DG Trésor, Banque de France, Conseil national de productivité, Haut-commissariat à la Stratégie et au Plan, Cour des comptes, Sénat and Assemblée reports, SGPI), international institutions (OECD, IMF, ECB, European Commission), then NBER/CEPR/SSRN working papers and journals. Rules:
- Keep a study only if it changes, confirms with new data, or contradicts the message, and only after reading the number in the source itself (page or URL). Never use a search snippet. At most two new items per entry per month.
- Edit only that entry: add the finding to `donnees` (one sentence, number with its comparison point and source), change `verdict` (tient | renforcé | nuancé | contredit | nouveau) only if the evidence clearly moves it, update `brouillon` (French, short sentences, French decimal comma, citations as « (Auteur, année) »), add the full reference to `references`, and set `maj_le` to today.
- Never add text from the textbook. The `message` field is a paraphrase; do not change it. Do not add new entries; propose them in the PR description instead.
- For competing positions in the public debate (part 4), add rows to `_data/ch6_partis.yml` (debat, position, qui, chiffre; `rapport: soutien` when the position agrees with the textbook).
- Do not edit charts, scripts or workflows.

In the pull request description, list each changed entry in one line (what changed and why) and flag any verdict change. If nothing new meets these rules, open no pull request and say so.
