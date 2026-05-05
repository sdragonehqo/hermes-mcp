import asyncio
from pathlib import Path

import typer
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig

from .utils import err_console  # Import from utils


async def run_crawl(
    start_url: str,
    output_file: Path,
    output_title: str,
    browser_config: BrowserConfig,
    run_config: CrawlerRunConfig,
    verbose: bool,
):
    """
    Runs the web crawler with the given configurations.

    Args:
        start_url: The URL to start crawling from.
        output_file: The path to save the output Markdown file.
        output_title: The title for the output Markdown file.
        browser_config: Configuration for the browser/crawler instance.
        run_config: Configuration for the specific crawl run.
        verbose: Flag to enable verbose logging.
    """
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"{output_title}\n\n")

    processed_count = 0
    error_count = 0
    async with AsyncWebCrawler(config=browser_config) as crawler:
        if verbose:
            print(f"Starting crawl from: {start_url}")
            print(f"Output file: {output_file.resolve()}")
            print(
                f"Max depth: {run_config.deep_crawl_strategy.max_depth if run_config.deep_crawl_strategy else 'N/A'}"
            )
            print(f"Cache mode: {run_config.cache_mode.name}")
            # Add more verbose output if needed

        try:
            result_generator = await crawler.arun(start_url, config=run_config)

            async for result in result_generator:
                if result.success:
                    processed_count += 1
                    if verbose:
                        print(f"\nProcessing page {processed_count}: {result.url}")

                    with open(output_file, "a", encoding="utf-8") as f:
                        page_title = "Unknown Page"
                        if result.metadata and isinstance(result.metadata, dict):
                            page_title = result.metadata.get(
                                "title", f"Page from {result.url}"
                            )
                        elif isinstance(result.metadata, str):
                            page_title = result.metadata

                        f.write(f"\n## {page_title}\n\n")
                        f.write(f"Source: {result.url}\n\n")

                        md_content = ""
                        if hasattr(result, "markdown") and result.markdown:
                            if hasattr(result.markdown, "raw_markdown"):
                                md_content = result.markdown.raw_markdown

                        if md_content:
                            f.write(md_content + "\n\n")
                        else:
                            f.write("*(No markdown content extracted)*\n\n")
                else:
                    error_count += 1
                    # Print errors to stderr instead of the file
                    err_console.print(
                        f"[bold red]Error crawling {result.url}:[/bold red] {result.error_message}"
                    )

                del result  # Optional memory management

        except Exception as e:
            err_console.print(f"[bold red]Crawling/Processing error:[/bold red] {e}")
            raise typer.Exit(code=1)  # Exit with error code

    print(f"\nProcessed {processed_count} pages successfully.")
    if error_count > 0:
        err_console.print(
            f"[yellow]Encountered errors on {error_count} pages.[/yellow]"
        )
    # Use Path.resolve() for absolute path
    print(f"Consolidated markdown saved to {output_file.resolve()}")
