"""DB 액세스 레이어 (S1 · 04 3-1).

**스테이지는 DB 를 직접 만지지 않는다.** 여기를 거친다 (`pipeline.py:10` 규율).

    from app.db import retrieve

    cands = retrieve(user_id=1, max_missing=2)     # list[Candidate]

## 🔴 요청당 왕복 1회

`retrieve_for_user()` 가 SQL 함수 하나로 끝나도록 설계돼 있다 (01 1-7).
스테이지마다 따로 조회하면 **왕복 횟수만큼 RTT 가 곱해지고**,
로컬에서는 티가 안 나다가 원격 DB 로 옮기는 순간 드러난다 (06 8-D).
"""
from .pool import close_pool, cursor, healthy
from .retrieval import retrieve, retrieve_raw

__all__ = ["cursor", "close_pool", "healthy", "retrieve", "retrieve_raw"]
