from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sources import ALL_URLS
from graph import news_graph

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class QueryRequest(BaseModel):
    query: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )

@app.post("/verify")
async def verify(query: QueryRequest):
    if not query.query.strip():
        return {"error": "Please enter a query"}

    result = news_graph.invoke({
        "query": query.query,
        "urls": ALL_URLS,
        "raw_articles": [],
        "deduplicated_articles": [],
        "summaries": [],
        "cross_source_result": {},
        "credibility_scores": [],
        "bias_results": [],
        "ai_detection_results": [],
        "verdict": {},
        "final_report": "",
    })

    return {
        "verdict": result["verdict"],
        "report": result["final_report"],
        "summaries": result["summaries"],
        "credibility_scores": result["credibility_scores"],
        "bias_results": result["bias_results"],
        "ai_detection_results": result["ai_detection_results"],
        "cross_source_result": result["cross_source_result"],
        "total_fetched": len(result["raw_articles"]),
        "after_dedup": len(result["deduplicated_articles"]),
    }
