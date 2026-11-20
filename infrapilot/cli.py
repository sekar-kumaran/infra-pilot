"""InfraPilot v2.6.0 Production CLI (`infrapilot`)."""
import json
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from .store import ControlPlaneStore, DEFAULT_DB_PATH

console = Console()


@click.group()
@click.option("--db-path", default=DEFAULT_DB_PATH, help="SQLite state DB path")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
@click.pass_context
def cli(ctx: click.Context, db_path: str, as_json: bool):
    """InfraPilot v2.6.0 — Production DevOps & SRE Control Plane CLI."""
    ctx.ensure_object(dict)
    ctx.obj["store"] = ControlPlaneStore(db_path=db_path)
    ctx.obj["json"] = as_json


@cli.group("auth")
def auth_group():
    """Authenticate and manage user passwords (default bootstrap: admin / admin)."""
    pass


@auth_group.command("login")
@click.option("-u", "--username", default="admin", help="Username or email")
@click.option("-p", "--password", required=True, help="Password")
@click.pass_context
def auth_login(ctx: click.Context, username: str, password: str):
    store: ControlPlaneStore = ctx.obj["store"]
    user = store.authenticate(username, password)
    if not user:
        raise click.ClickException("Authentication failed. Invalid username or password.")
    if ctx.obj["json"]:
        click.echo(json.dumps(user, indent=2))
        return
    console.print(f"[green]✔ Authenticated as:[/green] [bold]{user['username']}[/bold] (Role: {user['role']})")
    if user["must_change_password"]:
        console.print("[yellow]⚠ First-login security policy: Please update your password using `infrapilot auth passwd`.[/yellow]")


@auth_group.command("passwd")
@click.option("-u", "--username", default="admin", help="Username")
@click.option("-c", "--current-password", required=True, help="Current password")
@click.option("-n", "--new-password", required=True, help="New password")
@click.pass_context
def auth_passwd(ctx: click.Context, username: str, current_password: str, new_password: str):
    store: ControlPlaneStore = ctx.obj["store"]
    user = store.change_password(username, current_password, new_password)
    if ctx.obj["json"]:
        click.echo(json.dumps(user, indent=2))
        return
    console.print(f"[green]✔ Password updated for {user['username']}. First-login lock cleared.[/green]")


@cli.command("status")
@click.pass_context
def cmd_status(ctx: click.Context):
    store: ControlPlaneStore = ctx.obj["store"]
    tools = store.list_integrations()
    workloads = store.list_resources()
    data = {"status": "ONLINE", "version": "2.6.0", "connected_tools": len(tools), "workloads": len(workloads)}
    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
        return
    console.print(
        Panel(
            f"[bold cyan]InfraPilot Control Plane v2.6.0[/bold cyan]  |  [bold green]● ONLINE[/bold green]\n"
            f"Connected Tools: [bold]{len(tools)}[/bold]  |  Registered Workloads: [bold]{len(workloads)}[/bold]",
            title="InfraPilot Production Status",
            border_style="cyan",
        )
    )


@cli.group("tools")
def tools_group():
    """Connect and manage DevOps tool endpoints."""
    pass


@tools_group.command("list")
@click.pass_context
def tools_list(ctx: click.Context):
    store: ControlPlaneStore = ctx.obj["store"]
    rows = store.list_integrations()
    if ctx.obj["json"]:
        click.echo(json.dumps(rows, indent=2))
        return
    if not rows:
        console.print("[dim]No tools connected yet. Run `infrapilot tools connect <name> --provider <type> --endpoint <url>`.[/dim]")
        return
    for r in rows:
        console.print(f"[cyan]{r['id']}[/cyan]  [bold]{r['name']}[/bold] ({r['provider']}) -> {r['endpoint']} [{r['status']}]")


@tools_group.command("connect")
@click.argument("name")
@click.option("--provider", default="docker", help="Provider type")
@click.option("--endpoint", required=True, help="Endpoint URL or socket")
@click.option("--description", default="", help="Description")
@click.pass_context
def tools_connect(ctx: click.Context, name: str, provider: str, endpoint: str, description: str):
    store: ControlPlaneStore = ctx.obj["store"]
    res = store.create_integration(name=name, provider=provider, endpoint=endpoint, description=description)
    if ctx.obj["json"]:
        click.echo(json.dumps(res, indent=2))
        return
    console.print(f"[green]✔ Connected Tool:[/green] [bold]{res['name']}[/bold] ({res['id']}) -> {res['endpoint']}")


@cli.command("doctor")
@click.pass_context
def cmd_doctor(ctx: click.Context):
    store: ControlPlaneStore = ctx.obj["store"]
    checks = store.run_preflight_doctor()
    if ctx.obj["json"]:
        click.echo(json.dumps(checks, indent=2))
        return
    for c in checks:
        console.print(f"[green]✔ {c['id']}[/green] {c['issue']}: [bold green]{c['status']}[/bold green]")


if __name__ == "__main__":
    cli()
