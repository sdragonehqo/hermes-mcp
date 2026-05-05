from crawl4ai import CacheMode

# --- Default Configuration Values ---
DEFAULT_INCLUDE_PATTERNS = [
    "*doc*",
    "*docs*",
    "*tutorial*",
    "*guide*",
    "*quickstart*",
    "*introduction*",
    "*getting started*",
    "*installation*",
    "*setup*",
    "*manual*",
    "*faq*",
]
DEFAULT_EXCLUDE_PATTERNS = ["*#*"]
DEFAULT_CONTENT_TYPES = ["text/html"]
DEFAULT_KEYWORDS = [
    "docs",
    "documentation",
    "doc",
    "guide",
    "tutorial",
    "example",
    "quickstart",
    "introduction",
    "getting started",
    "installation",
    "setup",
    "manual",
    "faq",
]
DEFAULT_KEYWORD_WEIGHT = 0.7
DEFAULT_OUTPUT_TITLE = "# Crawled Documentation"
DEFAULT_MAX_DEPTH = 1
DEFAULT_CACHE_MODE = CacheMode.BYPASS
