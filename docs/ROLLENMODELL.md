# Rollenmodell

## Startrollen

| Rolle | Rechte |
| --- | --- |
| Admin | darf Benutzer verwalten und alle Termine bearbeiten |
| Nutzer | darf Termine ansehen und eigene Termine erstellen/bearbeiten |
| Gast | darf Termine ansehen, aber nichts bearbeiten |

## Technischer Ansatz

Fuer den Anfang reicht ein Rollenfeld am Benutzer:

```text
role = admin | user | guest
```

Die Rechte werden zentral in Hilfsfunktionen geprueft. Dadurch muss die Logik
nicht an vielen Stellen doppelt geschrieben werden.

## Beispiel

```python
def is_admin(user):
    # Nur angemeldete Benutzer mit Admin-Rolle sind Admins.
    return user.is_authenticated and user.role == "admin"


def can_edit_event(user, event):
    # Admins duerfen jeden Termin bearbeiten.
    if is_admin(user):
        return True

    # Normale Nutzer duerfen eigene Termine bearbeiten.
    if user.is_authenticated and user.role == "user":
        return event.created_by_id == user.id

    # Gaeste duerfen nicht bearbeiten.
    return False
```

## Spaetere Erweiterung

Wenn die Rechte feiner werden, koennen Django-Gruppen und einzelne Berechtigungen
ergänzt werden. Das einfache Rollenfeld bleibt trotzdem als gut verstaendliche
Grundlage nutzbar.
