from typing import TypedDict, List, Annotated
import operator

class NewsState(TypedDict):
    urls: List[str]                          # Input URLs to scrape
    raw_articles: Annotated[List[dict], operator.add]  # Raw scraped articles
    deduplicated_articles: List[dict]        # After deduplication
    summaries: Annotated[List[dict], operator.add]     # Summarized articles
    final_report: str                        # Final presented report
    topic: str                               # User's topic/query
