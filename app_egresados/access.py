"""Shared authentication, role, scope, and audit helpers."""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from app_auditoria.models import Bitacora

from .models import Egresado


def _role_names(user):
    """Return normalized names of the user's Django groups."""
    return {group.name.casefold() for group in user.groups.all()}


def has_role(user, *roles):
    """Check whether a user belongs to one of the required role groups."""
    if user.is_superuser:
        return any(role.casefold() == 'administrador' for role in roles)
    return bool(_role_names(user).intersection(role.casefold() for role in roles))


def role_required(*roles):
    """Protect a function-based view by login and named Django groups."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if not has_role(request.user, *roles):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator


def accessible_egresados(user, include_inactive=False):
    """Return graduates visible within the current user's role and scope."""
    queryset = Egresado.objects.prefetch_related(
        'trayectorias__programa', 'seguimientos'
    )
    roles = ('Administrador', 'Funcionario', 'Egresado', 'Visor')
    if not any(has_role(user, role) for role in roles):
        return queryset.none()
    if has_role(user, 'Egresado'):
        queryset = queryset.filter(usuario=user)
    elif has_role(user, 'Funcionario') and not user.has_perm(
        'app_egresados.ambito_global_egresados'
    ):
        queryset = queryset.filter(
            trayectorias__programa__funcionarios=user
        ).distinct()
    if not include_inactive:
        queryset = queryset.filter(activo=True)
    return queryset


def audit_event(user, action, entity, entity_id=None, before=None, after=None):
    """Append one immutable audit event for a successful operation."""
    return Bitacora.objects.create(
        usuario=user,
        accion=action,
        entidad=entity,
        entidad_id=entity_id,
        valores_anteriores=before or {},
        valores_nuevos=after or {},
    )


def mask_email(value):
    """Hide an email's local part while retaining its domain."""
    if '@' not in value:
        return 'No registrado' if not value else '***'
    local, domain = value.split('@', 1)
    return f'{local[:1]}***@{domain}'


def mask_phone(value):
    """Expose only the last four digits of a phone number."""
    digits = ''.join(character for character in value if character.isdigit())
    if not digits:
        return 'No registrado'
    return f'***-***-{digits[-4:]}'