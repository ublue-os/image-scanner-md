import typer
import arrow
from dotenv import load_dotenv
from ghapi.all import GhApi
from ghapi.core import print_summary
from ghapi.page import paged
from rich.table import Table
from rich.console import Console


app = typer.Typer()
load_dotenv()


@app.command()
def scan(
    gh_token: str = typer.Option(
        ...,
        help="The github token to use to hit the GH API",
        envvar=["GITHUB_TOKEN"],
    ),
    org: str = typer.Option(..., help="The org to fetch image from"),
):
    gh = GhApi(token=gh_token)
    paged_packages = paged(
        gh.packages.list_packages_for_organization,
        org=org,
        package_type="container",
        state="active",
        per_page=1000,
    )
    console = Console()
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Image Name")
    table.add_column("Description")
    table.add_column("Stars")
    table.add_column("Forks")
    table.add_column("Updated At")
    table.add_column("URL")
    seen_packages = []
    has_pages = True
    while has_pages:
        page = next(paged_packages)
        for package in page:
            package_id = int(package['id'])
            if package_id in seen_packages:
                has_pages = False
                continue
            seen_packages.append(package_id)
            owner = package['owner']['login']
            owner_url = package['owner']['html_url']
            image_name = package['name']
            repo_url = package['repository']['html_url']
            repo_name = package['repository']['name']
            repo_details = gh.repos.get(owner=owner, repo=repo_name)
            repo_description = repo_details['description']
            stars = repo_details['stargazers_count']
            forks = repo_details['forks']
            updated_at = arrow.get(repo_details['updated_at'])

            table.add_row(image_name, repo_description, str(stars), str(forks), updated_at.humanize(), repo_url)
    console.print(table)
