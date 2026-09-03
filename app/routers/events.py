"""행동 로그 수집.

🔴 `impression` 은 클라이언트가 보내지 않는다 — `/v1/recommend` 가 서버측에서
   자동 기록한다 (설계 3-2). 클라이언트에 맡기면 새로고침·세션 만료로 누락되고,
   랭킹 학습의 negative 샘플이 사라진다.
"""
from fastapi import APIRouter

from ..schemas import EventAck, EventBatchIn
from ..services.recommends import mock

router = APIRouter(prefix="/v1", tags=["events"])


@router.post("/events", response_model=EventAck)
def events(batch: EventBatchIn) -> EventAck:
    return mock.ack_events(batch)
