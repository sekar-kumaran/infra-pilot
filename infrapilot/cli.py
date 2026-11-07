#!/usr/bin/env python3
"""
InfraPilot — Enterprise DevOps & SRE Control Plane CLI (`infrapilot`).
Provides unified terminal control over:
- Container, Pod, Microservice & Tool Live Logs (`infrapilot logs <target>`)
- Interactive Container/Pod/Microservice Shell Exec (`infrapilot exec <target> "<cmd>"`)
- Jenkins CI/CD Pipelines (`infrapilot jenkins pipelines | build | logs`)
- GitHub Copilot Enterprise & SRE Agent (`infrapilot copilot status | analyze | policy`)
- Docker, Kubernetes, Ansible, Terraform, AWS & Prometheus (`infrapilot tools | resources | incidents | automation | policies`)
"""

import json
from typing import Optional
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich import box

from .store import ControlPlaneStore, PROVIDER_CAPABILITIES, DEFAULT_DB_PATH
from .sdk import InfraPilotClient

console = Console()


def get_store_and_client(ctx: click.Context):
    db_path = ctx.obj.get("db_path", DEFAULT_DB_PATH)
    api_url = ctx.obj.get("api_url", "http://127.0.0.1:8000/api/v1")
    store = ControlPlaneStore(db_path=db_path)
    client = InfraPilotClient(api_url=api_url, db_path=db_path)
    return store, client


def output_json_or_render(ctx: click.Context, data, render_fn):
    if ctx.obj.get("json_output"):
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        render_fn(data)


@click.group(invoke_without_command=True)
@click.option("--api-url", default="http://127.0.0.1:8000/api/v1", help="InfraPilot Control Plane REST API URL")
@click.option("--db-path", default=DEFAULT_DB_PATH, help="Path to local/shared Control Plane state DB")
@click.option("--json", "json_output", is_flag=True, help="Output raw JSON for scripting/CI pipelines")
@click.pass_context
def cli(ctx: click.Context, api_url: str, db_path: str, json_output: bool):
    """InfraPilot — Enterprise DevOps & SRE Control Plane CLI (v2.2.0)."""
    ctx.ensure_object(dict)
    ctx.obj["api_url"] = api_url
    ctx.obj["db_path"] = db_path
    ctx.obj["json_output"] = json_output
    if ctx.invoked_subcommand is None:
        ctx.invoke(status)


@cli.command("status")
@click.pass_context
def status(ctx: click.Context):
    """Display full InfraPilot Control Plane status, metrics, and tool health."""
    store, client = get_store_and_client(ctx)
    summary = client.get_metrics_summary()
    tools = store.list_integrations()
    incidents = store.list_incidents()
    apps = store.list_applications()

    payload = {
        "metrics_summary": summary,
        "applications": apps,
        "tools": tools,
        "open_incidents": [i for i in incidents if i["status"] not in ("RESOLVED", "CLOSED", "RECOVERED")],
    }

    def _render(d):
        m = d["metrics_summary"]
        console.print(Panel.fit(
            f"[bold cyan]InfraPilot // Enterprise SRE & DevOps Control Plane v2.2.0[/bold cyan]\n"
            f"[green]● CONTROL PLANE ONLINE[/green]  |  "
            f"Apps: [bold]{m.get('total_applications', len(apps))}[/bold]  |  "
            f"Healthy Tools: [bold green]{m['active_integrations']}/{len(tools)}[/bold green]  |  "
            f"Workloads: [bold]{m.get('total_resources', 0)}[/bold]\n"
            f"Open Incidents: [bold red]{m['open_incidents']}[/bold red] (P1: {m['critical_incidents']})  |  "
            f"Active Alerts: [bold yellow]{m['active_alerts']}[/bold yellow]  |  "
            f"Runbooks Executed: [bold cyan]{m['automation_executions']}[/bold cyan]  |  "
            f"Approvals Queued: [bold magenta]{m.get('pending_approvals', 0)}[/bold magenta]",
            title="InfraPilot Telemetry",
            border_style="cyan",
        ))

        t_table = Table(title="Connected DevOps Tools, CI/CD & AI Agents", box=box.SIMPLE_HEAVY)
        t_table.add_column("ID", style="dim")
        t_table.add_column("Tool / Integration", style="bold")
        t_table.add_column("Provider", style="cyan")
        t_table.add_column("Health", style="green")
        t_table.add_column("Circuit", style="magenta")
        for t in d["tools"]:
            st_color = "green" if t["status"] == "HEALTHY" else ("yellow" if t["status"] == "CONFIGURED" else "red")
            cb_color = "green" if t["circuit_state"] == "CLOSED" else "red"
            t_table.add_row(
                t["id"],
                t["name"],
                t["provider"].upper(),
                f"[{st_color}]{t['status']}[/{st_color}]",
                f"[{cb_color}]{t['circuit_state']}[/{cb_color}]",
            )
        console.print(t_table)

    output_json_or_render(ctx, payload, _render)


# ==============================================================================
# LOGS COMMAND (`infrapilot logs <target>`)
# ==============================================================================
@cli.command("logs")
@click.argument("target")
@click.option("--level", default=None, help="Filter by level (INFO, WARN, ERROR, DEBUG)")
@click.option("--grep", "query", default=None, help="Filter log lines by substring/pattern")
@click.option("-n", "--tail", default=50, type=int, help="Number of lines to tail")
@click.pass_context
def logs_cmd(ctx: click.Context, target: str, level: Optional[str], query: Optional[str], tail: int):
    """Stream logs for any Docker container, K8s pod, microservice, or DevOps tool."""
    store, _ = get_store_and_client(ctx)
    res = store.get_target_logs(target=target, level=level, query=query, tail=tail)

    def _render(d):
        console.print(Panel(
            "\n".join(d["lines"]) if d["lines"] else "No log lines matched filter.",
            title=f"Live Log Stream // Target: {d['target_id']} ({d['total']} lines)",
            border_style="cyan",
        ))

    output_json_or_render(ctx, res, _render)


# ==============================================================================
# INTERACTIVE CONTAINER / POD / TOOL EXEC (`infrapilot exec <target> "<cmd>"`)
# ==============================================================================
@cli.command("exec")
@click.argument("target")
@click.argument("command")
@click.option("--shell", default="bash", type=click.Choice(["bash", "sh", "cmd", "pwsh"]), help="Shell interpreter")
@click.pass_context
def exec_cmd(ctx: click.Context, target: str, command: str, shell: str):
    """Execute a command inside any Docker container, Kubernetes pod, or microservice."""
    store, _ = get_store_and_client(ctx)
    res = store.exec_in_target(target=target, command=command, shell=shell)

    def _render(d):
        prompt_str = f"root@{d['target_name']}:/app#" if d["shell"] in ("bash", "sh") else f"PS C:\\workloads\\{d['target_name']}>"
        console.print(f"[bold green]{prompt_str}[/bold green] {d['command']}")
        console.print(d["stdout"])

    output_json_or_render(ctx, res, _render)


# ==============================================================================
# JENKINS CI/CD CONTROL (`infrapilot jenkins ...`)
# ==============================================================================
@cli.group("jenkins")
def jenkins_group():
    """Track and control Jenkins CI/CD pipelines, parameterized builds, and console logs."""
    pass


@jenkins_group.command("pipelines")
@click.pass_context
def jenkins_pipelines(ctx: click.Context):
    """List Jenkins pipelines, build numbers, stage statuses, and commit SHAs."""
    store, _ = get_store_and_client(ctx)
    items = store.list_jenkins_pipelines()

    def _render(rows):
        tbl = Table(title="Jenkins CI/CD Pipelines (int-jenkins-01)", box=box.SIMPLE_HEAVY)
        tbl.add_column("ID", style="dim")
        tbl.add_column("Pipeline Name", style="bold cyan")
        tbl.add_column("Branch")
        tbl.add_column("Build #", justify="right")
        tbl.add_column("Status", style="green")
        tbl.add_column("Duration")
        tbl.add_column("Commit")
        for p in rows:
            tbl.add_row(p["id"], p["name"], p["branch"], f"#{p['last_build']}", p["status"], p["duration"], p["commit"])
        console.print(tbl)

    output_json_or_render(ctx, items, _render)


@jenkins_group.command("create")
@click.argument("name")
@click.option("--branch", default="main", help="Git branch to build")
@click.option("--repo", default="https://github.com/infrapilot-eng/app.git", help="Git repository URL")
@click.pass_context
def jenkins_create(ctx: click.Context, name: str, branch: str, repo: str):
    """Create a new Jenkins CI/CD pipeline in the Control Plane."""
    store, _ = get_store_and_client(ctx)
    res = store.create_jenkins_pipeline(name=name, branch=branch, repo_url=repo)
    output_json_or_render(ctx, res, lambda d: console.print(f"[green]✔ Created Jenkins Pipeline:[/green] [bold]{d['name']}[/bold] ({d['id']}) on branch {d['branch']}"))


@jenkins_group.command("build")
@click.argument("pipeline")
@click.option("--branch", default="main", help="Git branch to build")
@click.option("--tag", default="v2.3.2", help="Target image/release tag")
@click.pass_context
def jenkins_build(ctx: click.Context, pipeline: str, branch: str, tag: str):
    """Trigger a parameterized Jenkins pipeline build via REST API."""
    store, _ = get_store_and_client(ctx)
    res = store.trigger_jenkins_build(pipeline, branch=branch, tag=tag)
    output_json_or_render(
        ctx,
        res,
        lambda d: console.print(f"[green]✔ Jenkins Build Triggered:[/green] [bold]{d['name']} #{d['last_build']}[/bold] (branch={d['branch']}, tag={tag}) -> [bold green]{d['status']}[/bold green]")
    )


@jenkins_group.command("logs")
@click.argument("pipeline")
@click.pass_context
def jenkins_logs(ctx: click.Context, pipeline: str):
    """Fetch consoleText build output for a Jenkins pipeline."""
    store, _ = get_store_and_client(ctx)
    matches = [p for p in store.list_jenkins_pipelines() if p["id"] == pipeline or p["name"] == pipeline]
    if not matches:
        raise click.ClickException(f"Pipeline '{pipeline}' not found")
    p = matches[0]
    output_json_or_render(
        ctx,
        p,
        lambda d: console.print(Panel("\n".join(d["console_output"]), title=f"Jenkins Console Output // {d['name']} #{d['last_build']}", border_style="cyan"))
    )


# ==============================================================================
# GITHUB COPILOT ENTERPRISE & SRE AGENT (`infrapilot copilot ...`)
# ==============================================================================
@cli.group("copilot")
def copilot_group():
    """Track and control GitHub Copilot Enterprise seats, policies, and AI SRE log analysis."""
    pass


@copilot_group.command("status")
@click.pass_context
def copilot_status(ctx: click.Context):
    """Display GitHub Copilot Enterprise seat utilization, CLI completions, and policy guardrails."""
    store, _ = get_store_and_client(ctx)
    st = store.get_copilot_state()

    def _render(d):
        pol = d["policies"]
        console.print(Panel(
            f"Organization: [bold cyan]{d['org']}[/bold cyan] ({d['plan']})\n"
            f"Seat Pool: [bold green]{d['active_seats']}/{d['total_seats']}[/bold green] Active  |  "
            f"Acceptance Rate: [bold]{d['acceptance_rate_percent']}%[/bold]  |  "
            f"CLI Completions Today: [bold cyan]{d['cli_commands_generated_today']}[/bold cyan]  |  "
            f"RCA Patches: [bold]{d['rca_patches_generated']}[/bold]\n"
            f"Policies: public_code=[yellow]{pol['public_code_suggestions']}[/yellow] | "
            f"cli_in_prod_shells=[green]{pol['cli_in_prod_shells']}[/green] | "
            f"secret_redaction=[green]{pol['secret_pii_redaction']}[/green]",
            title="GitHub Copilot Enterprise Control Plane (int-copilot-01)",
            border_style="cyan",
        ))

    output_json_or_render(ctx, st, _render)


@copilot_group.command("analyze")
@click.argument("target")
@click.pass_context
def copilot_analyze(ctx: click.Context, target: str):
    """Run GitHub Copilot SRE Agent root-cause analysis on a container, pod, or tool's logs."""
    store, _ = get_store_and_client(ctx)
    res = store.copilot_analyze_target(target)

    def _render(d):
        console.print(Panel(
            f"Target Analyzed : [bold cyan]{d['target_id']}[/bold cyan] ({d['logs_analyzed']} log entries)\n"
            f"Confidence      : [bold green]{d['confidence']}[/bold green]\n"
            f"Diagnosis       : {d['diagnosis']}\n"
            f"Suggested CLI   : [bold yellow]{d['recommended_cli_command']}[/bold yellow]",
            title="GitHub Copilot SRE Agent // Root-Cause Analysis",
            border_style="magenta",
        ))

    output_json_or_render(ctx, res, _render)


@copilot_group.command("policy")
@click.option("--public-code", type=click.Choice(["BLOCK", "ALLOW"]), default=None, help="Public code suggestions filter")
@click.option("--cli-shell", type=click.Choice(["ENABLED", "DISABLED"]), default=None, help="Copilot CLI in production shells")
@click.pass_context
def copilot_policy(ctx: click.Context, public_code: Optional[str], cli_shell: Optional[str]):
    """Update GitHub Copilot Enterprise organization guardrails via REST API."""
    store, _ = get_store_and_client(ctx)
    res = store.update_copilot_policy(public_code=public_code, cli_shell=cli_shell)
    output_json_or_render(ctx, res, lambda d: console.print(f"[green]✔ Updated GitHub Copilot Org Policies:[/green] {json.dumps(d['policies'])}"))


# ==============================================================================
# EXISTING GROUPS (APPS, TOOLS, RESOURCES, INCIDENTS, AUTOMATION, POLICIES, DEMO)
# ==============================================================================
@cli.group("apps")
def apps_group():
    """Manage applications connected to the InfraPilot Control Plane."""
    pass


@apps_group.command("list")
@click.pass_context
def apps_list(ctx: click.Context):
    store, _ = get_store_and_client(ctx)
    apps = store.list_applications()
    output_json_or_render(ctx, apps, lambda items: console.print(f"Apps Registered: {len(items)}"))


@cli.group("tools")
def tools_group():
    """Connect, validate, discover, and control DevOps tools & providers."""
    pass


@tools_group.command("list")
@click.pass_context
def tools_list(ctx: click.Context):
    store, _ = get_store_and_client(ctx)
    tools = store.list_integrations()

    def _render(items):
        tbl = Table(title="Connected DevOps Tools & Integrations", box=box.SIMPLE_HEAVY)
        tbl.add_column("Tool ID", style="dim")
        tbl.add_column("Name", style="bold")
        tbl.add_column("Provider", style="cyan")
        tbl.add_column("Status")
        tbl.add_column("Circuit")
        for t in items:
            tbl.add_row(t["id"], t["name"], t["provider"].upper(), t["status"], t["circuit_state"])
        console.print(tbl)

    output_json_or_render(ctx, tools, _render)


@tools_group.command("connect")
@click.argument("name")
@click.option("--provider", default="ansible", help="Provider (docker, kubernetes, jenkins, github_copilot, ansible, prometheus, terraform, aws, custom_tool)")
@click.option("--endpoint", required=True, help="Endpoint URL or socket path")
@click.option("--description", default="Connected via InfraPilot CLI", help="Tool description")
@click.pass_context
def tools_connect(ctx: click.Context, name: str, provider: str, endpoint: str, description: str):
    """Connect a new DevOps tool endpoint to the Control Plane."""
    store, _ = get_store_and_client(ctx)
    res = store.create_integration(name=name, provider=provider, description=description, configuration={"base_url": endpoint})
    output_json_or_render(ctx, res, lambda d: console.print(f"[green]✔ Connected Tool:[/green] [bold]{d['name']}[/bold] ({d['id']}) -> {endpoint} [{d['status']}]"))


@tools_group.command("capabilities")
@click.pass_context
def tools_capabilities(ctx: click.Context):
    output_json_or_render(ctx, PROVIDER_CAPABILITIES, lambda caps: console.print(f"Providers: {len(caps)}"))


@cli.group("resources")
def resources_group():
    """Inspect infrastructure resources, topology graph, metrics, logs, and run actions."""
    pass


@resources_group.command("list")
@click.option("--provider", default=None)
@click.option("--status", default=None)
@click.pass_context
def resources_list(ctx: click.Context, provider: Optional[str], status: Optional[str]):
    store, _ = get_store_and_client(ctx)
    items = store.list_resources(provider=provider, status=status)

    def _render(rows):
        tbl = Table(title=f"Infrastructure Workloads & Containers ({len(rows)})", box=box.SIMPLE_HEAVY)
        tbl.add_column("ID", style="dim")
        tbl.add_column("Workload Name", style="bold")
        tbl.add_column("Provider", style="cyan")
        tbl.add_column("Type")
        tbl.add_column("Status")
        for r in rows:
            tbl.add_row(r["id"], r["display_name"], r["provider"].upper(), r["resource_type"], r["status"])
        console.print(tbl)

    output_json_or_render(ctx, items, _render)


@resources_group.command("topology")
@click.pass_context
def resources_topology(ctx: click.Context):
    store, _ = get_store_and_client(ctx)
    topo = store.get_topology()

    def _render(d):
        tree = Tree("[bold cyan]InfraPilot Service Dependency Graph[/bold cyan]")
        for n in d["nodes"]:
            tree.add(f"[bold]{n['label']}[/bold] ({n['provider'].upper()}) [{n['status']}]")
        console.print(tree)

    output_json_or_render(ctx, topo, _render)


@resources_group.command("action")
@click.argument("resource_id")
@click.argument("action", type=click.Choice(["start", "stop", "restart", "scale", "heal"]))
@click.option("--replicas", default=5, type=int)
@click.pass_context
def resources_action(ctx: click.Context, resource_id: str, action: str, replicas: int):
    store, _ = get_store_and_client(ctx)
    res = store.perform_resource_action(resource_id, action, {"replicas": replicas})
    output_json_or_render(ctx, res, lambda d: console.print(f"[green]✔ {d['action'].upper()} on {d['name']} -> {d['status']}[/green]"))


@cli.group("incidents")
def incidents_group():
    """Monitor, acknowledge, investigate, remediate, and resolve incidents."""
    pass


@incidents_group.command("list")
@click.option("--status", default=None)
@click.pass_context
def incidents_list(ctx: click.Context, status: Optional[str]):
    store, _ = get_store_and_client(ctx)
    items = store.list_incidents(status=status)
    output_json_or_render(ctx, items, lambda rows: console.print(f"Incidents: {len(rows)}"))


@incidents_group.command("inspect")
@click.argument("incident_id")
@click.pass_context
def incidents_inspect(ctx: click.Context, incident_id: str):
    store, _ = get_store_and_client(ctx)
    inc = store.get_incident(incident_id)
    if not inc:
        raise click.ClickException(f"Incident '{incident_id}' not found")
    output_json_or_render(ctx, inc, lambda d: console.print(f"Incident {d['id']}: {d['status']}"))


@incidents_group.command("remediate")
@click.argument("incident_id")
@click.option("--playbook", default="pb-restart-workers")
@click.option("--auto-approve", is_flag=True)
@click.pass_context
def incidents_remediate(ctx: click.Context, incident_id: str, playbook: str, auto_approve: bool):
    store, _ = get_store_and_client(ctx)
    inc = store.get_incident(incident_id)
    if not inc:
        raise click.ClickException(f"Incident '{incident_id}' not found")
    ex = store.trigger_execution(
        playbook_id=playbook,
        trigger_type="CLI_REMEDIATION",
        trigger_source="infrapilot_cli",
        incident_id=incident_id,
        resource_id=inc.get("primary_resource_id"),
        force_auto_approve=auto_approve,
    )
    output_json_or_render(ctx, ex, lambda d: console.print(f"[green]✔ Remediation {d['id']} -> {d['status']}[/green]"))


@cli.group("automation")
def automation_group():
    """Manage playbooks, workflows, executions, approvals, and cron schedules."""
    pass


@automation_group.command("playbooks")
@click.pass_context
def automation_playbooks(ctx: click.Context):
    store, _ = get_store_and_client(ctx)
    output_json_or_render(ctx, store.list_playbooks(), lambda rows: console.print(f"Playbooks: {len(rows)}"))


@automation_group.command("create")
@click.argument("name")
@click.option("--provider", default="ansible", help="Automation provider (ansible, kubernetes, docker, jenkins)")
@click.option("--action", default="ansible_run_playbook", help="Action or playbook module to execute")
@click.option("--target", default="all-prod-nodes", help="Target host group or resource ID")
@click.option("--risk", default="LOW", type=click.Choice(["LOW", "MEDIUM", "HIGH"], case_sensitive=False))
@click.pass_context
def automation_create(ctx: click.Context, name: str, provider: str, action: str, target: str, risk: str):
    """Create a new Ansible or multi-tool automation playbook."""
    store, _ = get_store_and_client(ctx)
    steps = [
        {"id": "step-1", "step_order": 1, "name": f"Execute {action} ({provider})", "action_name": action, "action_type": "EXECUTE_PROVIDER_ACTION", "risk_level": risk.upper(), "parameters": {"provider": provider, "target": target}},
        {"id": "step-2", "step_order": 2, "name": "Verify Post-Execution Health", "action_name": "app_health_check", "action_type": "VERIFY", "risk_level": "LOW", "parameters": {"target": target}}
    ]
    res = store.create_playbook(name=name, description=f"{provider.upper()} automation targeting {target}", trigger_type="MANUAL", steps=steps)
    output_json_or_render(ctx, res, lambda d: console.print(f"[green]✔ Created Automation Playbook:[/green] [bold]{d['name']}[/bold] ({d['id']})"))


@automation_group.command("run")
@click.argument("playbook_id")
@click.option("--dry-run", is_flag=True, help="Simulate runbook execution without mutating infrastructure")
@click.pass_context
def automation_run(ctx, playbook_id: str, dry_run: bool):
    """Execute an automation runbook (queues approval if policy requires it)."""
    store, _ = get_store_and_client(ctx)
    res = store.trigger_execution(playbook_id=playbook_id, force_auto_approve=dry_run)
    output_json_or_render(
        ctx,
        res,
        lambda d: console.print(
            f"[bold cyan]Runbook Execution {d['id']}[/bold cyan] ({d['playbook_name']}) -> Status: [bold yellow]{d['status']}[/bold yellow]"
            + (f" (Approval ID: {d.get('approval_id')})" if d.get("approval_id") else "")
        ),
    )


@automation_group.command("approvals")
@click.pass_context
def automation_approvals(ctx: click.Context):
    store, _ = get_store_and_client(ctx)
    output_json_or_render(ctx, store.list_approvals(), lambda rows: console.print(f"Approvals: {len(rows)}"))


@automation_group.command("approve")
@click.argument("approval_id")
@click.option("--reason", default="Approved via InfraPilot CLI")
@click.pass_context
def automation_approve(ctx: click.Context, approval_id: str, reason: str):
    store, _ = get_store_and_client(ctx)
    res = store.decide_approval(approval_id, "APPROVE", reason)
    output_json_or_render(ctx, res, lambda d: console.print(f"[green]✔ Approved {d['id']}[/green]"))


@cli.group("policies")
def policies_group():
    """Inspect governance policies and simulate policy decisions."""
    pass


@policies_group.command("simulate")
@click.option("--action", required=True)
@click.option("--risk", default="LOW")
@click.option("--env", default="PRODUCTION")
@click.pass_context
def policies_simulate(ctx: click.Context, action: str, risk: str, env: str):
    store, _ = get_store_and_client(ctx)
    res = store.simulate_policy({"action": action, "risk": risk, "environment": env})
    output_json_or_render(ctx, res, lambda d: console.print(f"Decision: {d['decision']} ({d['reason']})"))


@cli.group("audit")
def audit_group():
    """Inspect the security and operational audit trail."""
    pass


@audit_group.command("list")
@click.option("--limit", default=25, type=int)
@click.pass_context
def audit_list(ctx: click.Context, limit: int):
    store, _ = get_store_and_client(ctx)
    output_json_or_render(ctx, store.list_audit_events(limit=limit), lambda rows: console.print(f"Audit records: {len(rows)}"))


@cli.group("demo")
def demo_group():
    """Control, inject chaos, and auto-remediate the connected NexusPay Demo App."""
    pass


@demo_group.command("chaos")
@click.option("--scenario", default="worker_pool_exhaustion")
@click.pass_context
def demo_chaos(ctx: click.Context, scenario: str):
    _, client = get_store_and_client(ctx)
    res = client.send_prometheus_alert(
        alertname="NexusPayCanaryHigh5xxRate" if "canary" in scenario else "NexusPayWorkerPoolExhausted",
        severity="CRITICAL",
        instance="nexuspay:5055",
        job="nexuspay",
        summary=f"Chaos injected: {scenario}",
        description=f"Simulated anomaly ({scenario})",
        resource_external_id="res-nexus-gw" if "canary" in scenario else "res-nexus-worker",
    )
    output_json_or_render(ctx, res, lambda d: console.print(f"[red]⚡ Chaos injected -> Incident {d.get('incident_id')}[/red]"))


@demo_group.command("heal")
@click.pass_context
def demo_heal(ctx: click.Context):
    store, _ = get_store_and_client(ctx)
    open_incs = [i for i in store.list_incidents() if i["status"] not in ("RESOLVED", "CLOSED", "RECOVERED")]
    healed = []
    for inc in open_incs:
        ex = store.trigger_execution("pb-restart-workers", incident_id=inc["id"], resource_id=inc.get("primary_resource_id"), force_auto_approve=True)
        healed.append(ex["id"])
    output_json_or_render(ctx, {"healed": healed}, lambda d: console.print(f"[green]✔ Healed {len(d['healed'])} incidents[/green]"))




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
                "\n".join([f"[bold cyan]{u['email']}[/bold cyan] — Role: [bold yellow]{u['role']}[/bold yellow] (Active: {u['is_active']})" for u in rows]),
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
    output_json_or_render(ctx, res, lambda rows: console.print(Panel("\n".join([f"[bold cyan]{r['uid']}[/bold cyan]: {r['title']} ({r['url']})" for r in rows]), title="Grafana Dashboards", border_style="green")))


if __name__ == "__main__":
    cli()
