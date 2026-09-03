"""냉장고 조회 · 갱신. 전체 교체(replace) 방식이다."""
from fastapi import APIRouter

from ..schemas import PantryIn, PantryOut
from ..services.recommends import mock

router = APIRouter(prefix="/v1/users", tags=["pantry"])


@router.get("/{user_id}/pantry", response_model=PantryOut)
def get_pantry(user_id: int) -> PantryOut:
    return mock.read_pantry(user_id)


@router.put("/{user_id}/pantry", response_model=PantryOut)
def put_pantry(user_id: int, body: PantryIn) -> PantryOut:
    return mock.replace_pantry(user_id, body)
