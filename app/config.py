"""환경변수 → 설정. 규칙 7.6 — 매직 넘버를 코드에 박지 않는다.

    from .config import settings
    settings.pg_max_conn

🔴 **비밀값은 여기 기본값으로 두지 않는다.** `.env` 에만 두고 환경변수로 읽는다.
   특히 `REVIEW_SALT` 는 후기 624,422건의 작성자 해시를 만든 값이라
   기본값을 주면 "없어도 도는" 착각을 만든다 — 없으면 없다고 말해야 한다.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    return int(raw) if raw not in (None, "") else default


@dataclass(frozen=True)
class Settings:
    # ── DB ────────────────────────────────────────────────────
    database_url: str = field(default_factory=lambda: os.environ.get(
        "DATABASE_URL", "postgresql://reco:reco@localhost:5432/recodb"))
    #: 🔴 minconn 을 maxconn 과 같게 둔다. 작으면 psycopg2 가 putconn 때
    #:    초과분을 **닫아** 매 요청이 새 커넥션을 연다 — 동시 8요청 p50 32ms.
    #:    같게 두면 2.5ms 다 (09-02 실측).
    pg_max_conn: int = field(default_factory=lambda: _int("PG_MAX_CONN", 10))
    pg_min_conn: int = field(default_factory=lambda: _int(
        "PG_MIN_CONN", _int("PG_MAX_CONN", 10)))

    # ── 서빙 ──────────────────────────────────────────────────
    #: 후보 조회 상한. Retrieval 이 이만큼만 보고 자른다 (04_functions.sql p_limit).
    candidate_limit: int = field(default_factory=lambda: _int("RECO_CANDIDATE_LIMIT", 500))
    #: 탐색 풀 = 상위 N (설계 5-3-3). trace params 의 explore_pool_size 와 같아야 한다.
    explore_pool_size: int = field(default_factory=lambda: _int("RECO_EXPLORE_POOL", 200))
    #: propensity 추정 MC 반복 수.
    propensity_mc: int = field(default_factory=lambda: _int("RECO_PROPENSITY_MC", 200))

    # ── 외부 호출 (규칙 7.5 — 기본값에 맡기지 않는다) ──────────
    llm_timeout_s: int = field(default_factory=lambda: _int("LLM_TIMEOUT_S", 30))
    llm_max_retries: int = field(default_factory=lambda: _int("LLM_MAX_RETRIES", 3))

    # ── 배치 ──────────────────────────────────────────────────
    ingest_batch: int = field(default_factory=lambda: _int("INGEST_BATCH", 2000))

    @property
    def review_salt(self) -> str | None:
        """🔴 기본값 없음. 없으면 None — 부르는 쪽이 멈춰야 한다.

        새로 만들면 이미 적재된 후기의 작성자 해시와 어긋나고 되돌릴 수 없다.
        """
        return os.environ.get("REVIEW_SALT") or None


settings = Settings()
