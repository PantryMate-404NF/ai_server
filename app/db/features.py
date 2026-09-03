"""피처 로딩 — S3 에서 채운다. 지금은 자리만 잡아둔다.

⚠️ 여기를 채울 때 **후보 N개를 N번 조회하면 안 된다**. `WHERE recipe_id = ANY(%s)`
   한 번으로 끝내야 요청당 왕복 1회가 유지된다 (01 1-7).
"""
from __future__ import annotations

__all__: list[str] = []
