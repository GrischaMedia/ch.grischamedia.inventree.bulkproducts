# ch.grischamedia.inventree.bulkproducts

InvenTree Plugin zum **Erstellen mehrerer Teile** (und optional: **direktes Einbuchen**) in einem Schritt.

## Funktion

- Stellt eine Seite bereit unter: **`/plugin/bulk-products/`** (Trailing Slash wichtig)
- Dort können mehrere neue Teile in einer Tabelle erfasst werden:
  - Kategorie (Pflicht)
  - Name (Pflicht)
  - Beschreibung (optional)
  - IPN (optional)
  - Anzahl Produkte (optional, für Einbuchen)
  - Lagerort (optional, für Einbuchen)
- Optionales Einbuchen:
  - Wenn **Anzahl > 0**, wird ein StockItem am gewählten Lagerort erstellt
  - Wenn kein Lagerort gewählt ist, wird nicht eingebucht (oder es wird der Default-Standort aus den Plugin-Settings verwendet)

## Plugin Settings

- **ALLOW_CREATE**: muss aktiv sein, damit das Plugin Daten anlegen darf
- **DEFAULT_STOCK_LOCATION_ID**: optionaler Default-Lagerort (DB-ID) für Einbuchen, wenn pro Zeile kein Lagerort gewählt wird

## Installation (Development)

Im gleichen Python-Environment wie dein InvenTree-Server:

```bash
pip install -e .
```

Danach InvenTree neu starten und im Admin unter **Plugin Settings** aktivieren.

## Installation (Production / Docker / Portainer)

Voraussetzung:

- In InvenTree ist **Plugin Support** aktiv
- In der Server-Konfiguration ist **ENABLE_PLUGINS_URL** aktiv, damit `/plugin/...` erreichbar ist

### Variante A: Installation über InvenTree UI

- In InvenTree als Admin: **Settings → Plugin Settings**
- Plugin installieren (z.B. via Git URL oder Paketname)
- **Server & Worker neu starten**

### Variante B: Installation per `plugins.txt`

InvenTree kann Plugins beim Start automatisch installieren, wenn **Check Plugins on Startup** aktiv ist.

1. In deinem InvenTree Config-Verzeichnis eine `plugins.txt` anlegen/erweitern (Pfad abhängig von deiner Installation)
2. Eintrag hinzufügen (Beispiele):
   - VCS-Install (latest): `git+https://github.com/GrischaMedia/ch.grischamedia.inventree.bulkproducts.git@master`
   - Pin auf Tag/Commit: `git+https://github.com/GrischaMedia/ch.grischamedia.inventree.bulkproducts.git@<tag-oder-commit>`
3. Container neu starten

### Portainer (Stack)

Allgemeines Vorgehen (abhängig von deinem InvenTree Stack):

- **plugins.txt persistieren** (Volume/Bind-Mount), damit sie Container-Neustarts überlebt
- In Portainer: Stack → **Editor** → bei `inventree-server` und `inventree-worker` sicherstellen:
  - gleiches Plugin-Install-Verhalten (beide brauchen Plugin verfügbar)
  - nach Änderung: **Re-deploy**
- In InvenTree UI: **Check Plugins on Startup** aktivieren
- Danach Plugin in **Plugin Settings** aktivieren und beide Services neu starten

## Nutzung

Öffne die Seite:

- `https://<dein-host>/plugin/bulk-products/`

Wichtig:

- Pflichtfelder sind **Kategorie** und **Name**
- Einbuchen passiert nur, wenn **Anzahl > 0** und ein Lagerort (oder Default) vorhanden ist

## Roadmap (Phase 2)

- Labels drucken: Auswahl per Checkbox + Öffnen des InvenTree Label-Dialogs (Layout/Drucker wählen) für die neu erstellten Teile

## Beispiel: pip install direkt von GitHub (master)

```bash
pip install --no-cache-dir git+https://github.com/GrischaMedia/ch.grischamedia.inventree.bulkproducts.git@master
```

