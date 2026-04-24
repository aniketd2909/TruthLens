TRUSTED_SOURCES = {
    "Tier 1": {
        "names": ["BBC", "Reuters", "AP News", "NPR"],
        "urls": [
            "https://www.bbc.com/news",
            "https://www.reuters.com",
            "https://apnews.com",
            "https://www.npr.org/sections/news",
        ]
    },
    "Tier 2": {
        "names": ["CNN", "The Guardian", "Washington Post", "Al Jazeera"],
        "urls": [
            "https://www.cnn.com",
            "https://www.theguardian.com/international",
            "https://www.washingtonpost.com",
            "https://www.aljazeera.com",
        ]
    },
    "Tier 3": {
        "names": ["Fox News", "Daily Mail", "NY Post"],
        "urls": [
            "https://www.foxnews.com",
            "https://www.dailymail.co.uk/news",
            "https://nypost.com",
        ]
    },
}

# Flat list of all URLs for scraping
ALL_URLS = [url for tier in TRUSTED_SOURCES.values() for url in tier["urls"]]

# Source tier lookup
SOURCE_TIER = {}
for tier, data in TRUSTED_SOURCES.items():
    for name in data["names"]:
        SOURCE_TIER[name.lower()] = tier
