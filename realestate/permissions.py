from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Full access — administrator only."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin


class IsAdminOrManager(BasePermission):
    """Admin or manager."""
    def has_permission(self, request, view):
        return (request.user.is_authenticated and
                (request.user.is_admin or request.user.is_manager))


class IsAnyRole(BasePermission):
    """Any authenticated user (admin, manager, agent)."""
    def has_permission(self, request, view):
        return request.user.is_authenticated


class IsAdminOrReadOnly(BasePermission):
    """Read for all authenticated; write for admin only."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_admin


class IsOwnerAgentOrAdmin(BasePermission):
    """
    Agent can only see/modify records tied to their employee_id.
    Admin and manager see everything.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin or request.user.is_manager:
            return True
        # Agent: object must belong to them
        agent_id = getattr(request.user.employee, 'employee_id', None)
        if hasattr(obj, 'agent_id'):
            return obj.agent_id == agent_id
        if hasattr(obj, 'agent'):
            return obj.agent.employee_id == agent_id
        return False
