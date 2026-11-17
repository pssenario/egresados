"""Function-based views for administrator audit review."""

from django.shortcuts import render
from django.utils.dateparse import parse_date

from app_egresados.access import role_required

from .models import Bitacora


@role_required('Administrador')
def bitacora_list_view(request):
    """Show immutable audit events to administrators with basic filters."""
    events = Bitacora.objects.select_related('usuario')
    username = request.GET.get('usuario', '').strip()
    entity = request.GET.get('entidad', '').strip()
    start_date = parse_date(request.GET.get('desde', '').strip())
    end_date = parse_date(request.GET.get('hasta', '').strip())
    if username:
        events = events.filter(usuario__username__icontains=username)
    if entity:
        events = events.filter(entidad__icontains=entity)
    if start_date:
        events = events.filter(creado_en__date__gte=start_date)
    if end_date:
        events = events.filter(creado_en__date__lte=end_date)
    return render(request, 'app_auditoria/app_auditoria_audit.html', {
        'eventos': events[:200],
        'filtros': request.GET,
    })