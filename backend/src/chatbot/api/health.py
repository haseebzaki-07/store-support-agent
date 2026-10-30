from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    # TODO(T0.3): add a readiness check that verifies the database connection.
    return {"status": "ok"}
