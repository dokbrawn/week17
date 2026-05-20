
import json
import os
from pathlib import Path


def student_id():
    return os.getenv('STUDENT_ID', 's01')


def student_group():
    return os.getenv('GROUP', '431')


def repo_root():
    return Path(__file__).resolve().parents[1]


def variant_path(week: str) -> Path:
    sid = student_id()
    grp = student_group()
    return repo_root() / 'variants' / grp / sid / f"week-{week}.json"


def load_variant(week: str) -> dict:
    path = variant_path(week)
    if not path.exists():
        raise FileNotFoundError(f"Variant not found: {path}")
    v = json.loads(path.read_text())
    print(f"\nСтудент: {v['student_id']} | Группа: {v['group']} | Ресурс: {v.get('resource', 'N/A')}")
    return v
