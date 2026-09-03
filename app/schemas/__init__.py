"""스테이지·API 계약. **이 패키지가 계약의 SoT 다.**

설계 문서 01 ⑦절은 배경과 엔드포인트 목록만 설명하고, 필드 정의는 여기를 따른다.
소수 인원이 문서 계약을 따로 유지하면 코드와 어긋나고 결국 아무도 보지 않는다.
"""
from .common import (
    CONTRACT_VERSION, DEFAULT_WEIGHTS, FEATURE_KEYS, LABEL_WEIGHT,
    UNAVAILABLE_FEATURES,
    EventType, IngredientRole, MatchMethod, Stage, UserMode, rating_to_label,
)
from .pipeline import (
    Candidate, RankedItem, RetrievalInput, RetrievalRequest, ScoredCandidate,
    merge_served_detail,
    StageInfo, StageTrace, TraceTotals,
    SIGMA_FLOOR, feature_stats, salience, top_reasons,
)
from .api import (
    OnboardingIn, OnboardingOut,
    ErrorOut, EventAck, EventBatchIn, EventIn, HealthOut,
    IngredientHit, IngredientSearchOut, PantryIn, PantryItemIn, PantryItemOut, PantryOut,
    RecipeHit, RecipeSearchIn, RecipeSearchOut,
    RecommendRequest, RecommendResponse, RecommendationLogOut,
)

__all__ = [
    "CONTRACT_VERSION", "DEFAULT_WEIGHTS", "FEATURE_KEYS", "LABEL_WEIGHT",
    "UNAVAILABLE_FEATURES",
    "EventType", "IngredientRole", "MatchMethod", "Stage", "UserMode", "rating_to_label",
    "OnboardingIn", "OnboardingOut",
    "Candidate", "RankedItem", "RetrievalInput", "RetrievalRequest", "ScoredCandidate",
    "merge_served_detail",
    "StageInfo", "StageTrace", "TraceTotals",
    "SIGMA_FLOOR", "feature_stats", "salience", "top_reasons",
    "ErrorOut", "EventAck", "EventBatchIn", "EventIn", "HealthOut",
    "IngredientHit", "IngredientSearchOut", "PantryIn", "PantryItemIn",
    "PantryItemOut", "PantryOut",
    "RecipeHit", "RecipeSearchIn", "RecipeSearchOut",
    "RecommendRequest", "RecommendResponse", "RecommendationLogOut",
]
