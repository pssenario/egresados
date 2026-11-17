"""Function-based views for dashboards and filtered exports."""

import csv

from django.http import HttpResponse
from django.shortcuts import render

from app_egresados.access import (
    accessible_egresados,
    audit_event,
    has_role,
    role_required,
)
from app_egresados.models import TrayectoriaAcademica
from app_egresados.queries import filtered_egresados
from app_seguimiento.models import Seguimiento


@role_required('Administrador', 'Funcionario', 'Egresado', 'Visor')
def dashboard_view(request):
    """Show role-appropriate graduate and follow-up summary metrics."""
    visible = accessible_egresados(request.user)
    return render(request, 'app_reportes/app_reportes_dashboard.html', {
        'total_egresados': visible.count(),
        'total_programas': TrayectoriaAcademica.objects.filter(
            egresado__in=visible
        ).values('programa_id').distinct().count(),
        'seguimientos_pendientes': Seguimiento.objects.filter(
            validacion=Seguimiento.Validacion.PENDIENTE,
            egresado__in=visible,
        ).count(),
        'ultimos_egresados': visible.order_by('-creado_en')[:6],
        'es_admin': has_role(request.user, 'Administrador'),
        'es_funcionario': has_role(request.user, 'Funcionario'),
        'es_egresado': has_role(request.user, 'Egresado'),
        'es_visor': has_role(request.user, 'Visor'),
    })


@role_required('Administrador', 'Funcionario')
def egresados_export_view(request):
    """Export the filtered visible graduate list to CSV and audit the export."""
    graduates = filtered_egresados(request).prefetch_related(
        'trayectorias__programa'
    )
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="egresados.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow([
        'Tipo documento', 'Documento', 'Nombres', 'Apellidos', 'Correo',
        'Teléfono', 'Programa', 'Ficha', 'Fecha titulación', 'Situación',
    ])
    for graduate in graduates:
        for trajectory in graduate.trayectorias.all():
            writer.writerow([
                graduate.tipo_documento,
                graduate.numero_documento,
                graduate.nombres,
                graduate.apellidos,
                graduate.correo,
                graduate.telefono,
                trajectory.programa.nombre,
                trajectory.ficha,
                trajectory.fecha_titulacion,
                graduate.get_estado_ocupacional_display(),
            ])
    audit_event(
        request.user,
        'Exportación CSV',
        'Egresado',
        after={'filtros': dict(request.GET), 'registros': graduates.count()},
    )
    return response