import asyncio
import re
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import typer
from crawl4ai import BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.filters import (
    ContentTypeFilter,
    FilterChain,
    URLPatternFilter,
)
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer

# Import DefaultMarkdownGenerator AND our custom one
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from typing_extensions import Annotated

# Import from our modules
from .markdown import (
    LinkRemovingMarkdownGenerator,
)  # Import the custom generator # noqa: E501
from .config import (
    DEFAULT_CACHE_MODE,
    DEFAULT_CONTENT_TYPES,
    DEFAULT_EXCLUDE_PATTERNS,
    DEFAULT_INCLUDE_PATTERNS,
    DEFAULT_KEYWORDS,
    DEFAULT_KEYWORD_WEIGHT,
    DEFAULT_MAX_DEPTH,
    # DEFAULT_OUTPUT_FILENAME, # Unused
    DEFAULT_OUTPUT_TITLE,
)
from .crawler import run_crawl
from .utils import err_console


# --- Typer Application ---
app = typer.Typer(
    help="A CLI tool to crawl websites and generate Markdown documentation.",
    # Optional: disable Typer's own completion commands if not needed
    add_completion=False,
)


@app.command()
def main(
    url: Annotated[str, typer.Argument(help="The starting URL for the crawl.")],
    output_file: Annotated[
        Optional[Path],  # Allow None
        typer.Option(
            "--output",
            "-o",
            help=(
                "Path to save the merged Markdown output. If omitted, "
                "generates filename from URL in ./storage/."
            ),
        ),
    ] = None,  # Default to None to detect if user provided it
    output_title: Annotated[
        str,
        typer.Option("--title", help="Title for the output Markdown file."),
    ] = DEFAULT_OUTPUT_TITLE,
    max_depth: Annotated[
        int,
        typer.Option(
            "--max-depth",
            "-d",
            help="Maximum crawl depth (must be between 1 and 5).",
            min=1,
            max=5,
            # Typer will now error if value is outside the min/max range
        ),
    ] = DEFAULT_MAX_DEPTH,
    include_external: Annotated[
        bool,
        typer.Option(
            "--include-external/--exclude-external",
            help="Follow external links during crawl.",
        ),
    ] = False,
    include_patterns: Annotated[
        Optional[List[str]],  # Make optional to allow empty list from CLI
        typer.Option(
            "--include-pattern",
            help=(
                "URL pattern to include (can be used multiple times). "
                "Default: common doc patterns."
            ),
        ),
    ] = None,  # Default to None, handle logic below
    exclude_patterns: Annotated[
        Optional[List[str]],  # Make optional to allow empty list from CLI
        typer.Option(
            "--exclude-pattern",
            help=(
                "URL pattern to exclude (can be used multiple times). "
                "Default: fragment identifiers."
            ),
        ),
    ] = None,  # Default to None, handle logic below
    content_types: Annotated[
        Optional[List[str]],  # Make optional to allow empty list from CLI
        typer.Option(
            "--content-type",
            help=(
                "Allowed content type (can be used multiple times). "
                "Default: text/html."
            ),
        ),
    ] = None,  # Default to None, handle logic below
    keywords: Annotated[
        Optional[List[str]],  # Make optional to allow empty list from CLI
        typer.Option(
            "--keyword",
            "-k",
            help=(
                "Keyword for relevance scoring (can be used multiple times). "
                "Default: common doc keywords."
            ),
        ),
    ] = None,  # Default to None, handle logic below
    keyword_weight: Annotated[
        float,
        typer.Option("--keyword-weight", help="Weight for keyword relevance scorer."),
    ] = DEFAULT_KEYWORD_WEIGHT,
    remove_links_flag: Annotated[
        bool,
        typer.Option(
            "--remove-links/--keep-links",
            help=(
                "Remove nav links, headers, footers from HTML before "
                "markdown conversion."
            ),
        ),
    ] = True,
    ignore_images: Annotated[
        bool,
        typer.Option(
            "--ignore-images/--include-images",
            help="Ignore images during markdown conversion.",
        ),
    ] = True,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable verbose output during crawl."),
    ] = False,
    stream: Annotated[
        bool,
        typer.Option("--stream/--no-stream", help="Process results as they arrive."),
    ] = True,
    # Accept cache_mode as string, parse manually later
    cache_mode_str: Annotated[
        str,
        typer.Option(
            "--cache-mode",
            help=(
                f"Cache mode to use. Choices: "
                f"{[e.name.lower() for e in CacheMode]}. Case-insensitive."
            ),
        ),
    ] = DEFAULT_CACHE_MODE.name,  # Default to the name of the enum member
    exclude_markdown_external_links: Annotated[
        bool,
        typer.Option(
            "--exclude-markdown-external-links/" "--include-markdown-external-links",
            help="Exclude external links from the final markdown output.",
        ),
    ] = True,
    only_text: Annotated[
        bool,
        typer.Option(
            "--only-text/--keep-markup",
            help="Extract only text content, ignoring markup, for markdown.",
        ),
    ] = True,
    wait_for: Annotated[
        Optional[str],
        typer.Option(
            "--wait-for",
            help=(
                "Time in seconds or CSS selector to wait for before capturing content. "
                "For JavaScript-rendered pages, use a number (e.g., 5) or a CSS selector "
                "(e.g., 'css:.content-loaded'). Prefix with 'js:' for JavaScript conditions."
            ),
        ),
    ] = None,
    js_code: Annotated[
        Optional[str],
        typer.Option(
            "--js-code",
            help=(
                "JavaScript code to execute on the page before capturing content. "
                "Useful for interacting with the page or making it render dynamic content."
            ),
        ),
    ] = None,
    page_load_timeout: Annotated[
        int,
        typer.Option(
            "--page-load-timeout",
            help="Maximum time in seconds to wait for page to load completely.",
        ),
    ] = 30,
    wait_for_js_render: Annotated[
        bool,
        typer.Option(
            "--wait-for-js-render/--no-wait-for-js-render",
            help="Wait for JavaScript-rendered content using a special script for SPAs.",
        ),
    ] = False,
):
    """
    Crawls a website starting from the given URL and generates a merged
    Markdown file.
    """
    # --- Handle Optional List Defaults ---
    # If the user didn't provide the option, use the default list.
    # If they provided the option but no values, it will be an empty list.
    final_include_patterns = (
        include_patterns if include_patterns is not None else DEFAULT_INCLUDE_PATTERNS
    )
    final_exclude_patterns = (
        exclude_patterns if exclude_patterns is not None else DEFAULT_EXCLUDE_PATTERNS
    )
    final_content_types = (
        content_types if content_types is not None else DEFAULT_CONTENT_TYPES
    )
    final_keywords = keywords if keywords is not None else DEFAULT_KEYWORDS

    # --- Determine Output File Path ---
    if output_file is None:
        # User did not specify --output, generate filename from URL
        storage_dir = Path("storage")
        storage_dir.mkdir(parents=True, exist_ok=True)  # Ensure storage dir exists

        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            # Sanitize domain for use in filename
            # Remove http/https, www., and replace non-alphanumeric with underscore # noqa: E501
            sanitized_domain = re.sub(r"^www\.", "", domain)  # Remove www.
            sanitized_domain = re.sub(
                r"[^\w.-]+", "_", sanitized_domain
            )  # Replace invalid chars
            # Remove trailing dots or underscores
            sanitized_domain = sanitized_domain.strip("._")
            # Handle cases where sanitization results in empty string
            if not sanitized_domain:
                sanitized_domain = "default_crawl_output"

            output_filename = f"{sanitized_domain}.md"
            output_file = storage_dir / output_filename
            print("No output file specified. Using generated path:\n" f"{output_file}")
        except Exception as e:
            err_console.print(
                f"[bold red]Error generating output filename from URL '{url}':"
                f"[/bold red] {e}"
            )
            raise typer.Exit(code=1)
    # else: output_file remains the Path provided by the user

    # --- Configure Filters ---
    filters = []
    if final_exclude_patterns:
        filters.append(URLPatternFilter(patterns=final_exclude_patterns, reverse=True))
    if final_include_patterns:
        filters.append(URLPatternFilter(patterns=final_include_patterns))
    if final_content_types:
        filters.append(ContentTypeFilter(allowed_types=final_content_types))

    filter_chain = FilterChain(filters)

    # --- Configure Scorer ---
    scorer = KeywordRelevanceScorer(keywords=final_keywords, weight=keyword_weight)

    # --- Configure Crawling Strategy ---
    strategy = BestFirstCrawlingStrategy(
        max_depth=max_depth,
        include_external=include_external,
        filter_chain=filter_chain,
        url_scorer=scorer,
    )

    # --- Configure Markdown Generator ---
    # Choose the generator based on the flag
    if remove_links_flag:
        # Use our custom generator that removes links/nav
        markdown_strategy = LinkRemovingMarkdownGenerator(
            options={"ignore_images": ignore_images}
        )
        if verbose:
            print("Using LinkRemovingMarkdownGenerator.")
    else:
        # Use the default generator
        markdown_strategy = DefaultMarkdownGenerator(
            options={"ignore_images": ignore_images}
        )
        if verbose:
            print("Using DefaultMarkdownGenerator (keeping links/nav).")

    # --- Configure Browser ---
    browser_config = BrowserConfig(
        verbose=verbose
        # Add other browser configs here if needed later
    )

    # --- Configure Run ---
    # Pass the selected markdown strategy here
    
    # Determine the final wait_for value
    final_wait_for = wait_for if wait_for else ("5" if wait_for_js_render else None)
    
    merged_run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        # Correct argument name is markdown_generator
        markdown_generator=markdown_strategy,
        verbose=verbose,
        stream=stream,
        # cache_mode=cache_mode, # Set below
        exclude_external_links=exclude_markdown_external_links,
        only_text=only_text,
        # Add wait_for parameter using our determined value
        wait_for=final_wait_for,
        # Add js_code parameter if provided
        js_code=js_code if js_code else (
            # If wait_for_js_render is enabled and no custom js_code is provided, 
            # use this SPA-friendly script to ensure content loads
            """
            // Scroll through the page to trigger lazy loading
            function scrollToBottom() {
                window.scrollTo(0, document.body.scrollHeight);
            }
            
            // Scroll a few times with delay to ensure content loads
            scrollToBottom();
            setTimeout(scrollToBottom, 1000);
            setTimeout(scrollToBottom, 2000);
            
            // Try to find and click any "show more" or expand buttons
            setTimeout(() => {
                const buttons = Array.from(document.querySelectorAll('button, a, [role="button"]'))
                    .filter(el => {
                        const text = el.textContent.toLowerCase();
                        return text.includes('show') || 
                               text.includes('more') || 
                               text.includes('expand') ||
                               text.includes('load');
                    });
                buttons.forEach(button => button.click());
            }, 3000);
            """ if wait_for_js_render else None
        ),
        # Add page_timeout (milliseconds)
        page_timeout=page_load_timeout * 1000,  # Convert to milliseconds
    )

    # --- Manually Parse Cache Mode ---
    try:
        # Find the matching enum member case-insensitively
        parsed_cache_mode = next(
            mode for mode in CacheMode if mode.name.lower() == cache_mode_str.lower()
        )
        merged_run_config.cache_mode = parsed_cache_mode
    except StopIteration:
        valid_modes = [e.name for e in CacheMode]
        err_console.print(
            f"[bold red]Invalid cache mode:[/bold red] '{cache_mode_str}'. "
            f"Valid choices (case-insensitive): {valid_modes}"
        )
        raise typer.Exit(code=1)

    # --- Run the Crawl ---
    # Use asyncio.run to execute the async function from the sync Typer command
    try:
        asyncio.run(
            run_crawl(
                start_url=url,
                output_file=output_file,
                output_title=output_title,
                browser_config=browser_config,
                run_config=merged_run_config,
                verbose=verbose,
            )
        )
    except typer.Exit:
        # Catch typer.Exit to prevent asyncio errors on controlled exits
        pass
    except Exception as e:
        # Catch other potential errors during setup or run_crawl call
        err_console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")
        raise typer.Exit(code=1)


# --- Entry Point ---
# This allows running the CLI directly using `python -m crawler_cli.main`
if __name__ == "__main__":
    app()
