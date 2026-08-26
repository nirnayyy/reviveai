import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime

from backend.app.database import get_db
from backend.app.models.entities import AuditLog

router = APIRouter(prefix="/api/audit", tags=["Audit Log"])


class AuditLogItem(BaseModel):
    id: str
    case_id: Optional[str]
    actor: str
    action_type: str
    message: str
    metadata: Dict[str, Any]
    created_at: datetime


@router.get("", response_model=List[AuditLogItem])
async def get_audit_logs(
    actor: Optional[str] = Query(None, description="Filter by actor (SYSTEM, RISK_DETECTOR, AI_AGENT, POLICY_ENGINE, EXECUTOR, HUMAN_ADMIN)"),
    case_id: Optional[str] = Query(None, description="Filter by case ID"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    query = select(AuditLog).order_by(desc(AuditLog.created_at))

    if actor and actor != "ALL":
        query = query.where(AuditLog.actor == actor)
    if case_id:
        query = query.where(AuditLog.case_id == case_id)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    logs = result.scalars().all()

    items = []
    for log in logs:
        try:
            meta = json.loads(log.metadata_json)
        except Exception:
            meta = {}

        items.append(AuditLogItem(
            id=log.id,
            case_id=log.case_id,
            actor=log.actor,
            action_type=log.action_type,
            message=log.message,
            metadata=meta,
            created_at=log.created_at
        ))
    return items
