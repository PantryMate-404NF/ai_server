"""추천 실행과 로그 재조회."""
from uuid import UUID

from fastapi import APIRouter, HTTPException

from ..schemas import RecommendRequest, RecommendResponse, RecommendationLogOut
from ..services.recommends import mock

router = APIRouter(prefix="/v1", tags=["recommend"])


@router.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest) -> RecommendResponse:
    return mock.build_recommendation(req)


@router.get("/recommendations/{request_id}", response_model=RecommendationLogOut)
def get_log(request_id: UUID) -> RecommendationLogOut:
    # 🔴 404 판정은 여기서 한다 — 서비스는 없으면 None 을 돌려줄 뿐이다 (규칙 4절).
    log = mock.read_log(request_id)
    if log is None:
        raise HTTPException(404, "request_id 를 찾을 수 없습니다")
    return log
