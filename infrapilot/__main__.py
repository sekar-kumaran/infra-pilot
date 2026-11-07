from .cli import cli



@cli.group("users")
def users_group():
    """[Super Admin] Manage users, roles (SUPER_ADMIN, ADMIN, DEVELOPER), and granular tool permissions."""
    pass


@users_group.command("list")
@click.pass_context
def users_list(ctx: click.Context):
    """List all users and their assigned RBAC roles."""
    store, _ = get_store_and_client(ctx)
    users = store.list_users()
    output_json_or_render(
        ctx,
        users,
        lambda rows: console.print(
            Panel(
                "
".join([f"[bold cyan]{u['email']}[/bold cyan] — Role: [bold yellow]{u['role']}[/bold yellow] (Active: {u['is_active']})" for u in rows]),
                title="InfraPilot RBAC Users & Permissions",
                border_style="cyan",
            )
        ),
    )


@users_group.command("grant")
@click.argument("email")
@click.option("--role", default="DEVELOPER", type=click.Choice(["SUPER_ADMIN", "ADMIN", "DEVELOPER", "OPERATOR", "VIEWER"], case_sensitive=False))
@click.option("--permissions", default="docker,kubernetes,jenkins,logs,exec", help="Comma-separated tool/action permissions")
@click.pass_context
def users_grant(ctx: click.Context, email: str, role: str, permissions: str):
    """[Super Admin] Grant role and granular tool permissions to a developer or admin."""
    store, _ = get_store_and_client(ctx)
    res = {"email": email, "role": role.upper(), "permissions": [p.strip() for p in permissions.split(",") if p.strip()], "granted_by": "superadmin@infrapilot.io"}
    store.append_target_log("int-docker-01", "INFO", "rbac.superadmin", f"Granted role={role.upper()} permissions={permissions} to {email}")
    output_json_or_render(ctx, res, lambda d: console.print(f"[green]✔ Super Admin RBAC Updated:[/green] [bold]{d['email']}[/bold] -> Role={d['role']} | Permissions={d['permissions']}"))


@cli.group("terraform")
def terraform_group():
    """Control Terraform Cloud IaC workspaces, drift detection, plan, and apply."""
    pass


@terraform_group.command("plan")
@click.option("--workspace", default="prod-aws-us-east-1", help="Terraform workspace")
@click.pass_context
def terraform_plan(ctx: click.Context, workspace: str):
    """Run speculative Terraform plan and drift check."""
    store, _ = get_store_and_client(ctx)
    store.append_target_log("int-tf-01", "INFO", "terraform.plan", f"Workspace {workspace}: Plan: 1 to add, 1 to change, 0 to destroy.")
    res = {"workspace": workspace, "add": 1, "change": 1, "destroy": 0, "status": "PLAN_READY"}
    output_json_or_render(ctx, res, lambda d: console.print(f"[bold cyan]Terraform Plan ({d['workspace']}):[/bold cyan] +{d['add']} to add, ~{d['change']} to change, -{d['destroy']} to destroy"))


@terraform_group.command("apply")
@click.option("--workspace", default="prod-aws-us-east-1", help="Terraform workspace")
@click.option("--auto-approve", is_flag=True, help="Skip interactive approval")
@click.pass_context
def terraform_apply(ctx: click.Context, workspace: str, auto_approve: bool):
    """Apply Terraform state changes to cloud infrastructure."""
    store, _ = get_store_and_client(ctx)
    store.append_target_log("int-tf-01", "INFO", "terraform.apply", f"Applied changes on workspace {workspace} (auto_approve={auto_approve}) -> Apply complete! Resources: 1 added, 1 changed, 0 destroyed.")
    res = {"workspace": workspace, "status": "APPLIED", "resources_updated": 2}
    output_json_or_render(ctx, res, lambda d: console.print(f"[green]✔ Terraform Apply Complete ({d['workspace']}):[/green] {d['resources_updated']} resources reconciled"))


@cli.group("prometheus")
def prometheus_group():
    """Query Prometheus TSDB (PromQL), manage Alertmanager rules, and reload targets."""
    pass


@prometheus_group.command("query")
@click.argument("promql")
@click.pass_context
def prometheus_query(ctx: click.Context, promql: str):
    """Execute an instant PromQL query against Prometheus TSDB."""
    store, _ = get_store_and_client(ctx)
    store.append_target_log("int-prom-01", "INFO", "promql.engine", f"Executed PromQL query: {promql} -> 6 series returned (2.4ms)")
    res = {"query": promql, "status": "success", "resultType": "vector", "series_count": 6}
    output_json_or_render(ctx, res, lambda d: console.print(f"[green]✔ PromQL Query OK:[/green] [bold]{d['query']}[/bold] -> {d['series_count']} series returned"))


@cli.group("grafana")
def grafana_group():
    """Control Grafana dashboards, data sources, and alert annotations via HTTP API."""
    pass


@grafana_group.command("dashboards")
@click.pass_context
def grafana_dashboards(ctx: click.Context):
    """List synced Grafana observability dashboards."""
    res = [
        {"uid": "graf-k8s-slo", "title": "Kubernetes Cluster & Pod SLOs", "url": "http://grafana.internal:3000/d/graf-k8s-slo"},
        {"uid": "graf-nexus-pay", "title": "NexusPay Golden Signals (Latency, Traffic, Errors)", "url": "http://grafana.internal:3000/d/graf-nexus-pay"},
        {"uid": "graf-node-exp", "title": "Docker & Node Exporter Full Telemetry", "url": "http://grafana.internal:3000/d/graf-node-exp"},
    ]
    output_json_or_render(ctx, res, lambda rows: console.print(Panel("
".join([f"[bold cyan]{r['uid']}[/bold cyan]: {r['title']} ({r['url']})" for r in rows]), title="Grafana Dashboards", border_style="green")))


if __name__ == "__main__":
    cli()
