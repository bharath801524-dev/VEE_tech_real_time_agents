from fastapi import APIRouter, HTTPException, Query
from app.services.google_news import get_news

router = APIRouter()

@router.get("/news")
async def get_news_endpoint(
    q: str = Query(..., description="Search query for Google News"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of articles to return"),
):
    """Return latest Google News articles for a given query.

    The endpoint queries the public Google News RSS feed, parses the XML and
    returns a JSON list of articles.
    """
    try:
        items = await get_news(q, max_items=limit)
        return {"query": q, "count": len(items), "articles": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
