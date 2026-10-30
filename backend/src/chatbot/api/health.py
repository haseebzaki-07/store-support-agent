from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    # TODO(ops): add a readiness check that verifies the database connection.
    return {"status": "ok"}
