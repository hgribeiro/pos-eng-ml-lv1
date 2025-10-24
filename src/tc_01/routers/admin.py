from __future__ import annotations
from fastapi import APIRouter, Depends
from tc_01.core.security import role_required

router = APIRouter(prefix="/api/v1", tags=["admin"])

@router.post("/scraping/trigger")
def scraping_trigger(user=Depends(role_required("admin"))):
    # Aqui você poderia disparar um job/worker/CLI do scraping
    return {"message": f"Scraping disparado por {user.get('sub')}", "roles": user.get("roles", [])}

