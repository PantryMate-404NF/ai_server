"""HTTP 엔드포인트. 규칙 4절 — **여기서는 데이터 가공을 하지 않는다.**

스키마 검증(FastAPI 가 한다) → 서비스 호출 → 상태코드 결정. 그게 전부다.
파일은 기능 단위로 나눈다 (규칙 4절: 기능 이름 = 파일 이름 = 담당자).
"""
from . import events, health, onboarding, pantry, recommend, search  # noqa: F401

ROUTERS = (
    health.router, recommend.router, events.router,
    search.router, pantry.router, onboarding.router,
)
