New Agents to Add
1. 🔍 Cross-Source Verifier Agent

Checks if the same news is reported by multiple trusted sources
If only 1 source reports it → likely fake/unverified
If 3+ sources report it → likely real

2. 🤖 AI-Generated Content Detector Agent

Analyzes writing patterns to detect AI-generated text
Checks for: repetitive phrasing, lack of specific details, unnatural fluency

3. 📊 Credibility Scorer Agent

Scores each article 0-100 based on:

Source reputation (BBC > random blog)
Number of sources confirming it
Presence of named journalists/authors
Publication date relevance



4. 🖼️ Image Verification Agent (optional)

Extracts image URLs from articles
Uses reverse image search to check if images are original or reused

5. ⚖️ Bias Detector Agent

Detects if the article leans left/right/neutral
Flags emotionally charged language


New Features in UI
Input Changes

Single search query box (e.g. "Is [news headline] true?")
No manual URL input — auto-searches across all sources

Output Changes
CurrentNewJust summaryVerdict: ✅ Real / ❌ Fake / ⚠️ UnverifiedSource listCredibility score per sourceReportSide-by-side comparison of how different sources cover the same storyNothingConfidence percentage

New LangGraph Flow
User Query
     ↓
[Search Agent]         → Searches BBC, CNN, Reuters etc. for the query
     ↓
[Fetch Agent]          → Scrapes matching articles
     ↓
[Dedup Agent]          → Removes duplicates
     ↓
[Cross-Source Verifier] → How many sources confirm this?
     ↓
[AI Content Detector]  → Is this AI-generated?
     ↓
[Credibility Scorer]   → Score each source 0-100
     ↓
[Bias Detector]        → Left / Right / Neutral
     ↓
[Verdict Agent]        → Final: Real / Fake / Unverified + explanation
     ↓
[Present Agent]        → Structured report with verdict