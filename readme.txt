LangGraph Flow

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

![Truthlens](https://github.com/aniketd2909/TruthLens/blob/main/Truthlens.png?raw=true)
