"""재료명 정규화 파이프라인 (설계 ④).

    from app.services.normalize import normalize
    normalize("대파 1대(흰 부분만)")
    → [ParsedIngredient(name='대파', quantity=1.0, unit='대', note='흰 부분만')]

P1 전처리 → P2 분해 → **P3 매칭 캐스케이드** 까지 구현됨.
**P4 역할 판정** 까지 구현됨. P5 수량환산은 미착수.

    from app.services.normalize import Dictionary, match
    d = Dictionary.from_seeds()        # DB 불필요. 운영은 Dictionary.from_db(conn)
    match("국내산 대파", d)             # → 대파 [rule] 0.85
"""
from .p1_preprocess import classify_bracket, preprocess
from .p2_parse import normalize, parse
from .p3_head import Decomposed, HeadIndex
from .p3_match import Coverage, Dictionary, MatchResult, match, match_all
from .p4_role import RoleResult, RoleStats, judge, judge_all
from .types import ParsedIngredient, Preprocessed

__all__ = ["normalize", "parse", "preprocess", "classify_bracket",
           "ParsedIngredient", "Preprocessed",
           "HeadIndex", "Decomposed",
           "Dictionary", "MatchResult", "Coverage", "match", "match_all",
           "RoleResult", "RoleStats", "judge", "judge_all"]
