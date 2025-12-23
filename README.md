# ch.grischamedia.inventree.bulkproducts

InvenTree Plugin zum **Erstellen mehrerer Teile** (und perspektivisch: **direktes Einbuchen**) in einem Schritt.

Aktuell enthält das Repo ein startfähiges Plugin-Skeleton für **InvenTree stable (>= 1.1.7)**:

- **SettingsMixin**: erste Admin-Settings (z.B. Default-Location)
- **ActionMixin**: erste Action als **Dry-Run** (keine Side-Effects)

## Installation (Development)

Im gleichen Python-Environment wie dein InvenTree-Server:

```bash
pip install -e .
```

Danach InvenTree neu starten und im Admin unter **Plugin Settings** aktivieren.

## Erste Action testen (Dry-Run)

POST an `/api/action/` (auth nötig):

```json
{
  "action": "bulkproducts.dry_run",
  "data": {
    "parts": [
      { "name": "Widget A", "ipn": "W-A", "description": "Test", "quantity": 10 },
      { "name": "Widget B", "ipn": "W-B", "quantity": 0 }
    ]
  }
}
```

Die Response enthält `result` + `info.plan`, also was der Import später tun würde.
