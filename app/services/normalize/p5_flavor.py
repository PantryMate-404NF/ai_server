"""레시피 맛 벡터 산출 (설계 2-5-1 ⑤ · 02 I-15).

    재료 목록 + 역할  →  recipe_feature.flavor_vec REAL[6]

## 🔑 맛은 주로 양념에서 온다

소고기·감자·양파는 맛 축에 거의 기여하지 않고 고춧가루·간장·식초가 결정한다.
그래서 **집계에서 양념에 더 큰 가중치를 준다** — 단순 평균을 쓰면 재료가 많은
레시피에서 양념 신호가 희석되어 모든 레시피가 비슷해진다.

## 집계 방식을 고르는 것이 시드만큼 중요하다

    mean      재료 수에 희석된다. 재료 12개 레시피는 전부 밋밋해진다
    max       "고추 한 조각"이 매움 0.9 를 만든다. 과대평가
    role_w    역할 가중 평균 — 양념 3 · 필수 1 · 선택 0.5   ← 채택
    top3      축별 상위 3개 평균 — max 와 mean 의 절충

`bench/flavor_agg.py` 가 넷을 비교한다. **판별력(레시피 간 거리)** 으로 고른다 —
아무리 정확해도 모든 레시피가 같은 값을 받으면 `f_taste` 는 무용지물이다.
"""
from __future__ import annotations

import io
from pathlib import Path

import yaml

from ...schemas.common import IngredientRole

ROOT = Path(__file__).resolve().parents[3]
AXES = ["매움", "짠맛", "단맛", "신맛", "감칠맛", "기름짐"]
N_AXIS = 6

#: 역할별 집계 가중치. **양념이 맛을 만든다**는 도메인 사실을 수치로 넣은 것.
#: ⚠️ 근거는 요리 상식이지 측정이 아니다 — bench/flavor_agg.py 가 대안과 비교한다.
ROLE_WEIGHT = {
    IngredientRole.SEASONING: 3.0,
    IngredientRole.ESSENTIAL: 1.0,
    IngredientRole.OPTIONAL: 0.5,
    IngredientRole.GARNISH: 0.5,
}
DEFAULT_ROLE_WEIGHT = 1.0


class FlavorTable:
    """재료 → 6축 기여. 카테고리 기본값 + 개별 예외 (소비기한과 같은 패턴)."""

    def __init__(self, defaults: dict[str, list[float]], overrides: dict[str, list[float]]):
        self.defaults = defaults
        self.overrides = overrides

    @classmethod
    def from_seeds(cls, seeds: Path = ROOT / "seeds") -> "FlavorTable":
        d = yaml.safe_load(io.open(seeds / "ingredient_flavor.yaml", encoding="utf-8"))
        return cls({x["path"]: x["v"] for x in d["defaults"]},
                   {x["name"]: x["v"] for x in d["overrides"]})

    def of(self, name: str | None, category_path: str | None) -> list[float]:
        """개별 예외 > 카테고리 최장 접두 > 0벡터."""
        if name and name in self.overrides:
            return self.overrides[name]
        if category_path:
            parts = category_path.split(".")
            for i in range(len(parts), 0, -1):
                hit = self.defaults.get(".".join(parts[:i]))
                if hit:
                    return hit
        return [0.0] * N_AXIS


def aggregate(items: list[tuple[list[float], IngredientRole | None]],
              mode: str = "role_w") -> list[float]:
    """재료별 6축 → 레시피 6축.

    Args:
        items: [(6축 벡터, 역할)] — 역할이 None(P4 보류)이면 기본 가중치
        mode: mean | max | role_w | top3
    """
    vecs = [v for v, _ in items]
    if not vecs:
        return [0.0] * N_AXIS
    if mode == "max":
        return [max(v[k] for v in vecs) for k in range(N_AXIS)]
    if mode == "top3":
        out = []
        for k in range(N_AXIS):
            col = sorted((v[k] for v in vecs), reverse=True)[:3]
            out.append(sum(col) / len(col))
        return out
    if mode == "mean":
        return [sum(v[k] for v in vecs) / len(vecs) for k in range(N_AXIS)]
    # role_w — 양념에 가중
    ws = [ROLE_WEIGHT.get(r, DEFAULT_ROLE_WEIGHT) for _, r in items]
    tot = sum(ws) or 1.0
    return [sum(v[k] * w for (v, _), w in zip(items, ws)) / tot for k in range(N_AXIS)]
