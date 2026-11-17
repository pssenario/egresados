"""Reusable graduate and program query builders."""

from django.utils.dateparse import parse_date

from app_programa.models import Programa

from .access import accessible_egresados, has_role


def filtered_egresados(request):
    """Build the filtered graduate queryset for lists and exports."""
    is_admin = has_role(request.user, 'Administrador')
    include_inactive = is_admin and request.GET.get('inactivos') == '1'
    queryset = accessible_egresados(request.user, include_inactive)
    document = request.GET.get('documento', '').strip()
    name = request.GET.get('nombre', '').strip()
    program = request.GET.get('programa', '').strip()
    occupation = request.GET.get('ocupacion', '').strip()
    start_date = parse_date(request.GET.get('desde', '').strip())
    end_date = parse_date(request.GET.get('hasta', '').strip())
    if document:
        queryset = queryset.filter(numero_documento__icontains=document)
    if name:
        queryset = queryset.filter(nombres__icontains=name) | queryset.filter(
            apellidos__icontains=name
        )
    if program:
        queryset = queryset.filter(trayectorias__programa_id=program)
    if occupation:
        queryset = queryset.filter(estado_ocupacional=occupation)
    if start_date:
        queryset = queryset.filter(
            trayectorias__fecha_titulacion__gte=start_date
        )
    if end_date:
        queryset = queryset.filter(
            trayectorias__fecha_titulacion__lte=end_date
        )
    return queryset.distinct().order_by('apellidos', 'nombres')


def visible_programas(user):
    """Return active programs within the user's configured scope."""
    programs = Programa.objects.filter(activo=True)
    if has_role(user, 'Funcionario') and not user.has_perm(
        'app_egresados.ambito_global_egresados'
    ):
        programs = programs.filter(funcionarios=user)
    return programs