import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sources import NEWS_SOURCES
from graph import news_graph

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class QueryRequest(BaseModel):
    topic: str
    sources: list[str]  # List of selected source names e.g. ["BBC", "CNN"]

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"sources": list(NEWS_SOURCES.keys())}
    )

@app.post("/research")
async def research(query: QueryRequest):
    # Collect URLs from selected sources
    urls = []
    for source in query.sources:
        urls.extend(NEWS_SOURCES.get(source, []))

    if not urls:
        return {"error": "No valid sources selected"}

    # Run the LangGraph pipeline
    result = news_graph.invoke({
        "urls": urls,
        "raw_articles": [],
        "deduplicated_articles": [],
        "summaries": [],
        "final_report": "",
        "topic": query.topic,
    })

    return {
        "report": result["final_report"],
        "summaries": result["summaries"],
        "total_fetched": len(result["raw_articles"]),
        "after_dedup": len(result["deduplicated_articles"]),
    }

@app.get("/sources")
async def get_sources():
    return {"sources": list(NEWS_SOURCES.keys())}