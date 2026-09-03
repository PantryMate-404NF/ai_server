"""① Retrieval — SQL 함수를 파이썬 계약으로 옮긴다.

여기가 하는 일은 **번역뿐**이다. 필터링 로직은 전부 SQL 안에 있다
(`db/init/04_functions.sql`). 파이썬에서 한 번 더 거르면 두 곳이 어긋난다.

    from app.db import retrieve
    cands = retrieve(user_id=1, max_missing=2)   # list[Candidate]
"""
from __future__ import annotations

from app.schemas.pipeline import Candidate, RetrievalRequest

from .pool import cursor

#: 🔴 ① 은 넉넉히 뽑고 ②③ 에서 좁힌다. 500 은 p95 30.2ms 로 실측된 값
#:    (06 8-A). 늘리면 ② 의 파이썬 점수 계산이 선형으로 늘어난다.
DEFAULT_LIMIT = 500

_SQL = "SELECT * FROM retrieve_for_user(%s, %s, %s, %s, %s)"


def retrieve_raw(
    user_id: int,
    max_missing: int = 2,
    max_minutes: int | None = None,
    limit: int = DEFAULT_LIMIT,
    include_test: bool = False,
) -> list[tuple]:
    """SQL 원본 행. 스모크·벤치가 계약 변환 없이 쓰려고 남겨둔다.

    🔴 `include_test` 는 **테스트 전용**이다. `feature_version='test-*'` 인 합성
       피처까지 본다. 기본이 False 라 서빙 경로는 켤 수 없다 — B·C 가 넣은
       합성 5만 건이 실추천에 섞이는 것을 구조로 막는다.

    인자는 계약(`RetrievalRequest`)으로 검증한다 — 상한을 여기 다시 적으면
    두 곳이 어긋난다.
    """
    q = RetrievalRequest(user_id=user_id, max_missing=max_missing,
                         max_minutes=max_minutes, limit=limit)
    with cursor() as cur:
        cur.execute(_SQL, (q.user_id, q.max_missing, q.max_minutes, q.limit, include_test))
        return cur.fetchall()


def retrieve(
    user_id: int,
    max_missing: int = 2,
    max_minutes: int | None = None,
    limit: int = DEFAULT_LIMIT,
    include_test: bool = False,
) -> list[Candidate]:
    """① 산출. **점수는 아직 없다** — ② Ranking 이 매긴다.

    `max_missing` 은 요청마다 바뀔 수 있다 (사용자가 "재료 더 사도 됨" 을 켜는 경우).
    그래서 기본값을 상수로 박지 않고 인자로 받는다. 실제로 쓰인 값은
    `recommendation_log.policies` 에 실려야 재현이 된다 (S0 ① REQUIRED_TRACE_PARAMS).
    """
    return [
        Candidate(
            recipe_id=r[0],
            missing_count=r[1],
            # 🔴 SQL 이 NULL 을 줄 수 있다 (부족 재료가 없는 경우 빈 배열이 아니라 NULL).
            missing_ids=list(r[2] or []),
            coverage=float(r[3]),
            # SMALLINT → int. NULL 이면 클러스터링 배치 전이므로 균등 탐색 폴백.
            cluster_id=None if r[4] is None else int(r[4]),
        )
        for r in retrieve_raw(user_id, max_missing, max_minutes, limit, include_test)
    ]
