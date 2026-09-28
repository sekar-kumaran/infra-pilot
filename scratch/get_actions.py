import sys
import os

# Add apps/api to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "apps", "api"))

from app.services.action_registry import ActionRegistry, _registry

registry = _registry

print("| Action | Provider | Resource Type | Risk | Approval | Verification | Retryable | Reversible | Compensation |")
print("|---|---|---|---|---|---|---|---|---|")

for action_id, meta in registry.actions.items():
    print(f"| {meta.name} | {meta.provider} | {meta.resource_type} | {meta.risk_level} | {meta.requires_approval} | {bool(meta.verification_strategy)} | {meta.is_retryable} | {meta.is_reversible} | {meta.compensation_action or 'None'} |")
