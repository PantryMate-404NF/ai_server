"""JSONB 칸의 **속** 형식 (2026-09-03 신설).

## 왜 필요한가

표가 있다고 양식이 정해진 것은 아니다. `jsonb` 칸은 **무엇이든 받는다** —
넣는 사람과 읽는 사람이 서로 다른 모양을 써도 DB 는 아무 말도 하지 않는다.

실제로 09-02 에 A 와 C 가 `normalization_queue.suggested` 를
**배열과 객체로 각각** 적어 놓은 것이 발견됐다. 그대로 짰으면 시더가 넣은 것을
화면이 못 읽었을 것이고, **에러가 아니라 빈 화면**으로 나타났을 것이다.

## 무엇을 담나

**두 사람 이상이 주고받는 칸만** 담는다. 혼자 쓰는 자유 칸
(`batch_run.params` · `event_log.context` · `recipe.raw_json`)은 묶지 않는다 —
그런 것까지 계약으로 만들면 형식을 다듬을 때마다 계약을 고쳐야 한다.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)


# ─────────────────────────────────────────────────────────────────
# normalization_queue.suggested — A 시더가 쓰고 C 화면이 읽는다 (결정 D-2)
# ─────────────────────────────────────────────────────────────────
class QueueCandidate(_Base):
    """검수 화면에 버튼으로 놓일 후보 하나."""
    #: 🔴 **반드시 사전에 있는 표제어.** 없는 이름을 만들지 않는다 —
    #:    검수자가 누르면 그대로 사전에 들어가기 때문이다.
    name: str = Field(min_length=1)
    #: 0~1. 화면이 정렬·표시에만 쓴다. **자동 확정하지 않는다** —
    #: 실측에서 임계 0.6 재현율이 0% 였다(정탐 0.143 vs 오탐 0.118).
    score: float = Field(ge=0.0, le=1.0)
    method: Literal["exact", "alias", "rule", "jamo_trgm"]


class QueueSuggestion(_Base):
    """`normalization_queue.suggested` 의 전체 모양.

    배열이 아니라 **객체**인 이유는 나중에 칸을 늘릴 수 있어야 해서다.
    `[["매실청", 0.62, "trgm"]]` 은 위치로 의미를 기억해야 하고
    `blocked_by` 를 넣으려면 전부 고쳐야 한다.
    """
    candidates: list[QueueCandidate] = Field(default_factory=list, max_length=10)
    #: 구조적으로 막힌 이유. 없으면 None.
    blocked_by: Literal["hyponym", "sibling", "unrelated"] | None = None


# ─────────────────────────────────────────────────────────────────
# recommendation_log.pantry_detail — B 가 쓰고 C 가 읽는다
# ─────────────────────────────────────────────────────────────────
class PantrySnapshotItem(_Base):
    """요청 시점 냉장고 한 칸.

    🔴 `pantry_snapshot` 배열은 재료 id 만 담아 `f_expiring` 원값을 검증할 수 없다.
       그래서 상세를 따로 남긴다 — 소비기한이 유저 입력인지 추정인지까지.
    """
    ingredient_id: int
    quantity: float | None = None
    unit: str | None = None
    expires_at: str | None = None          # ISO date
    expires_at_source: Literal["user", "estimated", "unknown"] = "estimated"


# ─────────────────────────────────────────────────────────────────
# recommendation_log.policies — 두 정책을 섞어 낼 때만 채운다
# ─────────────────────────────────────────────────────────────────
class PolicyArm(_Base):
    """섞어 낸 정책 한 쪽.

    🔴 `recipe_ids` 가 없으면 **어느 쪽이 이겼는지 셀 수 없다.**
       모델 이름만으로는 승패가 안 나온다 — 클릭된 것이 어느 팀 것이었는지가 필요하다.
    """
    team: Literal["A", "B"]
    model_version: str
    mlflow_run_id: str | None = None
    recipe_ids: list[int] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────
# data_quality_snapshot.match_method_dist — A 와 C 가 나눠 쓴다 (결정 D-1)
# ─────────────────────────────────────────────────────────────────
class QualityExtra(_Base):
    """품질 기록에 곁들이는 값들.

    🔴 표본 수를 반드시 남긴다. 없으면 배치 개선 없이도 추이선이 오르내려
       "좋아졌다" 로 잘못 읽힌다.
    """
    #: 몇 건을 보고 잰 값인가
    sample_n: int = Field(ge=0, alias="_sample_n")
    #: 파일에서 쟀나 DB 에서 쟀나 — 정의가 달라 섞으면 시계열이 꺾인다
    source: Literal["file", "db"] = Field(alias="_source")
    #: 로그 쓰기 실패 계측. 프로세스 메모리라 여기 찍어야 시계열이 남는다
    log_counters: dict[str, int] = Field(default_factory=dict, alias="_log_counters")

    model_config = ConfigDict(extra="allow", populate_by_name=True)
