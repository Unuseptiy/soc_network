from sqlalchemy import select, text


async def health_check_db(session) -> bool:
    health_check_query = select(text("1"))
    try:
        result = await session.scalars(health_check_query)
        return result is not None
    except OSError:
        return False
