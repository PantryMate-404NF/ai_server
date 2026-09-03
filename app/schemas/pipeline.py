"""스테이지 간 계약 (설계 5-0).

    RetrievalInput → [①] → Candidate
                   → [②] → ScoredCandidate
                   → [③] → RankedItem

⚠️ 규율 (설계 1-2)
   1. 스테이지는 이 모델로만 대화한다. dict 전달 금지.
   2. 스테이지 간 직접 import 금지. api/ 가 순서대로 호출한다.
   3. 스테이지는 DB 접근을 features/ 에 위임한다.

책임 경계 — **제외는 오직 ①에서만 한다.** ②가 후보를 빼기 시작하면
"왜 빠졌는지"를 두 곳에서 찾아야 한다.
"""
from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import (CANDIDATE_KEEP, FEATURE_KEYS, PROPENSITY_SEMANTICS,
                     REQUIRED_TRACE_PARAMS, Stage, UserMode)


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)


# ─────────────────────────────────────────────────────────────────
# ① Retrieval
# ─────────────────────────────────────────────────────────────────
class RetrievalInput(_Base):
    """DB 함수 **retrieve_candidates()** 의 인자와 1:1 대응.

    집합을 직접 넘긴다 — 시뮬레이터·벤치가 유저 없이 후보를 뽑을 때 쓴다.
    서빙 경로는 아래 `RetrievalRequest` 다.
    """
    user_id: int
    pantry_ids: list[int] = Field(description="냉장고 + staple 전체 (결정 2)")
    allergy_ids: list[int] = Field(default_factory=list, description="4경로 합집합 전개 결과")
    max_missing: int = Field(default=2, ge=0, le=10)
    max_minutes: int | None = None
    limit: int = Field(default=500, ge=1, le=2000)


class RetrievalRequest(_Base):
    """DB 함수 **retrieve_for_user()** 의 인자와 1:1 대응 — 서빙 경로.

    pantry·allergy 를 넘기지 않는다. SQL 안에서 `user_pantry_ids()` 와
    `expand_user_allergens()` 가 유도한다 — 🔴 **왕복 1회를 지키려면
    파이썬이 먼저 조회해서 넘기면 안 된다** (01 1-7).

    경계값은 위 `RetrievalInput` 과 같아야 한다. 두 경로가 다른 상한을 쓰면
    시뮬 결과와 서빙 결과가 조용히 갈라진다.
    """
    user_id: int
    max_missing: int = Field(default=2, ge=0, le=10)
    max_minutes: int | None = Field(default=None, ge=1)
    limit: int = Field(default=500, ge=1, le=2000)


class Candidate(_Base):
    """① 산출. 아직 점수가 없다."""
    recipe_id: int
    missing_count: int = Field(ge=0)
    missing_ids: list[int] = Field(default_factory=list)
    coverage: float = Field(ge=0.0, le=1.0)
    #: 우연성·다양성 축 (설계 5-3-5). `recipe_feature.cluster_id` 를 그대로 싣는다.
    #: None 이면 클러스터링 배치가 아직 안 돌았다는 뜻 — 균등 탐색으로 폴백한다.
    cluster_id: int | None = None


# ─────────────────────────────────────────────────────────────────
# ② Ranking
# ─────────────────────────────────────────────────────────────────
class ScoredCandidate(Candidate):
    """② 산출.

    🔴 **`contrib`(=w·f) 가 아니라 피처 원값 `features` 를 저장한다.** *(v1.9)*

    이전 판은 `contrib = {k: w·f for k,w in weights if w > 0}` 를 저장했다.
    두 가지가 동시에 깨진다.

    1. **w=0 인 피처 7개가 로그에서 사라진다.** `f_content`·`f_ing_cf`·`f_quality`·
       `f_pantry_use`·`f_dish_type`·`f_skill_fit`·`f_group_pref`. 나중에 그 피처를 켜서 LightGBM 을
       학습하려 해도 **과거 로그에 값이 없어 소급이 불가능**하다. R9 ablation 도 못 한다.
    2. **training-serving skew.** 온라인은 SQL, 오프라인은 pandas 로 피처를 두 번
       계산하면 반드시 어긋난다. 서빙 시점 피처를 그대로 학습에 쓰면 원천 제거된다.

    `contrib` 는 저장하지 않고 `contrib(weights)` 로 언제든 되계산한다.
    가중치가 바뀌어도 과거 로그를 다시 해석할 수 있다.
    """
    #: 🔴 FEATURE_KEYS 전부가 있어야 한다. **`None` 과 `0.0` 은 다른 의미다.**
    #:    `0.0` = 계산했더니 0 · `None` = 계산할 수 없음(수단 미구현·데이터 없음).
    #:    LightGBM 은 결측을 native 로 처리하므로 0 으로 메우면 정보가 왜곡된다.
    features: dict[str, float | None] = Field(
        description="피처 원값 17종. w 와 무관하게 항상 전부 기록한다")
    score: float
    penalty: float = Field(default=1.0, ge=0.0, le=1.0,
                           description="p_recent · p_cooked · (1-p_avoid) 의 곱")

    @field_validator("features")
    @classmethod
    def _all_keys(cls, v: dict[str, float | None]) -> dict[str, float | None]:
        missing = set(FEATURE_KEYS) - set(v)
        unknown = set(v) - set(FEATURE_KEYS)
        if missing:
            raise ValueError(f"features 에 빠진 피처: {sorted(missing)} — 전부 기록해야 한다")
        if unknown:
            raise ValueError(f"FEATURE_KEYS 에 없는 피처: {sorted(unknown)}")
        return v

    def contrib(self, weights: dict[str, float]) -> dict[str, float]:
        """w·f. 저장하지 않고 필요할 때 계산한다 (디버거 막대그래프용)."""
        return {k: weights.get(k, 0.0) * (self.features.get(k) or 0.0)
                for k in FEATURE_KEYS if weights.get(k, 0.0) > 0}


# ─────────────────────────────────────────────────────────────────
# 추천 이유 선택 — z-salience (설계 5-5) *(v1.9)*
#
# 🔴 `contrib = w·f` 의 최댓값으로 이유를 고르면 **이유가 한 종류로 붕괴한다.**
#    측정: 후보 500건 시뮬레이션에서 Top-20 의 이유가 100% `f_coverage` 였다.
#    ① 이 곧 max_missing 으로 걸러낸 뒤라 상위 후보의 f_coverage 는 항상 1.0 근처이고,
#    ② w(f_coverage)=0.24 가 최대 가중치이므로 w·f 의 argmax 가 사실상 고정된다.
#
#    이유는 "점수가 높은 이유"가 아니라 **"다른 후보와 달라서 뽑힌 이유"** 여야 한다.
#    따라서 같은 요청의 후보 집합을 기준으로 표준화한다.
# ─────────────────────────────────────────────────────────────────
#: σ 하한. 🔴 **없으면 z-salience 가 무의미한 차이를 증폭한다.**
#:    후보 500건의 `f_coverage` 가 전부 0.98~0.99 라면 σ≈0.003 이고,
#:    0.01 차이가 z=3 으로 튀어 그것이 추천 이유가 된다. 유저가 지각할 수 없는 차이다.
#:    모든 피처가 0~1 로 정규화돼 있으므로(설계 5-2-1) 5% 를 지각 하한으로 둔다.
SIGMA_FLOOR = 0.05


def feature_stats(cands: Sequence["ScoredCandidate"]) -> dict[str, tuple[float, float]]:
    """후보 집합의 피처별 (평균, 표준편차). None 은 제외하고 계산한다."""
    out: dict[str, tuple[float, float]] = {}
    for k in FEATURE_KEYS:
        vals = [c.features.get(k) for c in cands]
        vals = [v for v in vals if v is not None]
        if not vals:
            out[k] = (0.0, SIGMA_FLOOR)
            continue
        mu = sum(vals) / len(vals)
        var = sum((v - mu) ** 2 for v in vals) / len(vals)
        out[k] = (mu, max(var ** 0.5, SIGMA_FLOOR))
    return out


def salience(cand: "ScoredCandidate", weights: dict[str, float],
             stats: dict[str, tuple[float, float]]) -> dict[str, float]:
    """w·(f−μ)/σ — 후보 집합 대비 이 레시피가 두드러진 정도."""
    out = {}
    for k in FEATURE_KEYS:
        w = weights.get(k, 0.0)
        f = cand.features.get(k)
        if w <= 0 or f is None:
            continue
        mu, sd = stats.get(k, (0.0, 1.0))
        out[k] = w * (f - mu) / sd
    return out


def top_reasons(cand: "ScoredCandidate", weights: dict[str, float],
                stats: dict[str, tuple[float, float]], n: int = 2) -> list[str]:
    """이유 템플릿에 쓸 상위 n개 피처.

    **2개를 쓰는 것이 기본이다.** 1개만 쓰면 σ 로 표준화해도 분포가 뾰족한 피처
    (`f_expiring` — 대부분 0, 가끔 1) 가 목록을 다시 지배한다. 측정에서 85% 였다.
    """
    sal = salience(cand, weights, stats)
    return [k for k, _ in sorted(sal.items(), key=lambda kv: -kv[1])[:n]]


# ─────────────────────────────────────────────────────────────────
# ③ Re-ranking
# ─────────────────────────────────────────────────────────────────
class RankedItem(ScoredCandidate):
    """③ 산출. 유저에게 나가는 최종 형태."""
    final_rank: int = Field(ge=1)
    reason: str = Field(default="", description="템플릿 생성 문구 (설계 5-5)")
    reason_features: list[str] = Field(
        default_factory=list,
        description="이유를 만든 피처 (z-salience 상위). 디버거가 근거를 보여준다")
    mmr_penalty: float = 0.0
    is_exploration: bool = Field(
        default=False,
        description="무작위 삽입 슬롯. position bias 보정의 기준점 (설계 5-3-3)",
    )
    #: 🔴 **소급 불가.** 이 아이템이 이 위치에 노출될 확률. IPS/SNIPS 의 분모다.
    #:    나중에 off-policy 평가를 하려면 그때의 로그 정책을 알아야 하는데,
    #:    저장해두지 않으면 영원히 복원할 수 없다 (설계 3-2).
    propensity: float | None = Field(
        default=None, gt=0.0, le=1.0,
        description="노출 확률. exploration 슬롯은 1/|pool|, 결정적 슬롯은 1.0")
    #: 🔑 탐색 슬롯을 **어느 경로가** 채웠는가 (설계 5-3-5).
    #:    'uniform'  — 균등 무작위. support 보장용. propensity 가 모든 후보에 > 0
    #:    'thompson' — 클러스터 Thompson. 우연성용. propensity 가 아이템마다 다르다
    #:    🔴 구분하지 않으면 두 경로의 로그가 섞여 off-policy 분석에서 나눌 수 없다.
    explore_source: str | None = Field(
        default=None, description="uniform | thompson | None(탐색 슬롯이 아님)")
    #: Team-Draft Interleaving 시 어느 랭커가 이 자리를 가져갔는가 (설계 5-7-2)
    team: str | None = None


# ─────────────────────────────────────────────────────────────────
# stage_trace — 🔴 1주차 동결 대상 (설계 3-1)
# ─────────────────────────────────────────────────────────────────
class StageInfo(_Base):
    """단계 하나의 기록. filters 가 디버깅에서 가장 유용하다."""
    name: Stage
    in_count: int
    out_count: int
    latency_ms: int

    strategy: str | None = None
    model: str | None = None
    fallback: str | None = Field(
        default=None, description="폴백이 발동했으면 대체 모델명 (설계 5-6)")

    filters: dict[str, int] = Field(
        default_factory=dict,
        description="탈락 사유별 건수. 예 {'no_overlap':227999,'allergy_cut':12}")
    dropped: dict[str, int] = Field(
        default_factory=dict, description="③ 전용. 다양성·캡으로 제외한 건수")
    params: dict[str, float | int | str | None] = Field(default_factory=dict)
    score_stats: dict[str, float] = Field(
        default_factory=dict, description="min·p25·p50·p75·max")
    exploration_items: list[int] = Field(default_factory=list)


class TraceTotals(_Base):
    latency_ms: int
    cache_hit: bool = False
    degraded: bool = Field(
        default=False,
        description="폴백 경로를 탔다. 이 비율이 조용히 오르는 것이 가장 위험한 실패 양상")
    user_mode: UserMode = UserMode.COLD


class StageTrace(_Base):
    """recommendation_log.stage_trace 에 그대로 직렬화된다."""
    trace_version: str = "v1"
    stages: list[StageInfo] = Field(default_factory=list)
    totals: TraceTotals

def merge_served_detail(scored: Sequence["ScoredCandidate"],
                        items: Sequence["RankedItem"]) -> list["ScoredCandidate"]:
    """③ 산출(RankedItem)을 ② 산출(ScoredCandidate) 위에 덮어쓴다.

    🔴 **propensity 는 `RankedItem` 에만 있다.** `ScoredCandidate` 에는 없고,
       `keep_candidates()` 는 `ScoredCandidate` 를 돌려준다. 그래서 이 병합을
       건너뛰면 저장되는 후보가 전부 ② 투영이라 **propensity 가 로그에 단 한 번도
       남지 않는다** — off-policy 평가의 IPS 분모가 통째로 사라진다.
       같은 이유로 `is_exploration`·`team`·`mmr_penalty`·`explore_source` 도 잃는다.

    propensity 는 서빙 순간의 MC 값이 유일본이다. `user_cluster_stat` 이 갱신되면
    사후 재계산이 불가능하므로 **이 자리에서 안 실으면 영원히 없다.**

    점수 내림차순 순서는 `scored` 것을 그대로 쓴다 — 절단 기준이 순서이기 때문이다.

        >>> merged = merge_served_detail(scored, ranked_items)
        >>> kept   = keep_candidates(merged, served, serving_mode)
        >>> all(hasattr(c, "propensity") for c in kept if c.recipe_id in set(served))
        True
    """
    by_id = {it.recipe_id: it for it in items}
    return [by_id.get(c.recipe_id, c) for c in scored]


def keep_candidates(candidates: Sequence["ScoredCandidate"], served: Sequence[int],
                    serving_mode: str = "real") -> list["ScoredCandidate"]:
    """🔴 저장할 candidates 를 고른다 — **`served ⊆ candidates` 를 보장한다** (S0 ① 확정).

    후보 500건을 다 저장하면 1행이 100KB 를 넘는다. 그래서 상위 N 만 남기는데,
    **exploration 아이템은 상위 200 풀에서 뽑히므로 그 N 밖으로 떨어질 수 있다.**
    하필 그것이 **propensity ≠ 1.0 인 유일한 행**이라, 잘리면 off-policy 평가에
    필요한 것만 정확히 사라진다. 실험 기록에서 대조군만 빼먹는 것과 같다.

    그래서 **절단한 뒤 실제 노출분을 합집합한다.** 최대 +2건, 한 행에 약 0.5KB 다.

    🔴 **`merge_served_detail()` 을 먼저 통과시켜라.** 이 함수는 `recipe_id` 만 읽으므로
       `RankedItem` 이 섞여 있어도 그대로 보존한다 — 그래야 노출분에 propensity 가 실린다.

        >>> kept = keep_candidates(scored, served=[c.recipe_id for c in ranked])
        >>> set(served) <= {c.recipe_id for c in kept}
        True
    """
    n = CANDIDATE_KEEP.get(serving_mode, 50)
    if n is None or n <= 0:
        return []
    head = list(candidates[:n])
    have = {c.recipe_id for c in head}
    rest = {c.recipe_id: c for c in candidates if c.recipe_id not in have}
    for rid in served:                      # 순서를 보존해 재현성을 지킨다
        if rid not in have and rid in rest:
            head.append(rest[rid])
            have.add(rid)
    return head


def check_trace_params(params: dict) -> list[str]:
    """`StageInfo.params` 에 동결 키가 다 있는지. 없는 키 목록을 돌려준다.

    값이 아니라 **정의**가 소급 불가다 — 로그가 있어도 이 키들이 없으면
    propensity 를 재구성할 수 없다 (07 E-3 ①).
    """
    missing = [k for k in REQUIRED_TRACE_PARAMS if k not in params]
    if params.get("propensity_semantics") not in (None, PROPENSITY_SEMANTICS):
        missing.append(f"propensity_semantics!={PROPENSITY_SEMANTICS}")
    return missing

