"""재료가 **얼마나 세게** 맛에 기여하는가 — 수량 환산 없이 (설계 2-5-1 ⑤).

## 문제

"재료가 들어갔다"와 "많이 들어갔다"는 다르다.
`고춧가루 1작은술` 과 `고춧가루 3큰술` 은 같은 매움이 아니다.

정확히 하려면 P5 수량 환산(g)이 필요한데, **그것은 보류하기로 했다**
(4-6 · 있음/없음 필터링만 한다). 그럼에도 **정성적 강도**는 잴 수 있다 —
수량 *숫자* 없이 **단위·제목·순서**만으로.

## 세 신호 — 전부 이미 데이터에 있다

    ① 단위 종류   P2 가 이미 파싱한다. `g/개/마리` = 주재료급, `큰술` = 양념, `약간` = 미량
    ② 제목 등장   "김치찌개"의 김치, "제육볶음"의 돼지고기 — **그 요리의 정체성**이다
    ③ 목록 순서   한국 레시피는 주재료를 앞에, 양념을 뒤에 적는 경향

실측(3건)에서 단위 분포는 `큰술 11 · 개 9 · 약간 6 · g 5 · 공기 2 · 마리 1` 로
**주재료 단위와 양념 단위가 뚜렷하게 갈렸다.** 제목 등장도 5건이 잡혔다
(카레·새우·밥·소고기).

## 🔴 이것은 수량 환산의 대체가 아니다

`고춧가루 1큰술` 과 `3큰술` 을 구분하지 못한다 — 같은 등급을 받는다.
**"등급"이지 "양"이 아니다.** 정확한 비율이 필요해지면 P5 를 해야 한다.
그때까지의 **최선의 근사**이고, 비용이 0 이다 (P2 산출을 그대로 쓴다).
"""
from __future__ import annotations

import re

from ...schemas.common import IngredientRole
from .types import ParsedIngredient

#: 단위 → 강도 등급. **양이 아니라 "그 단위를 쓴다는 것이 뜻하는 규모"** 다.
#:   g·kg·개·마리·대·모·공기 를 쓰면 주재료급이고, 큰술·작은술은 양념 규모다.
UNIT_TIER = {
    # 주재료급 — 무게·개수로 센다
    "g": 1.5, "kg": 2.0, "개": 1.5, "마리": 1.5, "대": 1.4, "모": 1.5,
    "공기": 1.5, "장": 1.2, "쪽": 1.0, "줌": 1.2, "봉지": 1.4, "팩": 1.4,
    # 액체 — 국물요리의 주재료일 수 있다
    "ml": 1.2, "L": 1.8, "컵": 1.3,
    # 양념 규모
    "큰술": 1.0, "작은술": 0.7, "티스푼": 0.7,
    # 미량
    "약간": 0.4, "조금": 0.4, "적당량": 0.6, "꼬집": 0.3,
}
DEFAULT_TIER = 1.0

#: 제목에 등장하면 그 요리의 정체성이다. 가장 강한 신호.
TITLE_BOOST = 2.0
#: 목록 앞쪽 1/3 에 있으면 주재료일 가능성이 높다 (한국 레시피의 관행)
POSITION_BOOST = 1.2
#: 역할 가중 (p5_flavor.ROLE_WEIGHT 와 곱해지지 않도록 여기서는 쓰지 않는다)

_TITLE_STRIP = re.compile(r"[\s\-_()\[\]/·,.]+")


def _norm(s: str) -> str:
    return _TITLE_STRIP.sub("", s)


def in_title(name: str, title: str) -> bool:
    """제목에 재료가 등장하는가. 띄어쓰기·기호를 무시하고 본다.

    🔴 2글자 미만은 오탐이 많아 제외한다 — `밥`·`물` 이 아무 제목에나 걸린다.
    """
    if not name or not title or len(name) < 2:
        return False
    return _norm(name) in _norm(title)


def intensity(p: ParsedIngredient, ingredient_name: str | None,
              title: str, position: int, n_total: int,
              role: IngredientRole | None = None) -> float:
    """맛 집계에 쓸 강도 배수. 1.0 이 기준.

    수량 *숫자* 는 쓰지 않는다 — P5 를 보류했으므로 있어도 신뢰하지 않는다.
    단위 *종류* 만 본다.
    """
    tier = UNIT_TIER.get(p.unit or "", DEFAULT_TIER)
    boost = 1.0
    nm = ingredient_name or p.name
    if in_title(nm, title):
        boost *= TITLE_BOOST
    if n_total >= 6 and position < max(1, n_total // 3):
        boost *= POSITION_BOOST
    # 미량 표시가 있으면 위치·제목 보정을 하지 않는다 — '약간' 이 이긴다
    if p.is_ambiguous_qty:
        boost = min(boost, 1.0)
    return tier * boost
