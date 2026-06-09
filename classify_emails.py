#!/usr/bin/env python3
"""Eisenhower email classifier.

Reads sample emails, classifies each into an Eisenhower-matrix quadrant
via the Claude API, and renders the result as an email-client-safe HTML mail.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python classify_emails.py [--emails-dir sample_emails] [--out output/briefing.html]
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date
from email.parser import Parser
from pathlib import Path

import anthropic

MODEL = "claude-sonnet-4-5"

QUADRANTS = {
    "Q1": {"label": "Sofort erledigen", "sub": "dringend & wichtig", "color": "#C0392B"},
    "Q2": {"label": "Einplanen", "sub": "wichtig, nicht dringend", "color": "#1E6E42"},
    "Q3": {"label": "Delegieren", "sub": "dringend, nicht wichtig", "color": "#B97A0E"},
    "Q4": {"label": "Eliminieren", "sub": "weder dringend noch wichtig", "color": "#6B7280"},
}

SYSTEM_PROMPT = """\
Du bist ein Assistent für das Management einer Zürcher Immobilienentwicklungs- \
und Investment-Gruppe. Du klassifizierst eingehende E-Mails nach der \
Eisenhower-Matrix aus Sicht des CEO.

Definitionen:
- dringend: erfordert Handlung innert ~48 Stunden, sonst entsteht Schaden \
oder eine Frist verfällt.
- wichtig: hat wesentlichen Einfluss auf Vermögenswerte, laufende Projekte, \
rechtliche Pflichten oder strategische Ziele der Gruppe.

Quadranten:
- Q1: dringend und wichtig (sofort erledigen)
- Q2: wichtig, nicht dringend (terminieren)
- Q3: dringend, nicht wichtig (delegieren)
- Q4: weder dringend noch wichtig (eliminieren/ignorieren)

Künstliche Verknappung in Werbemails ("nur noch heute!") macht eine E-Mail \
nicht dringend im Sinne der Matrix.

Antworte ausschliesslich mit einem JSON-Objekt, ohne Markdown-Codeblöcke:
{
  "quadrant": "Q1" | "Q2" | "Q3" | "Q4",
  "urgent": true | false,
  "important": true | false,
  "summary": "Ein Satz: worum geht es?",
  "reasoning": "Ein bis zwei Sätze: warum dieser Quadrant?",
  "next_action": "Konkrete empfohlene nächste Handlung, max. ein Satz.",
  "deadline": "Erkannte Frist als Text oder null"
}"""


@dataclass
class Email:
    filename: str
    sender: str
    subject: str
    body: str


@dataclass
class Classification:
    email: Email
    quadrant: str
    summary: str
    reasoning: str
    next_action: str
    deadline: str | None


def load_emails(emails_dir: Path) -> list[Email]:
    emails = []
    for path in sorted(emails_dir.glob("*.txt")):
        msg = Parser().parse(path.open(encoding="utf-8"))
        emails.append(
            Email(
                filename=path.name,
                sender=msg.get("From", "unbekannt"),
                subject=msg.get("Subject", "(kein Betreff)"),
                body=msg.get_payload().strip(),
            )
        )
    if not emails:
        sys.exit(f"Keine .txt-Dateien in {emails_dir} gefunden.")
    return emails


def classify(client: anthropic.Anthropic, email: Email) -> Classification:
    user_msg = (
        f"Von: {email.sender}\n"
        f"Betreff: {email.subject}\n\n"
        f"{email.body}"
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text.strip()
    # Defensive: strip code fences if the model adds them despite instructions.
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"Antwort für {email.filename} ist kein gültiges JSON: {e}\n{raw}")

    quadrant = data.get("quadrant")
    if quadrant not in QUADRANTS:
        sys.exit(f"Unbekannter Quadrant '{quadrant}' für {email.filename}.")

    return Classification(
        email=email,
        quadrant=quadrant,
        summary=data.get("summary", ""),
        reasoning=data.get("reasoning", ""),
        next_action=data.get("next_action", ""),
        deadline=data.get("deadline"),
    )


def render_html(results: list[Classification]) -> str:
    """Render an email-client-safe HTML mail (tables + inline CSS, no flexbox/grid),
    so it displays correctly in Outlook."""
    order = {"Q1": 0, "Q2": 1, "Q3": 2, "Q4": 3}
    results = sorted(results, key=lambda r: order[r.quadrant])

    cards = []
    for r in results:
        q = QUADRANTS[r.quadrant]
        deadline_row = (
            f'<tr><td style="padding:2px 0;font-size:13px;color:#374151;">'
            f"<strong>Frist:</strong> {r.deadline}</td></tr>"
            if r.deadline
            else ""
        )
        cards.append(f"""
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="margin:0 0 16px 0;border:1px solid #E5E7EB;border-left:5px solid {q['color']};
                    border-radius:6px;background:#FFFFFF;">
        <tr>
          <td style="padding:14px 18px;font-family:Arial,Helvetica,sans-serif;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="font-size:12px;font-weight:bold;color:{q['color']};
                           text-transform:uppercase;letter-spacing:0.5px;padding-bottom:6px;">
                  {r.quadrant} &middot; {q['label']} <span style="color:#6B7280;font-weight:normal;
                  text-transform:none;letter-spacing:0;">({q['sub']})</span>
                </td>
              </tr>
              <tr><td style="font-size:15px;font-weight:bold;color:#111827;padding-bottom:2px;">
                {r.email.subject}</td></tr>
              <tr><td style="font-size:12px;color:#6B7280;padding-bottom:8px;">
                {r.email.sender}</td></tr>
              <tr><td style="font-size:13px;color:#374151;padding:2px 0;">{r.summary}</td></tr>
              <tr><td style="font-size:13px;color:#6B7280;padding:2px 0;font-style:italic;">
                {r.reasoning}</td></tr>
              {deadline_row}
              <tr><td style="font-size:13px;color:#111827;padding-top:8px;">
                <strong>&#10148; Nächster Schritt:</strong> {r.next_action}</td></tr>
            </table>
          </td>
        </tr>
      </table>""")

    today = date.today().strftime("%d.%m.%Y")
    return f"""<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"><title>Posteingang-Briefing {today}</title></head>
<body style="margin:0;padding:0;background:#F3F4F6;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F3F4F6;">
    <tr><td align="center" style="padding:24px 12px;">
      <table role="presentation" width="620" cellpadding="0" cellspacing="0" style="max-width:620px;width:100%;">
        <tr><td style="font-family:Arial,Helvetica,sans-serif;padding-bottom:16px;">
          <span style="font-size:20px;font-weight:bold;color:#111827;">Posteingang-Briefing</span><br>
          <span style="font-size:13px;color:#6B7280;">{len(results)} E-Mails klassifiziert
          nach Eisenhower-Matrix &middot; {today}</span>
        </td></tr>
        <tr><td>{''.join(cards)}</td></tr>
        <tr><td style="font-family:Arial,Helvetica,sans-serif;font-size:11px;color:#9CA3AF;padding-top:8px;">
          Automatisch erstellt mit Claude ({MODEL}).
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emails-dir", type=Path, default=Path("sample_emails"))
    parser.add_argument("--out", type=Path, default=Path("output/briefing.html"))
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY ist nicht gesetzt.")

    client = anthropic.Anthropic()
    emails = load_emails(args.emails_dir)

    results = []
    for email in emails:
        print(f"Klassifiziere {email.filename} …", end=" ", flush=True)
        result = classify(client, email)
        print(f"{result.quadrant} ({QUADRANTS[result.quadrant]['label']})")
        results.append(result)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_html(results), encoding="utf-8")
    print(f"\nHTML-Mail geschrieben: {args.out}")


if __name__ == "__main__":
    main()
