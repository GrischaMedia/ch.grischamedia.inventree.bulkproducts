# ch.grischamedia.inventree.bulkproducts

InvenTree Plugin zum **Erstellen mehrerer Teile** (und optional: **direktes Einbuchen**) in einem Schritt.

## Funktion

Das Plugin stellt eine Seite bereit unter: **`/plugin/bulk-products/`** (Trailing Slash wichtig)

Auf dieser Seite können mehrere neue Teile in einer Tabelle erfasst werden:

- **Kategorie** (Pflicht)
- **Name** (Pflicht)
- **Beschreibung** (optional)
- **IPN** (optional)
- **Anzahl Produkte** (optional, für Einbuchen)
- **Lagerort** (optional, für Einbuchen - dynamisches Suchfeld)

### Features

- Massenerstellung von Teilen in einer Tabelle
- Optionales direktes Einbuchen in Lagerorte
- Dynamisches Suchfeld für Lagerorte (wie in InvenTree)
- Label-Druck für erstellte Produkte
- Checkbox-Auswahl für zu druckende Labels

### Optionales Einbuchen

- Wenn **Anzahl > 0**, wird ein StockItem am gewählten Lagerort erstellt
- Wenn kein Lagerort gewählt ist, wird nicht eingebucht (oder es wird der Default-Standort aus den Plugin-Settings verwendet)

### Label-Druck

Nach dem Erstellen von Produkten können diese per Checkbox ausgewählt und mit dem "Labels drucken" Button gedruckt werden. Es öffnet sich der InvenTree Label-Dialog, in dem Layout und Drucker gewählt werden können.

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

1. **plugins.txt persistieren** (Volume/Bind-Mount), damit sie Container-Neustarts überlebt
2. In Portainer: Stack → **Editor** → bei `inventree-server` und `inventree-worker` sicherstellen:
   - gleiches Plugin-Install-Verhalten (beide brauchen Plugin verfügbar)
   - nach Änderung: **Re-deploy**
3. In InvenTree UI: **Check Plugins on Startup** aktivieren
4. Danach Plugin in **Plugin Settings** aktivieren und beide Services neu starten

#### Beispiel für Portainer Stack (docker-compose.yml)

```yaml
services:
  inventree-server:
    volumes:
      - ./plugins.txt:/data/plugins.txt
    environment:
      - INVENTREE_PLUGINS_ENABLED=true
      - INVENTREE_PLUGINS_FILE=/data/plugins.txt

  inventree-worker:
    volumes:
      - ./plugins.txt:/data/plugins.txt
    environment:
      - INVENTREE_PLUGINS_ENABLED=true
      - INVENTREE_PLUGINS_FILE=/data/plugins.txt
```

In der `plugins.txt`:
```
git+https://github.com/GrischaMedia/ch.grischamedia.inventree.bulkproducts.git@master
```

## Nutzung

Öffne die Seite:

- `https://<dein-host>/plugin/bulk-products/`

Wichtig:

- Pflichtfelder sind **Kategorie** und **Name**
- Einbuchen passiert nur, wenn **Anzahl > 0** und ein Lagerort (oder Default) vorhanden ist
- Lagerort kann über das dynamische Suchfeld gesucht werden
- Nach dem Erstellen können Produkte per Checkbox ausgewählt und Labels gedruckt werden

## Beispiel: pip install direkt von GitHub (master)

```bash
pip install --no-cache-dir git+https://github.com/GrischaMedia/ch.grischamedia.inventree.bulkproducts.git@master
```

## Autor

GrischaMedia.ch

## Lizenz

MIT
