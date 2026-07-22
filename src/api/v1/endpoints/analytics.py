from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.core.database import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/dashboard-charts")
async def get_dashboard_chart_data(db: AsyncSession = Depends(get_db)):
    """
    Returns aggregated metrics with exactly 5 experience tiers:
    Intern, Junior, Mid-Level, Senior, Lead / Principal
    """
    # 1. Query raw counts from DB
    exp_query = text("""
        SELECT COALESCE(experience_level, 'Mid-Level') AS exp_level, COUNT(*) AS count
        FROM public.candidates
        GROUP BY COALESCE(experience_level, 'Mid-Level')
    """)
    exp_res = await db.execute(exp_query)
    raw_exp = {row[0]: row[1] for row in exp_res.fetchall()}

    # 2. Force all 5 experience levels in exact order
    exp_data = {
        "Intern": raw_exp.get("Intern", 0),
        "Junior": raw_exp.get("Junior", 0),
        "Mid-Level": raw_exp.get("Mid-Level", 0),
        "Senior": raw_exp.get("Senior", 0),
        "Lead / Principal": raw_exp.get("Lead / Principal", 0)
    }

    # 3. Top Target Roles
    roles_query = text("""
        SELECT COALESCE(target_role, 'General / Other') AS role, COUNT(*) AS count
        FROM public.candidates
        GROUP BY COALESCE(target_role, 'General / Other')
        ORDER BY count DESC
        LIMIT 6
    """)
    roles_res = await db.execute(roles_query)
    roles_data = [{"role": row[0], "count": row[1]} for row in roles_res.fetchall()]

    # 4. Stacked Breakdown by Target Role across all 5 tiers
    stacked_query = text("""
        SELECT 
            COALESCE(target_role, 'General / Other') AS role, 
            COALESCE(experience_level, 'Mid-Level') AS exp, 
            COUNT(*) AS count
        FROM public.candidates
        GROUP BY COALESCE(target_role, 'General / Other'), COALESCE(experience_level, 'Mid-Level')
        ORDER BY role
    """)
    stacked_res = await db.execute(stacked_query)
    
    stacked_raw = stacked_res.fetchall()
    roles_set = list(dict.fromkeys([row[0] for row in stacked_raw]))
    
    stacked_data = {
        "roles": roles_set,
        "Intern": [0] * len(roles_set),
        "Junior": [0] * len(roles_set),
        "Mid-Level": [0] * len(roles_set),
        "Senior": [0] * len(roles_set),
        "Lead / Principal": [0] * len(roles_set)
    }
    
    for role, exp, count in stacked_raw:
        if role in roles_set and exp in stacked_data:
            idx = roles_set.index(role)
            stacked_data[exp][idx] = count

    return {
        "experience_distribution": exp_data,
        "top_roles": roles_data,
        "stacked_breakdown": stacked_data
    }