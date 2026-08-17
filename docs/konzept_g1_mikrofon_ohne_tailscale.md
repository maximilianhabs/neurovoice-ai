# Konzept: Mikrofonzugriff lokal, ohne Abhängigkeit von unserer Tailscale-Infrastruktur (G1)

**Status (2026-08-17): Empfehlung UMGESETZT.** Erstellt auf Nutzer-Anfrage nach dem
Road-to-Public-Umbau — betrifft jetzt jede:n, der/die das öffentliche Repo klont und selbst
hostet, nicht mehr nur unseren eigenen Beelink-Server. Ursprünglich in `docs/backlog.md` als
G1 vermerkt (2026-08-16).

## ✅ Umsetzung (2026-08-17)

Die im Abschnitt „Empfehlung" unten skizzierte zweistufige Lösung ist umgesetzt:

1. **README-Hinweis zum Solo-Fall** — `localhost:8501` funktioniert bereits ohne HTTPS,
   direkt in der "Lokal starten"-Sektion dokumentiert.
2. **Option B (Caddy) als optionales Compose-Profil** — `dashboard/Caddyfile.local` +
   neuer `caddy`-Service in `dashboard/docker-compose.local.yml` hinter
   `profiles: ["https"]` (Default-Fall bleibt minimal, Caddy startet nur mit
   `--profile https`). Caddys lokale CA persistiert in einem eigenen Docker-Volume,
   README dokumentiert den einmaligen CA-Import je Plattform (macOS/Windows/Linux/
   mobiles Zweitgerät) über aufklappbare `<details>`-Blöcke.

**Echter Bug beim Verifizieren gefunden und behoben**: der ursprüngliche Catch-all-Listener
(`:8443` ohne festen Hostnamen) ließ den TLS-Handshake mit `"internal error"` fehlschlagen —
Caddy wusste ohne `on_demand`-Option nicht, für welchen Host/welche IP es ein Zertifikat
ausstellen soll, wenn der Listener selbst keinen festen Namen hat. Fix:
`tls internal { on_demand }`. Verifiziert per Standalone-Caddy-Container (ohne die schweren
WhisperX-Container zu bauen) gegen `localhost` UND eine simulierte fremde Adresse — beide
TLS-Handshakes erfolgreich, `502` danach nur weil in diesem isolierten Test kein echter
Dashboard-Container als Upstream lief (erwartetes Verhalten).

Optionen A/C/D/E unten bleiben als dokumentierte Alternativen bestehen, wurden nicht
implementiert (bewusst, siehe Begründung unten).

## Problem, präzise gefasst

Browser verweigern `getUserMedia` (Mikrofon-/Kamerazugriff) auf unverschlüsselten Origins.
Ausnahme laut [W3C Secure-Contexts-Spec](https://w3c.github.io/webappsec-secure-contexts/):
`http://localhost` (und `127.0.0.1`) gilt **immer** als sicherer Kontext, unabhängig von TLS.
**Jede andere Adresse** — private LAN-IP, Tailscale-IP, eigener Hostname — braucht echtes,
gültiges HTTPS, sonst bleibt der Aufnahme-Button tot (siehe `docs/bugtracker.md` BUG-15).

### Wichtige Klarstellung, bevor Lösungen bewertet werden

**Der reine Solo-Fall ist schon heute gelöst, ohne jede weitere Arbeit:** Wer
`docker-compose.local.yml` startet und im selben Browser auf demselben Rechner
`http://localhost:8501` öffnet, bekommt Mikrofonzugriff bereits jetzt — `localhost` ist per
Spezifikation ausgenommen. Das deckt vermutlich den häufigsten Einzel-Nutzer:innen-Fall ab
(eigener Laptop, eigene App, eigene Aufnahme).

**Die tatsächliche Lücke betrifft nur den Mehrgeräte-/Netzwerk-Fall**: der "Laptop zum
Patienten mitnehmen"-Anwendungsfall (siehe P0-Konzept), bei dem die App auf einem Server/
Rechner läuft und von einem ANDEREN Gerät im selben Netzwerk (Tablet, zweiter Laptop) über
dessen LAN-IP oder einen eigenen Hostnamen angesprochen wird — genau der Fall, für den wir
selbst bisher Tailscale genutzt haben. **Die Lösung muss also nicht jeden Nutzer betreffen,
sondern nur den, der die App netzwerkweit statt rein lokal betreiben will** — das verschiebt
die Priorität von "jeder braucht das sofort" zu "wichtig für den Mehrgeräte-Fall, dokumentiert
als optionaler Zusatzschritt".

## Optionen

### Option A — `mkcert` + Streamlits eigene SSL-Flags

Nutzer:in installiert [mkcert](https://github.com/FiloSottile/mkcert) einmalig lokal, führt
`mkcert -install` aus (installiert eine lokal vertrauenswürdige CA in den System-/Browser-
Truststore) und erzeugt dann ein Zertifikat für die eigenen Adressen:
`mkcert -cert-file cert.pem -key-file key.pem localhost 127.0.0.1 <eigene-LAN-IP>`.
Diese Dateien werden dem Streamlit-Prozess direkt übergeben:

```
--server.sslCertFile=cert.pem --server.sslKeyFile=key.pem
```

**Wichtiger Fund beim Gegenprüfen**: Streamlits eigene `--help`-Ausgabe (Version, die wir
einsetzen) warnt explizit: *"DO NOT USE THIS OPTION IN A PRODUCTION DEPLOYMENT. It is
recommended that you use a proxy for HTTPS."* — Streamlit selbst rät von dieser Option für
den produktiven Einsatz ab, empfiehlt stattdessen einen Reverse Proxy (→ Option B).

- **Aufwand**: gering, keine Code-/Compose-Änderung nötig, nur eine README-Anleitung.
- **Nachteil**: pro Betreiber:in ein manueller, einmaliger Terminal-Schritt AUSSERHALB von
  Docker (mkcert läuft auf dem Host, nicht im Container) — schlechter für Windows-Nutzer:innen,
  die evtl. gar kein Terminal gewohnt sind. Und: widerspricht Streamlits eigener Empfehlung.
- **Für wen geeignet**: technisch versierte Einzel-Betreiber:in, die schnell testen will.

### Option B — Caddy als Reverse Proxy mit automatischem lokalem HTTPS (empfohlen)

Ein zusätzlicher `caddy`-Service in `docker-compose.local.yml`, der VOR das Dashboard
geschaltet wird. Caddy kann seit Version 2 selbständig eine lokale CA erzeugen und Zertifikate
für `localhost`/beliebige interne Hostnamen ausstellen (`tls internal`-Direktive) — technisch
sehr ähnlich zu mkcert, aber komplett in Docker gekapselt, kein Host-Terminal-Schritt nötig.

Beispiel-`Caddyfile`:
```
:8443 {
    tls internal
    reverse_proxy neurovoice-dashboard:8501
}
```

Nutzer:in ruft dann `https://localhost:8443` auf. Beim allerersten Aufruf zeigt der Browser
eine Zertifikatswarnung (Caddys interne CA ist dem System-Truststore nicht automatisch
bekannt) — **außer** man exportiert Caddys Root-CA einmalig und importiert sie ins Betriebs-
system (ähnlicher manueller Schritt wie bei mkcert, aber nur EINMAL nötig, nicht pro Adresse).

- **Aufwand**: mittel — neuer Service in `docker-compose.local.yml`, ein `Caddyfile`, ein neuer
  Port. Für den Mehrgeräte-Fall zusätzlich: Caddy muss die tatsächliche LAN-IP/den Hostnamen
  kennen, den andere Geräte verwenden (Konfiguration nötig, nicht automatisch).
- **Vorteil**: läuft komplett innerhalb von Docker, plattformunabhängig, folgt Streamlits
  eigener Empfehlung (Reverse Proxy statt eingebautem SSL), kein Host-Terminal-Schritt.
- **Für wen geeignet**: Standard-Empfehlung für alle, die die App über mehr als `localhost`
  erreichen wollen — sollte der Default-Pfad in `docker-compose.local.yml` werden.

### Option C — Selbstsigniertes Zertifikat "ab Werk", ohne CA-Import

Ein beim ersten Start automatisch erzeugtes selbstsigniertes Zertifikat (z. B. per
`openssl req -x509 -newkey rsa:2048 -nodes ...` in einem Docker-Entrypoint-Skript), ohne
jeden manuellen CA-Trust-Schritt. Browser zeigen eine Sicherheitswarnung ("Diese Verbindung
ist nicht privat"), die man einmalig pro Gerät/Browser mit "Trotzdem fortfahren" bestätigt —
danach gilt die Seite technisch als sicherer HTTPS-Kontext (die Secure-Context-Prüfung fragt
nur nach dem Schema `https:`, nicht nach CA-Vertrauenswürdigkeit), `getUserMedia` funktioniert.

- **Aufwand**: am geringsten — keine externe Abhängigkeit (mkcert/Caddy), nur ein
  Entrypoint-Skript im bestehenden Dockerfile.
- **Nachteil**: schlechteste UX — jedes neue Gerät/jeder neue Browser sieht die
  Warnung erneut, wirkt für medizinisches/klinisches Personal evtl. unseriös/beunruhigend
  ("ist das sicher?"). Bei Zertifikatsablauf (falls eine Gültigkeitsdauer gesetzt wird)
  wiederholt sich die Warnung.
- **Für wen geeignet**: Notlösung/Fallback, nicht als Standardweg empfohlen.

### Option D — Tailscale weiterhin, aber als EINE dokumentierte Möglichkeit unter mehreren

Unsere eigene, bereits bewährte Lösung (`tailscale serve`) bleibt in der Doku als Option
stehen — für alle, die ohnehin schon ein (kostenloses) Tailscale-Konto haben oder eines
anlegen wollen. Kein Zwang mehr, aber auch kein Grund, sie zu verschweigen: liefert echtes,
von einer öffentlichen CA signiertes HTTPS ohne jede Zertifikatswarnung, geringster
Konfigurationsaufwand für alle, die sowieso VPN-Software wollen.

- **Für wen geeignet**: wer bereits im Tailscale-Ökosystem ist oder ein VPN für den
  Fernzugriff sowieso will (z. B. unser eigener Anwendungsfall).

### Option E — Öffentliche Domain + Let's Encrypt

Nur der Vollständigkeit halber aufgeführt, **nicht empfohlen als Standardweg**: würde eine
eigene Domain + offenen Port 80/443 zum Internet voraussetzen — steht im Widerspruch zum
lokalen/privaten Grundprinzip der App und würde `SECURITY.md`s aktuelle Warnung ("kein
Auth-Layer") von einer Betriebsempfehlung zu einem echten Sicherheitsrisiko machen. Nur
sinnvoll, wenn jemand ohnehin einen öffentlich erreichbaren Dienst bauen will UND vorher
einen eigenen Auth-Layer ergänzt (siehe `SECURITY.md`) — eigenes, größeres Vorhaben.

## Empfehlung

**Zweistufig dokumentieren, nichts erzwingen:**

1. **README ergänzen**: "Für die reine Einzelplatz-Nutzung (App und Browser auf demselben
   Rechner) funktioniert `http://localhost:8501` bereits ohne weitere Schritte." — behebt die
   Verwirrung für den häufigsten Fall sofort, ganz ohne Code-Änderung.
2. **Für den Mehrgeräte-Fall**: Option B (Caddy) als empfohlener Standardweg in
   `docker-compose.local.yml` ergänzen (auskommentiert/optional zuschaltbar, nicht
   erzwungen — nicht jede:r braucht das), mit README-Anleitung zum einmaligen CA-Import.
   Optionen A/C/E als Alternativen in der Doku erwähnen, nicht implementieren.

**Warum nicht Option A trotz geringstem Aufwand**: widerspricht Streamlits eigener
Produktionsempfehlung — ein Projekt, das gerade öffentlich wird, sollte nicht aktiv von der
eigenen Kernabhängigkeit abgeraten Praktiken empfehlen, wenn eine sauberere Alternative
(Option B) nur mäßig mehr Aufwand bedeutet.

**Warum nicht Option C als Standard trotz Einfachheit**: die Zertifikatswarnung bei jedem
neuen Gerät ist für den klinischen/medizinischen Kontext dieser App ein echter
Vertrauens-Malus — passt nicht zum sonstigen Anspruch ("seriöse, transparente Arbeit", siehe
`ROAD_TO_PUBLIC.md`).

## Offene Entscheidung (beim Nutzer)

- Zustimmung zur zweistufigen Empfehlung oben (README-Hinweis sofort + Caddy optional)?
- Soll Caddy fest in `docker-compose.local.yml` verankert werden (Default an) oder als
  separate, optionale Compose-Datei (`docker-compose.local-https.yml`, nur wer sie explizit
  aufruft bekommt den Caddy-Service)? Letzteres hält den einfachen Fall (`localhost`) minimal
  und fügt Komplexität nur hinzu, wenn tatsächlich gebraucht.
- Soll der Mehrgeräte-Fall (Caddy) schon jetzt umgesetzt werden, oder reicht vorerst der
  README-Hinweis zum bereits funktionierenden `localhost`-Fall (kleinster erster Schritt)?
