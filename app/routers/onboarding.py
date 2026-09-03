"""온보딩 5문항 저장. 가입 직후 1회."""
from fastapi import APIRouter

from ..schemas import OnboardingIn, OnboardingOut
from ..services.recommends import mock

router = APIRouter(prefix="/v1", tags=["onboarding"])


@router.post("/onboarding/{user_id}", response_model=OnboardingOut)
def put_onboarding(user_id: int, body: OnboardingIn) -> OnboardingOut:
    return mock.save_onboarding(user_id, body)
