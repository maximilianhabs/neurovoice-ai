# Security Policy

## Zugriffsmodell — bitte vor dem Betrieb lesen

**NeuroVoice AI hat aktuell keinen eigenen Auth-Layer** — kein Login, keine Benutzerkonten,
keine Rollen, kein Zugriffsprotokoll. Die einzige Zugriffskontrolle ist das Netzwerk selbst:
in der Referenz-Installation läuft das Dashboard hinter einem [Tailscale](https://tailscale.com/)-
VPN und ist nur innerhalb des eigenen Tailnets erreichbar (siehe `dashboard/docker-compose.yml`,
`NEUROVOICE_BIND_ADDR`). Wer Zugriff auf dieses Netzwerk hat, hat vollen Zugriff auf die App —
inklusive aller zugeordneten Proband:innen-IDs, Altersangaben und Aufnahmen/Analysen.

**Konsequenzen für den eigenen Betrieb:**

- Niemals ohne VPN/Reverse-Proxy-Zugriffsschutz direkt am offenen Internet betreiben.
- Keine Mehrbenutzer-Trennung: jede Person mit Netzwerkzugriff sieht potenziell alle
  Proband:innen-Sitzungen (`derived/_sessions/`, `derived/_subjects/`), nicht nur eigene.
- Kein Audit-Log, wer wann welche Daten eingesehen hat.
- Mikrofon-/Kamera-Zugriff im Browser braucht ohnehin einen sicheren Kontext (HTTPS) — siehe
  `docs/bugtracker.md` BUG-15 zur eigenen Tailscale-Serve-Einrichtung als ein möglicher Weg dahin.

Wer die App für einen echten klinischen/mehrbenutzerfähigen Einsatz braucht, muss selbst einen
Auth-/Autorisierungs-Layer davorsetzen (z. B. über einen Reverse Proxy mit Basic Auth/OAuth2-Proxy)
oder die App entsprechend erweitern — beides ist aktuell **nicht** Teil dieses Projekts.

## Gemeldete Schwachstellen

Bitte **keine** Sicherheitslücken als öffentliches GitHub-Issue melden. Stattdessen über
GitHub Security Advisories (Tab „Security“ → „Report a vulnerability“) oder per E-Mail an die
im Profil des Maintainers hinterlegte Adresse.

Enthält die Meldung selbst sensible Daten (z. B. reale Proband:innen-Informationen), bitte
diese vorher entfernen/anonymisieren — siehe auch `CONTRIBUTING.md`.

## Umgang mit Proband:innen-Daten

Die App sammelt bewusst **keine** Namen/Initialen, nur eine pseudonyme ID + Alter
(`core/subject_store.py`). Eine Re-Identifizierung (welche ID zu welcher realen Person gehört)
liegt außerhalb der App bei der behandelnden/aufnehmenden Person. Trotzdem gilt: Audio-Aufnahmen
von Sprache sind potenziell selbst identifizierend (Stimme) — die App ersetzt keine
datenschutzrechtliche Einordnung durch die Betreiber:in vor Ort.
