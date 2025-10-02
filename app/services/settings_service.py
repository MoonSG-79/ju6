
import json
from app.core.db import get_session, Setting

def save_settings(d: dict):
    with get_session() as s:
        s.merge(Setting(key="ui_settings", value=json.dumps(d, ensure_ascii=False))); s.commit()

def load_settings() -> dict:
    with get_session() as s:
        row = s.get(Setting, "ui_settings")
        return json.loads(row.value) if row and row.value else {}
