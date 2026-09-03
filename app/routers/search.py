"""재료 자동완성 · 자연어 레시피 검색."""
from fastapi import APIRouter

from ..schemas import IngredientSearchOut, RecipeSearchOut
from ..services.recommends import mock

router = APIRouter(prefix="/v1", tags=["search"])


@router.get("/ingredients/search", response_model=IngredientSearchOut)
def search_ingredients(q: str, limit: int = 5) -> IngredientSearchOut:
    return mock.search_ingredients(q, limit)


@router.get("/recipes/search", response_model=RecipeSearchOut)
def search_recipes(q: str, limit: int = 20, user_id: int | None = None,
                   max_missing: int | None = None) -> RecipeSearchOut:
    return mock.search_recipes(q, limit, user_id, max_missing)
