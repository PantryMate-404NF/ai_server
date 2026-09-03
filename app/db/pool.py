"""커넥션 풀. 원격 DB 로 옮겨도 코드가 안 바뀌게 여기서만 연결을 만든다.

원격에서는 접속 수립 자체가 비싸다 — TCP 3-way + PG 스타트업 + SCRAM(+TLS) 로
**커넥션당 5~10ms**. 유닉스 소켓은 ~0.1ms 였다 (06 8-D ④).
그래서 매번 connect 하지 않고 풀에서 빌린다.
"""
from __future__ import annotations

import contextlib
import os
import threading
from collections.abc import Iterator

from ..config import settings

_LOCK = threading.Lock()
_POOL = None


def dsn() -> str:
    # 🔴 매번 환경변수를 다시 읽는다 — 테스트가 DATABASE_URL 을 바꿔 끼우기 때문이다.
    #    설정 기본값은 config.settings 가 갖는다 (규칙 7.6).
    return os.environ.get("DATABASE_URL", settings.database_url)


def _pool():
    global _POOL
    if _POOL is None:
        with _LOCK:
            if _POOL is None:
                try:
                    from psycopg2.pool import ThreadedConnectionPool
                except ImportError as e:                       # pragma: no cover
                    raise RuntimeError(
                        "psycopg2 필요:  make install TRACK=A|B|C") from e
                # 🔴 minconn 이 작으면 풀이 그만큼만 **캐시**한다. psycopg2 는
                #    putconn 시 minconn 을 넘는 커넥션을 닫아버려서, 동시 요청이
                #    minconn 을 넘으면 매 라운드 새로 connect 한다.
                #    원격 DB 에서 커넥션 수립은 5~10ms 라 그게 그대로 지연이 된다
                #    (06 8-D ④). 그래서 기본값을 maxconn 과 같게 둔다.
                _max = settings.pg_max_conn
                _POOL = ThreadedConnectionPool(
                    minconn=settings.pg_min_conn,
                    # 🔴 max_connections=50 (06 3절) 안에 있어야 한다.
                    #    앱·대시보드·배치가 나눠 쓰므로 넉넉히 잡으면 안 된다.
                    maxconn=_max,
                    dsn=dsn())
    return _POOL


@contextlib.contextmanager
def cursor(commit: bool = False) -> Iterator:
    """커서를 빌려준다. `search_path` 는 여기서 한 번만 건다.

    🔴 `SET search_path` 를 DATABASE 수준으로 걸지 않는다 —
       공유 DB 에서 백엔드팀에 영향이 간다 (01 1-7).
    """
    p = _pool()
    conn = p.getconn()
    try:
        cur = conn.cursor()
        cur.execute("SET search_path TO reco, public")
        yield cur
        if commit:
            conn.commit()
        else:
            conn.rollback()          # 읽기 전용 경로가 트랜잭션을 열어두지 않게
        cur.close()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


def healthy() -> bool:
    """DB 가 살아 있는가. 대시보드 상태 표시용.

    🔴 DB 가 죽으면 추천이 통째로 죽는다 — Redis 는 순수 캐시라 대신할 수 없고
       `retrieve_for_user` 자체가 PG 함수다 (02 I-17 ②, 미해결).
    """
    try:
        with cursor() as cur:
            cur.execute("SELECT 1")
            return cur.fetchone()[0] == 1
    except Exception:
        return False


def close_pool() -> None:
    global _POOL
    if _POOL is not None:
        _POOL.closeall()
        _POOL = None
