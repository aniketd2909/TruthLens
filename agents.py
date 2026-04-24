import hashlib
from dotenv import load_dotenv
from newspaper import Article
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from state import NewsState
from sources import SOURCE_TIER

load_dotenv()
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

# ─── Helper: Detect source tier ──────────────────────────────────────────────
def get_source_tier(url: str) -> str:
    for key, tier in SOURCE_TIER.items():
        if key in url.lower():
            return tier
    return "Unknown"

# ─── Agent 1: Fetch Agent ─────────────────────────────────────────────────────
def fetch_agent(state: NewsState) -> dict:
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
                    "text": article.text[:3000],
                    "source": article.source_url or url,
                    "authors": article.authors,
                    "publish_date": str(article.publish_date) if article.publish_date else "Unknown",
                    "tier": get_source_tier(url),
                })
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
    return {"raw_articles": raw_articles}

# ─── Agent 2: Deduplication Agent ────────────────────────────────────────────
def dedup_agent(state: NewsState) -> dict:
    seen_hashes = set()
    deduplicated = []
    for article in state["raw_articles"]:
        content_hash = hashlib.md5(article["text"][:500].encode()).hexdigest()
        if content_hash not in seen_hashes:
            seen_hashes.add(content_hash)
            deduplicated.append(article)
    print(f"Dedup: {len(state['raw_articles'])} → {len(deduplicated)} articles")
    return {"deduplicated_articles": deduplicated}

# ─── Agent 3: Summarization Agent ────────────────────────────────────────────
summarize_prompt = ChatPromptTemplate.from_template("""
You are a news summarizer. Summarize this article in 2-3 sentences.
Focus on key facts related to the user query.

User Query: {query}
Article Title: {title}
Article Content: {text}

Respond ONLY in this format:
SUMMARY: <2-3 sentence summary>
RELEVANT: <Yes/No - is this article relevant to the query?>
""")
summarize_chain = summarize_prompt | llm | StrOutputParser()

def summarize_agent(state: NewsState) -> dict:
    summaries = []
    for article in state["deduplicated_articles"]:
        try:
            result = summarize_chain.invoke({
                "query": state["query"],
                "title": article["title"],
                "text": article["text"],
            })
            summary = ""
            relevant = "No"
            if "SUMMARY:" in result:
                parts = result.split("RELEVANT:")
                summary = parts[0].replace("SUMMARY:", "").strip()
                relevant = parts[1].strip() if len(parts) > 1 else "No"

            # if relevant.lower().startswith("yes"):
                summaries.append({
                    "title": article["title"],
                    "url": article["url"],
                    "source": article["source"],
                    "tier": article["tier"],
                    "authors": article["authors"],
                    "publish_date": article["publish_date"],
                    "summary": summary,
                    "text": article["text"],
                })
        except Exception as e:
            print(f"Summarize error: {e}")
    return {"summaries": summaries}

# ─── Agent 4: Cross-Source Verifier ──────────────────────────────────────────
verify_prompt = ChatPromptTemplate.from_template("""
You are a fact-checking expert. Analyze these summaries from different news sources 
about the query: "{query}"

Summaries:
{summaries}

Respond ONLY in this format:
CONSISTENT: <Yes/No - are the core facts consistent across sources?>
CONTRADICTIONS: <List any contradictions found, or "None">
CONFIRMED_BY: <Number of sources that confirm the story>
CONFIDENCE: <High/Medium/Low>
""")
verify_chain = verify_prompt | llm | StrOutputParser()

def cross_source_verifier_agent(state: NewsState) -> dict:
    if not state["summaries"]:
        return {"cross_source_result": {
            "consistent": "Unknown",
            "contradictions": "No articles found",
            "confirmed_by": 0,
            "confidence": "Low"
        }}
    summaries_text = "\n\n".join([
        f"Source ({s['tier']}): {s['source']}\nSummary: {s['summary']}"
        for s in state["summaries"]
    ])
    try:
        result = verify_chain.invoke({
            "query": state["query"],
            "summaries": summaries_text,
        })
        consistent = "No"
        contradictions = "None"
        confirmed_by = 0
        confidence = "Low"

        for line in result.split("\n"):
            if "CONSISTENT:" in line:
                consistent = line.split("CONSISTENT:")[1].strip()
            elif "CONTRADICTIONS:" in line:
                contradictions = line.split("CONTRADICTIONS:")[1].strip()
            elif "CONFIRMED_BY:" in line:
                try:
                    confirmed_by = int(''.join(filter(str.isdigit, line.split("CONFIRMED_BY:")[1].strip())))
                except:
                    confirmed_by = len(state["summaries"])
            elif "CONFIDENCE:" in line:
                confidence = line.split("CONFIDENCE:")[1].strip()

        return {"cross_source_result": {
            "consistent": consistent,
            "contradictions": contradictions,
            "confirmed_by": confirmed_by,
            "confidence": confidence,
        }}
    except Exception as e:
        print(f"Verify error: {e}")
        return {"cross_source_result": {"consistent": "Unknown", "contradictions": str(e), "confirmed_by": 0, "confidence": "Low"}}

# ─── Agent 5: Credibility Scorer ─────────────────────────────────────────────
credibility_prompt = ChatPromptTemplate.from_template("""
Score the credibility of this news article from 0-100.

Title: {title}
Source: {source}
Source Tier: {tier}
Authors: {authors}
Publish Date: {publish_date}
Summary: {summary}

Scoring criteria:
- Tier 1 source: +40 points
- Tier 2 source: +25 points  
- Tier 3 source: +10 points
- Named authors present: +20 points
- Recent publish date: +15 points
- Clear factual writing: +25 points

Respond ONLY in this format:
SCORE: <0-100>
REASON: <one sentence explanation>
""")
credibility_chain = credibility_prompt | llm | StrOutputParser()

def credibility_scorer_agent(state: NewsState) -> dict:
    scores = []
    for article in state["summaries"]:
        try:
            result = credibility_chain.invoke({
                "title": article["title"],
                "source": article["source"],
                "tier": article["tier"],
                "authors": ", ".join(article["authors"]) if article["authors"] else "Unknown",
                "publish_date": article["publish_date"],
                "summary": article["summary"],
            })
            score = 50
            reason = ""
            for line in result.split("\n"):
                if "SCORE:" in line:
                    try:
                        score = int(''.join(filter(str.isdigit, line.split("SCORE:")[1].strip()))[:3])
                    except:
                        score = 50
                elif "REASON:" in line:
                    reason = line.split("REASON:")[1].strip()

            scores.append({
                "title": article["title"],
                "source": article["source"],
                "score": min(score, 100),
                "reason": reason,
            })
        except Exception as e:
            print(f"Credibility error: {e}")
    return {"credibility_scores": scores}

# ─── Agent 6: Bias Detector ───────────────────────────────────────────────────
bias_prompt = ChatPromptTemplate.from_template("""
Analyze the political bias and emotional tone of this article.

Title: {title}
Content: {text}

Respond ONLY in this format:
BIAS: <Left/Center-Left/Center/Center-Right/Right>
TONE: <Neutral/Emotional/Sensational/Factual>
EMOTIONAL_WORDS: <list 3 emotionally charged words if found, or "None">
""")
bias_chain = bias_prompt | llm | StrOutputParser()

def bias_detector_agent(state: NewsState) -> dict:
    bias_results = []
    for article in state["summaries"]:
        try:
            result = bias_chain.invoke({
                "title": article["title"],
                "text": article["text"][:1500],
            })
            bias = "Center"
            tone = "Neutral"
            emotional_words = "None"

            for line in result.split("\n"):
                if "BIAS:" in line:
                    bias = line.split("BIAS:")[1].strip()
                elif "TONE:" in line:
                    tone = line.split("TONE:")[1].strip()
                elif "EMOTIONAL_WORDS:" in line:
                    emotional_words = line.split("EMOTIONAL_WORDS:")[1].strip()

            bias_results.append({
                "title": article["title"],
                "source": article["source"],
                "bias": bias,
                "tone": tone,
                "emotional_words": emotional_words,
            })
        except Exception as e:
            print(f"Bias error: {e}")
    return {"bias_results": bias_results}

# ─── Agent 7: AI Content Detector ────────────────────────────────────────────
ai_detect_prompt = ChatPromptTemplate.from_template("""
Analyze whether this article appears to be AI-generated or human-written.

Look for signs of AI generation:
- Overly perfect grammar with no personality
- Generic phrases like "it is worth noting", "in conclusion", "furthermore"
- Lack of specific quotes from real people
- No unique journalistic voice
- Repetitive sentence structures

Article Title: {title}
Article Content: {text}

Respond ONLY in this format:
AI_PROBABILITY: <Low/Medium/High>
INDICATORS: <list 2-3 indicators found, or "None detected">
VERDICT: <Likely Human-Written/Possibly AI-Generated/Likely AI-Generated>
""")
ai_detect_chain = ai_detect_prompt | llm | StrOutputParser()

def ai_detector_agent(state: NewsState) -> dict:
    results = []
    for article in state["summaries"]:
        try:
            result = ai_detect_chain.invoke({
                "title": article["title"],
                "text": article["text"][:2000],
            })
            ai_probability = "Low"
            indicators = "None detected"
            verdict = "Likely Human-Written"

            for line in result.split("\n"):
                if "AI_PROBABILITY:" in line:
                    ai_probability = line.split("AI_PROBABILITY:")[1].strip()
                elif "INDICATORS:" in line:
                    indicators = line.split("INDICATORS:")[1].strip()
                elif "VERDICT:" in line:
                    verdict = line.split("VERDICT:")[1].strip()

            results.append({
                "title": article["title"],
                "source": article["source"],
                "ai_probability": ai_probability,
                "indicators": indicators,
                "verdict": verdict,
            })
        except Exception as e:
            print(f"AI detect error: {e}")
    return {"ai_detection_results": results}

# ─── Agent 8: Final Verdict Agent ────────────────────────────────────────────
verdict_prompt = ChatPromptTemplate.from_template("""
You are a senior fact-checker. Based on all the analysis below, give a final verdict.

Query: {query}
Number of sources found: {source_count}
Cross-source consistency: {consistent}
Contradictions: {contradictions}
Confidence level: {confidence}
Average credibility score: {avg_credibility}
AI generation results: {ai_results}
Bias summary: {bias_summary}

Verdict options:
- REAL: Story confirmed by multiple trusted sources with consistent facts
- FAKE: Story contradicted by trusted sources or has no credible sources
- UNVERIFIED: Story found in some sources but cannot be fully confirmed
- MISLEADING: Facts may be real but presented in a misleading/biased way

Respond ONLY in this format:
VERDICT: <REAL/FAKE/UNVERIFIED/MISLEADING>
CONFIDENCE: <percentage 0-100>
EXPLANATION: <2-3 sentence explanation of the verdict>
RECOMMENDATION: <What should the reader do? e.g. "Cross-check with official sources">
""")
verdict_chain = verdict_prompt | llm | StrOutputParser()

def verdict_agent(state: NewsState) -> dict:
    avg_credibility = 0
    if state["credibility_scores"]:
        avg_credibility = sum(s["score"] for s in state["credibility_scores"]) / len(state["credibility_scores"])

    ai_summary = ", ".join([f"{r['source']}: {r['ai_probability']} AI probability" for r in state["ai_detection_results"][:3]])
    bias_summary = ", ".join([f"{r['source']}: {r['bias']} bias, {r['tone']} tone" for r in state["bias_results"][:3]])

    try:
        result = verdict_chain.invoke({
            "query": state["query"],
            "source_count": len(state["summaries"]),
            "consistent": state["cross_source_result"].get("consistent", "Unknown"),
            "contradictions": state["cross_source_result"].get("contradictions", "None"),
            "confidence": state["cross_source_result"].get("confidence", "Low"),
            "avg_credibility": round(avg_credibility, 1),
            "ai_results": ai_summary or "No AI detection data",
            "bias_summary": bias_summary or "No bias data",
        })

        verdict = "UNVERIFIED"
        confidence = 50
        explanation = ""
        recommendation = ""

        for line in result.split("\n"):
            if "VERDICT:" in line:
                verdict = line.split("VERDICT:")[1].strip()
            elif "CONFIDENCE:" in line:
                try:
                    confidence = int(''.join(filter(str.isdigit, line.split("CONFIDENCE:")[1].strip()))[:3])
                except:
                    confidence = 50
            elif "EXPLANATION:" in line:
                explanation = line.split("EXPLANATION:")[1].strip()
            elif "RECOMMENDATION:" in line:
                recommendation = line.split("RECOMMENDATION:")[1].strip()

        return {"verdict": {
            "verdict": verdict,
            "confidence": min(confidence, 100),
            "explanation": explanation,
            "recommendation": recommendation,
            "avg_credibility": round(avg_credibility, 1),
            "sources_found": len(state["summaries"]),
        }}
    except Exception as e:
        print(f"Verdict error: {e}")
        return {"verdict": {"verdict": "UNVERIFIED", "confidence": 0, "explanation": str(e), "recommendation": "Please try again"}}

# ─── Agent 9: Final Report ────────────────────────────────────────────────────
report_prompt = ChatPromptTemplate.from_template("""
Write a concise fact-check report for the query: "{query}"

Verdict: {verdict}
Explanation: {explanation}
Sources analyzed: {source_count}
Key findings from sources:
{summaries}

Write a 3-4 sentence professional fact-check report summarizing the findings.
""")
report_chain = report_prompt | llm | StrOutputParser()

def present_agent(state: NewsState) -> dict:
    summaries_text = "\n".join([f"- {s['source']}: {s['summary']}" for s in state["summaries"][:5]])
    try:
        report = report_chain.invoke({
            "query": state["query"],
            "verdict": state["verdict"].get("verdict", "UNVERIFIED"),
            "explanation": state["verdict"].get("explanation", ""),
            "source_count": len(state["summaries"]),
            "summaries": summaries_text,
        })
        return {"final_report": report}
    except Exception as e:
        return {"final_report": f"Report generation failed: {e}"}
