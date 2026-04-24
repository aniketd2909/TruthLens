from typing import TypedDict, List, Annotated
import operator

class NewsState(TypedDict):
    query: str                                          # User's search query
    urls: List[str]                                     # URLs to scrape
    raw_articles: Annotated[List[dict], operator.add]   # Raw scraped articles
    deduplicated_articles: List[dict]                   # After deduplication
    summaries: Annotated[List[dict], operator.add]      # Summarized articles
    cross_source_result: dict                           # Cross-source verification
    credibility_scores: Annotated[List[dict], operator.add]  # Per article scores
    bias_results: Annotated[List[dict], operator.add]   # Bias per article
    ai_detection_results: Annotated[List[dict], operator.add]  # AI content detection
    verdict: dict                                       # Final verdict
    final_report: str                                   # Final report
