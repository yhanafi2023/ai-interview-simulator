from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness probe — is the process running at all?"""
    return {"status": "ok", "nah" : "hi"}