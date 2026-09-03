"""상태 확인.

⬜ 규칙 7.2 는 `/health/live`(프로세스)와 `/health/ready`(초기화 완료)로
   나누라고 한다. 지금은 `/health` 하나다 — 나누면 계약이 바뀌므로
   `app/schemas/api.py` 와 `docs/05_API_명세.md` 를 함께 고쳐야 한다 (미합의).
"""
from fastapi import APIRouter

from ..schemas import HealthOut
from ..services.recommends import mock

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    return mock.health_payload()
