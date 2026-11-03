import json
from datetime import datetime, date
from typing import Any

def json_serializer(obj: Any) -> Any:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def safe_json_loads(data: Any, default: Any = None) -> Any:
    if data is None:
        return default
    if isinstance(data, (dict, list)):
        return data
    try:
        return json.loads(data)
    except Exception:
        return default

def safe_json_dumps(data: Any) -> str:
    if data is None:
        return "[]" if isinstance(data, list) else "{}"
    if isinstance(data, str):
        return data
    try:
        return json.dumps(data, default=json_serializer)
    except Exception:
        return "{}"
