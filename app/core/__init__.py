"""S2 로그 쓰기 경로 (04 3-1).

    from app.core import write_recommendation, counters

    write_recommendation(req, resp, scored=scored, pantry_ids=pids)

## 🔴 로그는 소급이 안 된다

`recipe_ingredient_raw` 는 원문이 남아 사전을 고치면 재정규화된다. **로그에는
그런 장치가 없다.** 서빙 순간에만 존재하는 값(propensity·features·서빙 시점의
pantry)은 그 요청이 지나가면 어떤 백필로도 복원되지 않는다.

## 🔴 로그 실패가 추천을 실패시키지 않는다

그렇다고 조용히 삼키면 데이터가 비어가는 것을 아무도 모른다. 그래서
**삼키되 반드시 센다** — `counters()` 가 대시보드/`/health` 로 나간다.
"""
from .counters import counters, reset_counters
from .writer import write_recommendation

__all__ = ["write_recommendation", "counters", "reset_counters"]
