"""Function-based views for follow-up and validation workflows."""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from app_egresados.access import (
    accessible_egresados,
    audit_event,
    role_required,
)
from app_egresados.models import Egresado

from .forms import AutogestionForm, SeguimientoForm
from .models import Seguimiento


@role_required('Administrador', 'Funcionario')
def seguimiento_create_view(request, pk):
    """Create a staff follow-up only for an accessible, consented graduate."""
    graduate = get_object_or_404(accessible_egresados(request.user), pk=pk)
    if graduate.no_contacto:
        messages.error(request, 'El egresado solicitó no recibir contacto.')
        return redirect('app_egresados:egresado_detail', pk=graduate.pk)
    if not graduate.autorizacion_datos:
        messages.error(
            request,
            'No se puede registrar el seguimiento: no hay autorización vigente.',
        )
        return redirect('app_egresados:egresado_detail', pk=graduate.pk)
    form = SeguimientoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        follow_up = form.save(commit=False)
        follow_up.egresado = graduate
        follow_up.responsable = request.user
        follow_up.origen = 'institucional'
        follow_up.validacion = Seguimiento.Validacion.APROBADO
        follow_up.save()
        graduate.estado_ocupacional = follow_up.estado_ocupacional
        graduate.save(update_fields=['estado_ocupacional', 'actualizado_en'])
        audit_event(
            request.user,
            'Registro de seguimiento',
            'Seguimiento',
            follow_up.pk,
            after={'egresado_id': graduate.pk, 'medio': follow_up.medio},
        )
        messages.success(request, 'El seguimiento quedó guardado en el historial.')
        return redirect('app_egresados:egresado_detail', pk=graduate.pk)
    return render(request, 'app_seguimiento/app_seguimiento_form.html', {
        'form': form,
        'titulo': f'Nuevo seguimiento · {graduate.nombre_completo}',
        'accion': 'Registrar seguimiento',
        'egresado': graduate,
    })


@role_required('Egresado')
def autogestion_create_view(request):
    """Save a graduate's own situation update for staff review."""
    graduate = get_object_or_404(Egresado, usuario=request.user, activo=True)
    if not graduate.autorizacion_datos:
        messages.error(request, 'Se requiere autorización vigente para actualizar.')
        return redirect('app_egresados:egresado_detail', pk=graduate.pk)
    form = AutogestionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        follow_up = form.save(commit=False)
        follow_up.egresado = graduate
        follow_up.responsable = request.user
        follow_up.medio = Seguimiento.Medio.AUTOGESTIONADO
        follow_up.origen = 'autogestionado'
        follow_up.validacion = Seguimiento.Validacion.PENDIENTE
        follow_up.save()
        audit_event(
            request.user,
            'Actualización autogestionada',
            'Seguimiento',
            follow_up.pk,
            after={'egresado_id': graduate.pk},
        )
        messages.success(request, 'Tu actualización quedó pendiente de validación.')
        return redirect('app_egresados:egresado_detail', pk=graduate.pk)
    return render(request, 'app_seguimiento/app_seguimiento_form.html', {
        'form': form,
        'titulo': 'Actualizar mi situación',
        'accion': 'Enviar actualización',
        'egresado': graduate,
    })


@role_required('Administrador', 'Funcionario')
def seguimientos_pendientes_view(request):
    """Review graduate-submitted updates and audit every decision."""
    queryset = Seguimiento.objects.filter(
        validacion=Seguimiento.Validacion.PENDIENTE,
        egresado__in=accessible_egresados(request.user),
    ).select_related('egresado', 'responsable')
    if request.method == 'POST':
        follow_up = get_object_or_404(
            queryset, pk=request.POST.get('seguimiento_id')
        )
        decision = request.POST.get('decision')
        observation = request.POST.get('observacion', '').strip()
        if decision not in {'aprobar', 'rechazar'}:
            messages.error(request, 'Selecciona una decisión válida.')
        elif decision == 'rechazar' and not observation:
            messages.error(request, 'La observación es obligatoria para rechazar.')
        else:
            follow_up.validacion = (
                Seguimiento.Validacion.APROBADO
                if decision == 'aprobar'
                else Seguimiento.Validacion.RECHAZADO
            )
            follow_up.observacion_validacion = observation
            follow_up.validado_por = request.user
            follow_up.save()
            if decision == 'aprobar':
                Egresado.objects.filter(pk=follow_up.egresado_id).update(
                    estado_ocupacional=follow_up.estado_ocupacional
                )
            audit_event(
                request.user,
                f'Seguimiento {follow_up.validacion}',
                'Seguimiento',
                follow_up.pk,
                after={'observacion': observation},
            )
            messages.success(request, 'La decisión quedó registrada.')
        return redirect('app_seguimiento:seguimientos_pendientes')
    return render(request, 'app_seguimiento/app_seguimiento_pending.html', {
        'seguimientos': queryset.order_by('fecha_contacto'),
    })