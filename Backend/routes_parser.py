from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import Job
from auth import get_current_user
from schemas import JobResponse
from job_parser import (
    parse_somon_tj, parse_remotive, parse_arbeitnow, parse_himalayas, parse_all_sources,
)
from scheduler import run_daily_parse

router = APIRouter(prefix="/parser", tags=["Parser"])


@router.post("/somon-tj/")
async def trigger_somon_parse(max_jobs: int = 30, db: AsyncSession = Depends(get_db)):
    result = await parse_somon_tj(db, max_jobs)
    return result


@router.post("/remotive/")
async def trigger_remotive_parse(max_jobs: int = 50, db: AsyncSession = Depends(get_db)):
    result = await parse_remotive(db, max_jobs)
    return result


@router.post("/arbeitnow/")
async def trigger_arbeitnow_parse(max_jobs: int = 50, db: AsyncSession = Depends(get_db)):
    result = await parse_arbeitnow(db, max_jobs)
    return result


@router.post("/himalayas/")
async def trigger_himalayas_parse(max_jobs: int = 50, db: AsyncSession = Depends(get_db)):
    result = await parse_himalayas(db, max_jobs)
    return result


@router.post("/all/")
async def trigger_all_parse(max_jobs: int = 30):
    import asyncio
    result = await parse_all_sources(max_jobs)
    return result


@router.post("/run-now/")
async def run_now():
    await run_daily_parse()
    return {"detail": "Parse triggered"}


@router.get("/stats/")
async def parser_stats(db: AsyncSession = Depends(get_db)):
    total = await db.execute(select(func.count(Job.id)))
    total_count = total.scalar() or 0

    sources = await db.execute(
        select(Job.source, func.count(Job.id)).group_by(Job.source)
    )
    source_stats = {row[0]: row[1] for row in sources.all()}

    return {
        "total_jobs": total_count,
        "by_source": source_stats,
    }
