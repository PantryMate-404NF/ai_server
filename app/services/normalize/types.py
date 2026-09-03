"""P1·P2 산출 타입.

P3 매칭은 `ParsedIngredient.name` 만 본다. 나머지 필드는 P4(역할 판정)와
P5(수량 환산)가 쓴다.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Preprocessed:
    """P1 산출. 아직 분해되지 않았다."""
    original: str                                  # 원문. 절대 수정하지 않는다
    text: str                                      # 괄호를 걷어낸 본문
    notes: list[str] = field(default_factory=list)         # 부위·상태 설명
    conversions: list[str] = field(default_factory=list)   # '400ml' 같은 환산값
    optional_hints: list[str] = field(default_factory=list)  # '생략가능'
    substitutes: list[str] = field(default_factory=list)     # '또는 미림'


@dataclass
class ParsedIngredient:
    """P2 산출. P3 매칭의 입력."""
    raw_text: str                     # 원문 (recipe_ingredient_raw.raw_text)
    name: str                         # ← P3 매칭 대상
    quantity: float | None = None     # 모호하면 None. 0 으로 채우지 않는다
    unit: str | None = None
    note: str | None = None
    modifiers: list[str] = field(default_factory=list)    # 제거한 수식어 (L2 재활용)
    substitutes: list[str] = field(default_factory=list)
    is_optional_hint: bool = False    # → P4 optional 신호
    is_ambiguous_qty: bool = False    # '약간' 류 → P4 optional 신호
    split_candidate: bool = False     # 복합 의심 → P3 실패 시 검수 큐
    position: int = 0                 # 한 raw_text 에서 몇 번째로 나왔나
    #: 🔴 재료가 아니다 — 조리도구·용기·소모품 (seeds/non_ingredient.yaml).
    #:    만개의레시피는 재료 목록에 도구를 섞어 넣는다 (도마 ×2,259 · 냄비 ×1,124).
    #:    **지우지 않고 표시만 한다.** 유저에게 묻는 값이 아니라
    #:    후속 코드가 읽어가는 내부 플래그다 — position 이 어긋나면 안 되고,
    #:    "무엇을 걸렀는지" 자체가 데이터 품질 지표이기 때문이다.
    is_non_ingredient: bool = False
    non_ingredient_kind: str | None = None   # tool | vessel | consumable | action
