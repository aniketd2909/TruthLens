import hashlib
from newspaper import Article
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from state import NewsState
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

# llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

# ─── Agent 1: Fetch Agent ────────────────────────────────────────────────────
def fetch_agent(state: NewsState) -> dict:
    """Scrapes articles from provided URLs"""
    raw_articles = []
    for url in state["urls"]:
        try:
            article = Article(url)
            article.download()
            article.parse()
            if article.text and len(article.text) > 200:
                raw_articles.append({
                    "url": url,
                    "title": article.title or "No Title",
                    "text": article.text[:3000],  # Limit to 3000 chars
                    "source": article.source_url or url,
                })
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
    return {"raw_articles": raw_articles}


# ─── Agent 2: Deduplication Agent ────────────────────────────────────────────
def dedup_agent(state: NewsState) -> dict:
    """Removes duplicate articles based on content similarity"""
    seen_hashes = set()
    deduplicated = []
    for article in state["raw_articles"]:
        # Hash first 500 chars to detect duplicates
        content_hash = hashlib.md5(article["text"][:500].encode()).hexdigest()
        if content_hash not in seen_hashes:
            seen_hashes.add(content_hash)
            deduplicated.append(article)
    print(f"Deduplication: {len(state['raw_articles'])} → {len(deduplicated)} articles")
    return {"deduplicated_articles": deduplicated}


# ─── Agent 3: Summarization Agent ────────────────────────────────────────────
prompt = ChatPromptTemplate.from_template("""
You are a news summarizer. Given the article below, create a concise 3-sentence summary.
Focus on the key facts, who is involved, and why it matters.

Article Title: {title}
Article Content: {text}
User Topic of Interest: {topic}

Respond in this format:
SUMMARY: <3 sentence summary>
RELEVANCE: <High/Medium/Low based on how relevant this is to the user's topic>
""")

summarize_chain = prompt | llm | StrOutputParser()

def summarize_agent(state: NewsState) -> dict:
    """Summarizes each deduplicated article"""
    summaries = []
    for article in state["deduplicated_articles"]:
        try:
            result = summarize_chain.invoke({
                "title": article["title"],
                "text": article["text"],
                "topic": state.get("topic", "general news"),
            })
            summary = ""
            relevance = "Medium"
            if "SUMMARY:" in result:
                parts = result.split("RELEVANCE:")
                summary = parts[0].replace("SUMMARY:", "").strip()
                relevance = parts[1].strip() if len(parts) > 1 else "Medium"

            summaries.append({
                "title": article["title"],
                "url": article["url"],
                "source": article["source"],
                "summary": summary,
                "relevance": relevance,
            })
        except Exception as e:
            print(f"Failed to summarize {article['url']}: {e}")
    return {"summaries": summaries}


# ─── Agent 4: Presenter Agent ─────────────────────────────────────────────────
report_prompt = ChatPromptTemplate.from_template("""
You are a news editor. Given the following summarized articles, create a well-structured 
news report for the topic: "{topic}"

Organize by relevance (High first), group related stories, and write a brief introduction.

Articles:
{articles}

Write a professional news digest report.
""")

report_chain = report_prompt | llm | StrOutputParser()

def present_agent(state: NewsState) -> dict:
    """Creates a final structured news report"""
    articles_text = "\n\n".join([
        f"Title: {s['title']}\nSource: {s['source']}\nRelevance: {s['relevance']}\nSummary: {s['summary']}\nURL: {s['url']}"
        for s in state["summaries"]
    ])
    report = report_chain.invoke({
        "topic": state.get("topic", "general news"),
        "articles": articles_text,
    })
    return {"final_report": report}