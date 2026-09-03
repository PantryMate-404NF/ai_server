"""② Ranking · ③ Re-ranking 구현.

Mock 과 실제 구현이 **같은 모듈을 쓴다.** 이유 생성 로직을 두 벌 유지하면
반드시 어긋나고, 디버거가 보여주는 것과 실제 서빙이 달라진다.
"""
from .reason import REASON_TEMPLATES, build_reason
from .explore import exploration_slots, interleave
from .serendipity import ClusterStats, mixed_exploration, thompson_propensity

__all__ = ["REASON_TEMPLATES", "build_reason", "exploration_slots", "interleave",
           "ClusterStats", "mixed_exploration", "thompson_propensity"]
