---
name: eisenhower-inbox
description: Klassifiziert eingehende E-Mails nach der Eisenhower-Matrix (dringend/wichtig) und erstellt daraus ein HTML-Briefing. Verwende diesen Skill, wenn der Nutzer E-Mails priorisieren, den Posteingang triagieren, ein Pendenzen-Briefing erstellen oder wissen will, welche Mails er sofort erledigen, einplanen, delegieren oder ignorieren soll.
---

# Eisenhower Inbox Triage

Klassifiziert E-Mails aus Sicht des CEO einer Immobilienentwicklungs- und
Investment-Gruppe in die vier Eisenhower-Quadranten und gibt ein
Outlook-taugliches HTML-Briefing aus.

## Quadranten-Definitionen

| Quadrant | Kriterium | Aktion |
|---|---|---|
| Q1 | dringend & wichtig | sofort erledigen |
| Q2 | wichtig, nicht dringend | terminieren |
| Q3 | dringend, nicht wichtig | delegieren |
| Q4 | weder noch | eliminieren |

- **dringend** = Handlung innert ~48 h nötig, sonst Schaden/Fristverfall.
- **wichtig** = wesentlicher Einfluss auf Vermögenswerte, Projekte,
  rechtliche Pflichten oder strategische Ziele.
- Künstliche Verknappung in Werbemails ("nur noch heute!") zählt **nicht**
  als dringend.

## Workflow

1. E-Mails als `.txt` (RFC-822-ähnlich: `From:`, `Subject:`, Body) in
   `sample_emails/` ablegen.
2. `python classify_emails.py` ausführen (benötigt `ANTHROPIC_API_KEY`).
3. Ergebnis: `output/briefing.html` — sortiert Q1 → Q4, pro Mail mit
   Zusammenfassung, Begründung, erkannter Frist und konkretem nächsten
   Schritt.

## Output-Regeln

- HTML muss E-Mail-Client-sicher sein: Tabellen-Layout, Inline-CSS,
  kein Flexbox/Grid (Outlook-Kompatibilität).
- Jede Klassifikation enthält eine kurze Begründung — keine Blackbox.
- Bei unklarer Wichtigkeit konservativ einstufen (eher Q2 als Q4),
  damit nichts Geschäftskritisches verloren geht.
