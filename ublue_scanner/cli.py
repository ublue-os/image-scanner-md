import typer
import arrow
from enum import Enum
from dotenv import load_dotenv
from ghapi.all import GhApi
from ghapi.core import print_summary
from ghapi.page import paged
from rich.table import Table
from rich.console import Console
from ruamel.yaml import YAML
yaml = YAML()


app = typer.Typer()
load_dotenv()

class OutputOptions(str, Enum):
    cli = "cli"
    markdown = "md"

@app.command()
def scan(
    gh_token: str = typer.Option(
        ...,
        help="The github token to use to hit the GH API",
        envvar=["GITHUB_TOKEN"],
    ),
    org: str = typer.Option(..., help="The org to fetch image from"),
    output: OutputOptions = typer.Option(
        OutputOptions.cli,
        help="How to output the data",
    ),
    config: str = typer.Option(
        None,
        help="Config file for the CLI",
    ),
):
    settings = None

    if config:
        with open(config) as f:
            settings = yaml.load(f.read())

    gh = GhApi(token=gh_token)
    paged_packages = paged(
        gh.packages.list_packages_for_organization,
        org=org,
        package_type="container",
        state="active",
        per_page=1000,
    )
    seen_packages = []
    has_pages = True
    rows = []

    while has_pages:
        page = next(paged_packages)
        for package in page:
            package_id = int(package["id"])
            if package_id in seen_packages:
                has_pages = False
                continue

            seen_packages.append(package_id)
            owner = package["owner"]["login"]
            owner_url = package["owner"]["html_url"]
            image_name = package["name"]
            repo_url = package["repository"]["html_url"]
            repo_name = package["repository"]["name"]
            repo_details = gh.repos.get(owner=owner, repo=repo_name)
            repo_description = repo_details["description"]
            stars = repo_details["stargazers_count"]
            forks = repo_details["forks"]
            updated_at = arrow.get(repo_details["updated_at"])

            if settings and len(settings["ignores"]) > 0:
                if image_name in settings["ignores"]:
                    continue

            rows.append(
                (
                    image_name,
                    repo_description,
                    str(stars),
                    str(forks),
                    updated_at.humanize(),
                    repo_url,
                )
            )

    sorted_rows = sorted(rows, key=lambda tup: tup[0])
    if output == OutputOptions.cli:
        console = Console()
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Image Name")
        table.add_column("Description")
        table.add_column("Stars")
        table.add_column("Forks")
        table.add_column("Updated At")
        table.add_column("URL")

        for row in sorted_rows:
            table.add_row(*row)
        console.print(table)
    elif output == OutputOptions.markdown:
        for row in sorted_rows:
            image_name = row[0]
            description = row[1]
            stars = row[2]
            forks = row[3]
            updated_at = row[4]
            url = row[5]
            content = f"""\
# {image_name} 
{description}  
*Stars*: {stars}  
*Forks*: {forks}  
*Last Updated*: {updated_at}  
[Repo]({url})
"""
            typer.echo(content)
    else:
        typer.echo("Sorry, don't understand output option")
