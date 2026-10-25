"""Production CLI Interface for RegWatch."""

import logging
import typer
from rich.console import Console
from rich.table import Table
from regwatch.bootstrap import build_container
from regwatch.infrastructure.sources.registry import get_adapter, load_all_sources
from regwatch.logging_setup import configure_logging

app = typer.Typer(
    name="regwatch",
    help="Autonomous regulatory intelligence & compliance monitoring engine",
    add_completion=False,
)
console = Console()


@app.callback()
def main_callback(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
) -> None:
    """Initialize logging context for all commands."""
    configure_logging(level="DEBUG" if verbose else "INFO")


@app.command()
def sources() -> None:
    """List all registered regulatory sources and their configured listings."""
    configs = load_all_sources()
    table = Table(title="Registered Regulatory Sources", show_header=True)
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Jurisdiction", style="green")
    table.add_column("Listings", style="magenta")

    for key, cfg in configs.items():
        listings = ", ".join([l.get("name", "") for l in cfg.get("listings", [])])
        table.add_row(key, cfg.get("name", key), cfg.get("jurisdiction", "IN"), listings)

    console.print(table)


@app.command()
def ingest(
    source: str = typer.Option("sebi", "--source", "-s", help="Regulator source key"),
    listing: str = typer.Option("circulars", "--listing", "-l", help="Listing name to ingest"),
    max_pages: int | None = typer.Option(None, "--max-pages", "-p", help="Maximum pages to scrape (defaults to source config limit)"),
) -> None:
    """Ingest a regulatory listing, reconcile items, and enqueue detection jobs."""
    console.print(f"[bold green]Starting ingestion for regulator:[/bold green] '{source}' [listing='{listing}']")
    container = build_container()
    adapter = get_adapter(source, container.fetcher)

    target_listing = None
    for l_def in adapter.listings():
        if l_def.name == listing:
            target_listing = l_def
            break

    if not target_listing:
        console.print(f"[bold red]Error:[/bold red] Listing '{listing}' not found in source '{source}'.")
        raise typer.Exit(code=1)

    effective_pages = max_pages if max_pages is not None else target_listing.max_pages
    console.print(f"[dim]Crawling up to {effective_pages} pages for '{listing}'...[/dim]")

    items = adapter.iter_items(target_listing, max_pages=effective_pages)
    summary = container.ingest_uc.execute(items)

    console.print(
        f"[bold cyan]Ingestion Summary:[/bold cyan] "
        f"{summary['items_seen']} items seen, {summary['jobs_enqueued']} jobs enqueued."
    )


@app.command()
def worker(
    worker_id: str = typer.Option("worker-1", "--id", help="Worker instance identifier"),
    max_jobs: int = typer.Option(10, "--max-jobs", "-n", help="Maximum jobs to process before exiting"),
) -> None:
    """Run an asynchronous queue worker to process pending pipeline jobs."""
    console.print(f"[bold blue]Worker '{worker_id}' started. Listening for jobs...[/bold blue]")
    container = build_container()

    processed = 0
    while processed < max_jobs:
        job = container.job_queue.claim_next(worker_id)
        if not job:
            console.print("[yellow]No pending jobs in queue.[/yellow]")
            break

        console.print(f"Claimed job [bold]#{job.id}[/bold] (type='{job.job_type}')")
        try:
            result = container.dispatcher.handle(job)
            container.job_queue.mark_completed(job.id)
            console.print(f"[green]Job #{job.id} completed successfully:[/green] {result}")
        except Exception as exc:
            container.job_queue.mark_failed(job.id, str(exc))
            console.print(f"[red]Job #{job.id} failed:[/red] {exc}")

        processed += 1

    console.print(f"Worker completed {processed} jobs.")


@app.command()
def health() -> None:
    """Check connectivity to Supabase, LLM, and local environment."""
    container = build_container()
    table = Table(title="RegWatch System Health Check", show_header=True)
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details")

    # Supabase check
    has_supabase = bool(container.settings.supabase_url and container.settings.supabase_key)
    table.add_row(
        "Supabase Database",
        "[green]Configured[/green]" if has_supabase else "[yellow]Missing Credentials[/yellow]",
        container.settings.supabase_url or "Local in-memory fallback active",
    )

    # Groq LLM check
    has_groq = bool(container.settings.groq_api_key)
    table.add_row(
        "Groq AI Client",
        "[green]Ready[/green]" if has_groq else "[yellow]Missing API Key[/yellow]",
        f"Model: {container.settings.groq_model}",
    )

    # Sources loaded
    src_count = len(load_all_sources())
    table.add_row(
        "Registered Sources",
        "[green]Ready[/green]",
        f"{src_count} sources loaded from config/adapters",
    )

    console.print(table)


if __name__ == "__main__":
    app()
