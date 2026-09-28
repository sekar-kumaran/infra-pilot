import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.rbac import Role, Permission, UserRole, RolePermission, ResourceScope
from app.models.resource import InfrastructureResource
from app.models.user import User

logger = logging.getLogger(__name__)

class AuthorizationService:
    def __init__(self, db: Session):
        self.db = db

    def check_permission(self, user: User, permission_name: str, resource: Optional[InfrastructureResource] = None, current_tenant_id: Optional[UUID] = None) -> bool:
        """
        Check if the user has the given permission, optionally scoped to the given resource and tenant.
        """
        # Superuser shortcut
        if getattr(user, "is_superuser", False):
            return True

        # Tenant isolation check
        if current_tenant_id:
            if user.tenant_id and str(user.tenant_id) != str(current_tenant_id):
                return False
            if resource and resource.tenant_id and str(resource.tenant_id) != str(current_tenant_id):
                return False

        if resource and resource.tenant_id and user.tenant_id:
            if str(resource.tenant_id) != str(user.tenant_id):
                return False

        # Find roles that the user has that contain the required permission
        user_roles = self.db.query(UserRole).join(Role).join(RolePermission).join(Permission).filter(
            UserRole.user_id == user.id,
            Permission.name == permission_name
        ).all()

        if not user_roles:
            return False

        # If there is no specific resource to check against, having the permission globally or via any scope is sufficient for general access
        if not resource:
            return True

        # If checking against a specific resource, verify that at least one of those roles covers the resource's scope
        for user_role in user_roles:
            scopes = user_role.scopes
            if not scopes:
                # Unscoped role implies global access for this role within the tenant
                return True

            for scope in scopes:
                if self._scope_matches(scope, resource):
                    return True

        return False

    def _scope_matches(self, scope: ResourceScope, resource: InfrastructureResource) -> bool:
        """
        Check if a scope applies to the given resource.
        Handles provider, resource_type, and resource_id.
        """
        if scope.provider and scope.provider != resource.provider:
            return False
        
        if scope.resource_type and scope.resource_type != resource.resource_type:
            return False
            
        if scope.resource_id:
            # Match directly on internal id or external_id (treating scope.resource_id as a string)
            # In a hierarchical system, we would also check if resource is a child of scope.resource_id
            if scope.resource_id != str(resource.id) and scope.resource_id != resource.external_id:
                # Hierarchical check: if the resource has a parent_external_id, see if it falls under the scope
                if resource.parent_external_id and scope.resource_id == resource.parent_external_id:
                    pass # It matches the parent, so we allow it
                else:
                    return False
                
        return True

    def get_user_permissions(self, user: User) -> List[str]:
        if getattr(user, "is_superuser", False):
            return ["*"]
            
        permissions = self.db.query(Permission.name).join(RolePermission).join(Role).join(UserRole).filter(
            UserRole.user_id == user.id
        ).all()
        return list(set(p[0] for p in permissions))
