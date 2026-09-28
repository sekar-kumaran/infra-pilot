#!/usr/bin/env python3
"""
Real Docker Provider Acceptance Test for InfraPilot Phase 1.17.

Configuration via environment variables:
  DOCKER_REAL_URL        Docker Engine API URL (e.g. http://192.168.1.10:2375)
  DOCKER_REAL_TLS_VERIFY Whether to verify TLS (default: false)
  DOCKER_REAL_TIMEOUT    Request timeout in seconds (default: 10)
  DOCKER_REAL_ALLOW_MUTATION  Set to 'true' to allow restart operation (default: off)
  DOCKER_REAL_TARGET_CONTAINER  Container name/ID to use for mutation (required if mutation is enabled)

Usage:
  DOCKER_REAL_URL=http://docker-host:2375 python scripts/test_real_docker.py
  DOCKER_REAL_URL=http://docker-host:2375 DOCKER_REAL_ALLOW_MUTATION=true DOCKER_REAL_TARGET_CONTAINER=my-app python scripts/test_real_docker.py

Default behavior is READ-ONLY. No destructive operations occur unless DOCKER_REAL_ALLOW_MUTATION=true.
"""

import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api"))

from app.integrations.providers.docker.client import DockerClient
from app.integrations.providers.docker.schemas import DockerIntegrationConfig, DockerIntegrationSecrets
from app.integrations.providers.docker.errors import DockerProviderError


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def run():
    url = os.environ.get("DOCKER_REAL_URL", "http://localhost:2375")
    verify_tls = os.environ.get("DOCKER_REAL_TLS_VERIFY", "false").lower() == "true"
    timeout = int(os.environ.get("DOCKER_REAL_TIMEOUT", "10"))
    allow_mutation = os.environ.get("DOCKER_REAL_ALLOW_MUTATION", "false").lower() == "true"
    target_container = os.environ.get("DOCKER_REAL_TARGET_CONTAINER", "")

    print(f"InfraPilot Real Docker Acceptance Test")
    print(f"URL: {url} | TLS: {verify_tls} | Mutation: {allow_mutation}")

    config = DockerIntegrationConfig(
        base_url=url,
        verify_tls=verify_tls,
        timeout_seconds=timeout
    )
    secrets = DockerIntegrationSecrets()
    client = DockerClient(config=config, secrets=secrets)

    failures = []

    # 1. Health Check
    print_section("1. Health Check")
    try:
        healthy = client.check_health()
        if healthy:
            print("  ✓ Docker API is healthy")
        else:
            print("  ✗ Docker API health check returned unhealthy")
            failures.append("health_check")
    except DockerProviderError as e:
        print(f"  ✗ Docker API connection failed: {e}")
        failures.append("health_check_error")
        print("\nFATAL: Cannot connect to Docker. Stopping test.")
        sys.exit(1)

    # 2. Container Discovery
    print_section("2. Container Discovery")
    try:
        containers = client.list_containers(all_containers=True)
        print(f"  ✓ Discovered {len(containers)} container(s)")
        for c in containers[:5]:
            names = c.get("Names", [])
            name = names[0].lstrip("/") if names else c.get("Id", "")[:12]
            state = c.get("State", "unknown")
            print(f"    - {name} [{state}]")
    except DockerProviderError as e:
        print(f"  ✗ Container discovery failed: {e}")
        failures.append("container_discovery")

    # 3. Image Discovery
    print_section("3. Image Discovery")
    try:
        images = client.list_images()
        print(f"  ✓ Discovered {len(images)} image(s)")
        for img in images[:5]:
            tags = img.get("RepoTags") or []
            tag_str = tags[0] if tags else img.get("Id", "")[:20]
            print(f"    - {tag_str}")
    except DockerProviderError as e:
        print(f"  ✗ Image discovery failed: {e}")
        failures.append("image_discovery")

    # 4. Network Discovery
    print_section("4. Network Discovery")
    try:
        networks = client.list_networks()
        print(f"  ✓ Discovered {len(networks)} network(s)")
        for n in networks[:5]:
            print(f"    - {n.get('Name')} [{n.get('Driver')}]")
    except DockerProviderError as e:
        print(f"  ✗ Network discovery failed: {e}")
        failures.append("network_discovery")

    # 5. Volume Discovery
    print_section("5. Volume Discovery")
    try:
        volumes_res = client.list_volumes()
        volumes = volumes_res.get("Volumes", []) if volumes_res else []
        print(f"  ✓ Discovered {len(volumes)} volume(s)")
        for v in volumes[:5]:
            print(f"    - {v.get('Name')} [{v.get('Driver')}]")
    except DockerProviderError as e:
        print(f"  ✗ Volume discovery failed: {e}")
        failures.append("volume_discovery")

    # 6. Container Inspection
    print_section("6. Container Inspection")
    if containers:
        try:
            cid = containers[0].get("Id", "")
            inspected = client.inspect_container(cid)
            # Strip Config.Env
            conf = inspected.get("Config", {})
            conf.pop("Env", None)
            print(f"  ✓ Inspected container '{cid[:12]}' — State: {inspected.get('State', {}).get('Status')}")
        except DockerProviderError as e:
            print(f"  ✗ Container inspection failed: {e}")
            failures.append("container_inspection")
    else:
        print("  - No containers to inspect")

    # 7. Bounded Log Retrieval
    print_section("7. Bounded Log Retrieval (max 20 lines)")
    running = [c for c in containers if c.get("State") == "running"]
    if running:
        try:
            cid = running[0].get("Id", "")
            logs = client.get_container_logs(cid, max_lines=20)
            lines = logs.strip().splitlines()
            print(f"  ✓ Retrieved {len(lines)} log line(s) from container '{cid[:12]}'")
        except DockerProviderError as e:
            print(f"  ✗ Log retrieval failed: {e}")
            failures.append("log_retrieval")
    else:
        print("  - No running containers to retrieve logs from")

    # 8. Optional Mutation (explicit opt-in only)
    print_section("8. Mutation Test (restart)")
    if allow_mutation:
        if not target_container:
            print("  ✗ DOCKER_REAL_TARGET_CONTAINER not set. Skipping mutation.")
            failures.append("mutation_no_target")
        else:
            try:
                print(f"  Restarting container '{target_container}'...")
                client.restart_container(target_container)
                # Verify it's running again
                import time
                for _ in range(10):
                    time.sleep(3)
                    data = client.inspect_container(target_container)
                    if data.get("State", {}).get("Running") is True:
                        print(f"  ✓ Container '{target_container}' is running after restart")
                        break
                else:
                    print(f"  ✗ Container '{target_container}' did not come back running after restart")
                    failures.append("mutation_verify")
            except DockerProviderError as e:
                print(f"  ✗ Restart failed: {e}")
                failures.append("mutation_error")
    else:
        print("  - Mutation is DISABLED. Set DOCKER_REAL_ALLOW_MUTATION=true to enable.")
        print("    WARNING: This will restart the container specified by DOCKER_REAL_TARGET_CONTAINER.")

    # Summary
    print_section("SUMMARY")
    if failures:
        print(f"  FAILED: {len(failures)} test(s) failed: {failures}")
        sys.exit(1)
    else:
        print("  ALL TESTS PASSED ✓")
        sys.exit(0)


if __name__ == "__main__":
    run()
