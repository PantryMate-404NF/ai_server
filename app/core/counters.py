"""로그 쓰기 계측.

🔴 **`stage_trace.totals.degraded` 에 얹지 않는다.** 두 가지 이유다.

  ① `degraded` 는 `stage_trace` 안에 있고 `stage_trace` 는 그 INSERT 로만 저장된다.
     쓰기가 실패하면 `degraded=true` 를 담은 행도 같이 사라진다 —
     **실패를 실패한 것 안에 기록할 수는 없다.**
  ② `degraded` 의 정의는 "폴백 경로를 탔다" 이고 폴백율 대시보드의 분자다.
     로깅 결함을 섞으면 두 신호가 한 칸에서 합쳐져 다시 못 나눈다.

그래서 프로세스 메모리에 세고 밖으로 노출한다.
"""
from __future__ import annotations

import threading

_LOCK = threading.Lock()
_C: dict[str, int] = {}


def bump(key: str, n: int = 1) -> None:
    with _LOCK:
        _C[key] = _C.get(key, 0) + n


def counters() -> dict[str, int]:
    """현재 카운터 스냅샷. `/health` 와 대시보드가 읽는다.

    🔴 프로세스 메모리다 — 재시작하면 0 이 된다. 유실을 **누적 총계**로 보려면
       대시보드가 주기적으로 긁어 시계열로 쌓아야 한다.
    """
    with _LOCK:
        return dict(_C)


def reset_counters() -> None:
    """테스트 전용."""
    with _LOCK:
        _C.clear()
