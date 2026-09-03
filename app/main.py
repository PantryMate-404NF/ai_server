"""FastAPI 앱 조립. 규칙 4절 — 여기는 **앱과 라우터 등록만** 한다.

    .venv/bin/uvicorn app.main:app --reload --port 8000
    http://localhost:8000/docs        ← OpenAPI 문서 자동 생성

**목적: 대시보드 트랙이 엔진 완성을 기다리지 않게 하는 것.**
엔진과 대시보드를 순차로 진행하면 남은 기간이 모자란다.
두 트랙을 동시에 진행하려면 이 서버가 먼저 있어야 한다.

지금 응답은 `app/services/recommends/mock.py` 가 만든다 — 고정 시드라 재현
가능하고 실제 추천 로직은 없다. 각 스테이지 담당자가 자기 mock 을 실제 구현으로
갈아끼우면 라우터와 계약은 그대로 둔 채 서비스만 바뀐다.

⬜ 규칙 7.1 은 LLM 클라이언트·임베딩 모델을 `lifespan` 에서 1회 만들라고 한다.
   지금은 둘 다 없어서 lifespan 이 비어 있다 — 생기는 시점에 여기 붙인다.
"""
from __future__ import annotations

from fastapi import FastAPI

from .routers import ROUTERS
from .schemas import CONTRACT_VERSION

app = FastAPI(title="Reco API (mock)", version=CONTRACT_VERSION)

for _r in ROUTERS:
    app.include_router(_r)
