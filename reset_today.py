import asyncio
from app.db.session import async_session_maker
from app.models.daily_plan import DailyPlan
from sqlalchemy import delete
from datetime import date

async def reset_today():
    async with async_session_maker() as db:
        today = date.today()
        print(f"Borrando planes del día: {today}")
        
        # Delete all plans for today (simplification for single user context)
        # Ideally filter by user, but assuming single user dev mode mainly.
        stmt = delete(DailyPlan).where(DailyPlan.date == today)
        result = await db.execute(stmt)
        await db.commit()
        
        print(f"Eliminados {result.rowcount} planes.")

if __name__ == "__main__":
    asyncio.run(reset_today())
