"""Example CRUD resource showing the request -> session -> model path end to end."""

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from opentelemetry import metrics
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_service_template.db import get_session
from fastapi_service_template.models import Note

router = APIRouter(prefix="/v1/notes", tags=["notes"])
log = structlog.get_logger(__name__)

notes_created = metrics.get_meter(__name__).create_counter(
    "notes.created", unit="{note}", description="Notes created through the API"
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class NoteIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(default="", max_length=10_000)


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    body: str
    created_at: datetime


@router.post("", status_code=status.HTTP_201_CREATED, response_model=NoteOut)
async def create_note(payload: NoteIn, session: SessionDep) -> Note:
    note = Note(title=payload.title, body=payload.body)
    session.add(note)
    await session.commit()
    notes_created.add(1)
    log.info("note created", note_id=str(note.id))
    return note


@router.get("", response_model=list[NoteOut])
async def list_notes(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Sequence[Note]:
    result = await session.scalars(
        select(Note).order_by(Note.created_at.desc()).limit(limit).offset(offset)
    )
    return result.all()


@router.get("/{note_id}", response_model=NoteOut)
async def get_note(note_id: uuid.UUID, session: SessionDep) -> Note:
    note = await session.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="note not found")
    return note
