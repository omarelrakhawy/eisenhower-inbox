# Eisenhower Inbox Triage — Mini-Claude-Skill

Arbeitsprobe für das Praktikum **AI Workflow Engineer** bei aestate.

Klassifiziert drei Beispiel-E-Mails (Immobilien-Kontext) nach der
Eisenhower-Matrix via Claude API und rendert das Ergebnis als
Outlook-taugliche HTML-Mail.

## Quickstart

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python classify_emails.py
open output/briefing.html
```

## Projektstruktur

```
eisenhower-skill/
├── SKILL.md              # Claude-Skill-Definition (Trigger, Regeln, Workflow)
├── classify_emails.py    # CLI: laden → klassifizieren → HTML rendern
├── sample_emails/        # 3 Beispiel-Mails (Q1, Q2, Q4-Kandidaten)
├── output/               # generiertes Briefing
└── requirements.txt
```

## Design-Entscheidungen

**Prompt:** Die Klassifikation erfolgt explizit *aus CEO-Sicht einer
Immobiliengruppe* mit operationalisierten Definitionen (dringend = Handlung
innert ~48 h, wichtig = Einfluss auf Vermögenswerte/Pflichten/Strategie).
Ohne diese Verankerung schwankt das Modell bei Grenzfällen. Eine Regel
fängt den klassischen Fehlklassifikations-Fall ab: künstliche Verknappung
in Werbemails ("nur noch heute!") gilt nicht als dringend.

**Strukturierter Output:** Claude antwortet als reines JSON
(Quadrant, Summary, Begründung, Frist, nächster Schritt). Das macht den
Output maschinell weiterverarbeitbar — z. B. später für eine
Power-Automate-Anbindung. Code-Fences werden defensiv entfernt,
ungültiges JSON führt zu einem klaren Fehler statt stillem Raten.

**HTML-Mail statt HTML-Seite:** Tabellen-Layout und Inline-CSS, kein
Flexbox/Grid — Outlook rendert mit der Word-Engine und ignoriert moderne
CSS-Layouts. Sortierung Q1 → Q4, damit das Dringendste oben steht.

**SKILL.md:** Die Logik ist zusätzlich als Claude Skill dokumentiert
(Frontmatter mit Trigger-Beschreibung + Regeln im Body), sodass derselbe
Workflow auch agentisch — von Claude selbst — ausgeführt werden kann,
nicht nur als Script.

## Bewusste Vereinfachungen (2–3 h Scope)

- E-Mails als `.txt`-Dateien statt Live-Anbindung an Outlook/Graph API —
  der nächste reale Schritt wäre ein MCP-Server auf Microsoft Graph.
- Eine API-Anfrage pro E-Mail statt Batching — bei 3 Mails irrelevant,
  bei echtem Posteingangsvolumen würde ich batchen und parallelisieren.
- Kein Retry/Rate-Limit-Handling, keine Tests — in Produktion Pflicht.
