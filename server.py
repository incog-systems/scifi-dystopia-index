"""
FastAPI server for the Sci-Fi Dystopia Index.

Endpoints:
  GET  /                    → Serve the frontend dashboard
  GET  /api/index           → Return current index data (from disk)
  GET  /api/refresh/stream  → SSE: fetch news → analyze → rebuild index
"""
import asyncio
import json
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from news_fetcher import fetch_articles
from analyzer import analyze_article
from index import build_index

app = FastAPI(title="Sci-Fi Dystopia Index")
app.mount("/static", StaticFiles(directory="static"), name="static")

RESULTS_FILE = Path("dystopia_index_results.json")


@app.get("/")
def root():
    return FileResponse("static/index.html")


@app.get("/api/index")
def get_index():
    if not RESULTS_FILE.exists():
        return JSONResponse({"status": "empty"})
    with open(RESULTS_FILE) as f:
        return JSONResponse(json.load(f))


@app.get("/api/refresh/stream")
async def refresh_stream():
    """
    SSE endpoint that streams progress events while fetching news,
    analyzing articles, and rebuilding the index.

    Event types:
      status     — general status message
      fetched    — articles fetched, count included
      analyzing  — about to analyze article num/total
      analyzed   — article analyzed successfully
      error      — single article failed (non-fatal)
      complete   — done, full data payload included
      fatal_error — unrecoverable error
    """
    newsapi_key = os.environ.get("NEWSAPI_KEY", "")

    async def event_stream():
        def emit(payload: dict) -> str:
            return f"data: {json.dumps(payload)}\n\n"

        try:
            # 1. Fetch articles
            yield emit({"type": "status", "message": "Fetching news articles..."})
            articles = await asyncio.to_thread(fetch_articles, newsapi_key, 10)

            if not articles:
                yield emit({"type": "fatal_error", "error": "No articles returned from NewsAPI. Check your NEWSAPI_KEY."})
                return

            yield emit({"type": "fetched", "count": len(articles)})

            # 2. Analyze each article
            analyses = []
            for i, article in enumerate(articles):
                yield emit({"type": "analyzing", "headline": article["headline"], "num": i + 1, "total": len(articles)})
                try:
                    analysis = await asyncio.to_thread(
                        analyze_article, article["text"], article["headline"]
                    )
                    analyses.append(analysis)
                    yield emit({"type": "analyzed", "headline": article["headline"], "num": i + 1, "total": len(articles)})
                except Exception as e:
                    yield emit({"type": "error", "headline": article["headline"], "error": str(e)})

            if not analyses:
                yield emit({"type": "fatal_error", "error": "All article analyses failed."})
                return

            # 3. Build index + summary
            yield emit({"type": "status", "message": "Building index and generating summary..."})
            index = await asyncio.to_thread(build_index, analyses)

            output = {
                "analyses": [a.model_dump() for a in analyses],
                "index": index.model_dump(),
            }
            with open(RESULTS_FILE, "w") as f:
                json.dump(output, f, indent=2)

            yield emit({"type": "complete", "data": output})

        except Exception as e:
            yield emit({"type": "fatal_error", "error": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
