"""Function-based views for the alumni management portal."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .access import (
    accessible_egresados as _accessible_egresados,
    audit_event as _audit,
    has_role as _has_role,
    mask_email as _mask_email,
    mask_phone as _mask_phone,
    role_required,
)
from .queries import filtered_egresados as egresados_queryset_view
from .queries import visible_programas as _programas_visibles

from .forms import (
    ContactoEgresadoForm,
    EgresadoForm,
    TrayectoriaForm,
)
from .models import Egresado, TrayectoriaAcademica


@role_required('Administrador', 'Funcionario', 'Egresado', 'Visor')
def egresados_list_view(request):
    """List graduates visible to the user with privacy-aware contact fields."""
    queryset = egresados_queryset_view(request)
    is_visor = _has_role(request.user, 'Visor')
    may_see_contact = request.user.has_perm(
        'app_egresados.ver_contacto_completo'
    )
    graduates = list(queryset)
    for graduate in graduates:
        graduate.correo_lista = graduate.correo
        graduate.telefono_lista = graduate.telefono
        if is_visor and not may_see_contact:
            graduate.correo_lista = _mask_email(graduate.correo)
            graduate.telefono_lista = _mask_phone(graduate.telefono)
    return render(request, 'app_egresados/app_egresados_list.html', {
        'egresados': graduates,
        'programas': _programas_visibles(request.user),
        'filtros': request.GET,
        'ocupaciones': Egresado.EstadoOcupacional.choices,
        'es_admin': _has_role(request.user, 'Administrador'),
        'puede_crear': _has_role(request.user, 'Administrador', 'Funcionario'),
        'puede_exportar': _has_role(request.user, 'Administrador', 'Funcionario'),
        'es_visor': is_visor,
    })


@role_required('Administrador', 'Funcionario')
def egresado_create_view(request):
    """Create a graduate and initial program association with an audit event."""
    form = EgresadoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            graduate = form.save(commit=False)
            graduate.creado_por = request.user
            graduate.origen = 'manual'
            if graduate.autorizacion_datos:
                graduate.fecha_autorizacion = timezone.now()
            graduate.save()
            form.save(commit=True)
            _audit(
                request.user,
                'Creación manual',
                'Egresado',
                graduate.pk,
                after={
                    'documento': graduate.numero_documento,
                    'nombre': graduate.nombre_completo,
                },
            )
        messages.success(request, 'El egresado se registró correctamente.')
        return redirect('app_egresados:egresado_detail', pk=graduate.pk)
    return render(request, 'app_egresados/app_egresados_form.html', {
        'form': form,
        'titulo': 'Registrar egresado',
        'accion': 'Crear registro',
    })


@role_required('Administrador', 'Funcionario', 'Egresado', 'Visor')
def egresado_detail_view(request, pk):
    """Show one graduate and their complete academic and follow-up history."""
    include_inactive = _has_role(request.user, 'Administrador')
    graduate = get_object_or_404(
        _accessible_egresados(request.user, include_inactive), pk=pk
    )
    is_visor = _has_role(request.user, 'Visor')
    if is_visor and not request.user.has_perm(
        'app_egresados.ver_contacto_completo'
    ):
        graduate.correo_visible = _mask_email(graduate.correo)
        graduate.telefono_visible = _mask_phone(graduate.telefono)
        graduate.direccion = 'Datos protegidos'
    else:
        graduate.correo_visible = graduate.correo or 'No registrado'
        graduate.telefono_visible = graduate.telefono or 'No registrado'
    return render(request, 'app_egresados/app_egresados_detail.html', {
        'egresado': graduate,
        'trayectorias': graduate.trayectorias.select_related('programa'),
        'seguimientos': graduate.seguimientos.select_related('responsable'),
        'puede_editar': _has_role(request.user, 'Administrador', 'Funcionario')
            or graduate.usuario_id == request.user.pk,
        'puede_seguimiento': _has_role(
            request.user, 'Administrador', 'Funcionario'
        ),
        'es_admin': _has_role(request.user, 'Administrador'),
        'es_egresado': _has_role(request.user, 'Egresado'),
    })


@login_required
def egresado_update_view(request, pk):
    """Update allowed contact data and preserve old and new values in audit."""
    graduate = get_object_or_404(
        _accessible_egresados(request.user), pk=pk
    )
    can_manage = _has_role(request.user, 'Administrador', 'Funcionario')
    if not can_manage and graduate.usuario_id != request.user.pk:
        raise PermissionDenied
    if not graduate.autorizacion_datos:
        messages.error(
            request,
            'La autorización de tratamiento no está vigente; no se pueden '
            'actualizar datos de contacto.',
        )
        return redirect('app_egresados:egresado_detail', pk=graduate.pk)
    old_values = {
        'correo': graduate.correo,
        'telefono': graduate.telefono,
        'direccion': graduate.direccion,
        'estado_ocupacional': graduate.estado_ocupacional,
        'preferencias_contacto': graduate.preferencias_contacto,
    }
    form = ContactoEgresadoForm(request.POST or None, instance=graduate)
    if request.method == 'POST' and form.is_valid():
        updated = form.save(commit=False)
        if updated.correo != old_values['correo']:
            updated.correo_verificado = False
        if updated.telefono != old_values['telefono']:
            updated.telefono_verificado = False
        updated.save()
        _audit(
            request.user,
            'Actualización de contacto',
            'Egresado',
            graduate.pk,
            before=old_values,
            after={field: getattr(updated, field) for field in old_values},
        )
        messages.success(request, 'Los datos se actualizaron correctamente.')
        return redirect('app_egresados:egresado_detail', pk=graduate.pk)
    return render(request, 'app_egresados/app_egresados_form.html', {
        'form': form,
        'titulo': 'Actualizar contacto y situación',
        'accion': 'Guardar cambios',
        'egresado': graduate,
    })


@role_required('Administrador', 'Funcionario')
def trayectoria_create_view(request, pk):
    """Associate one additional distinct program with an accessible graduate."""
    graduate = get_object_or_404(_accessible_egresados(request.user), pk=pk)
    form = TrayectoriaForm(request.POST or None, egresado=graduate)
    form.fields['programa'].queryset = _programas_visibles(request.user)
    if request.method == 'POST' and form.is_valid():
        trajectory = form.save(commit=False)
        trajectory.egresado = graduate
        trajectory.save()
        _audit(
            request.user,
            'Asociación de programa',
            'TrayectoriaAcademica',
            trajectory.pk,
            after={
                'egresado_id': graduate.pk,
                'programa': trajectory.programa.nombre,
                'ficha': trajectory.ficha,
                'fecha_titulacion': trajectory.fecha_titulacion.isoformat(),
            },
        )
        messages.success(request, 'El programa quedó asociado a la trayectoria.')
        return redirect('app_egresados:egresado_detail', pk=graduate.pk)
    return render(request, 'app_egresados/app_egresados_form.html', {
        'form': form,
        'titulo': f'Asociar programa · {graduate.nombre_completo}',
        'accion': 'Asociar programa',
        'egresado': graduate,
    })


@role_required('Administrador')
@require_POST
def egresado_inactivate_view(request, pk):
    """Inactivate a graduate with a required catalog reason and audit record."""
    graduate = get_object_or_404(Egresado, pk=pk, activo=True)
    reason = request.POST.get('motivo', '')
    valid_reasons = dict(Egresado.MotivoInactivacion.choices)
    if reason not in valid_reasons:
        messages.error(request, 'Selecciona un motivo válido de inactivación.')
        return redirect('app_egresados:egresado_detail', pk=graduate.pk)
    graduate.activo = False
    graduate.motivo_inactivacion = reason
    graduate.save(update_fields=['activo', 'motivo_inactivacion', 'actualizado_en'])
    _audit(
        request.user,
        'Inactivación de egresado',
        'Egresado',
        graduate.pk,
        before={'activo': True},
        after={'activo': False, 'motivo': valid_reasons[reason]},
    )
    messages.success(request, 'El registro fue inactivado; su historial se conserva.')
    return redirect('app_egresados:egresado_list')


@role_required('Administrador', 'Funcionario', 'Egresado')
@require_POST
def privacidad_update_view(request, pk):
    """Record consent and no-contact choices with an auditable justification."""
    is_admin = _has_role(request.user, 'Administrador')
    graduate = get_object_or_404(
        _accessible_egresados(request.user, include_inactive=is_admin), pk=pk
    )
    is_owner = graduate.usuario_id == request.user.pk
    is_alumni = _has_role(request.user, 'Egresado')
    action = request.POST.get('accion')
    justification = request.POST.get('justificacion', '').strip()
    before = {
        'autorizacion_datos': graduate.autorizacion_datos,
        'no_contacto': graduate.no_contacto,
    }
    if action in {'autorizar', 'revocar'}:
        if not (is_owner and is_alumni):
            raise PermissionDenied
        graduate.autorizacion_datos = action == 'autorizar'
        if action == 'autorizar':
            graduate.fecha_autorizacion = timezone.now()
        message = 'Autorización registrada.' if action == 'autorizar' else (
            'Autorización revocada. Se bloquearon nuevos seguimientos y '
            'actualizaciones de contacto.'
        )
    elif action == 'no_contacto':
        graduate.no_contacto = True
        message = 'La preferencia de no contacto quedó registrada.'
    elif action == 'contacto_permitido':
        if not justification:
            messages.error(
                request,
                'La justificación es obligatoria para revertir no contacto.',
            )
            return redirect('app_egresados:egresado_detail', pk=graduate.pk)
        if not (is_owner and is_alumni) and not is_admin:
            raise PermissionDenied
        graduate.no_contacto = False
        message = 'La preferencia de contacto se actualizó.'
    else:
        messages.error(request, 'La acción solicitada no es válida.')
        return redirect('app_egresados:egresado_detail', pk=graduate.pk)
    graduate.save()
    _audit(
        request.user,
        'Actualización de privacidad',
        'Egresado',
        graduate.pk,
        before=before,
        after={
            'autorizacion_datos': graduate.autorizacion_datos,
            'no_contacto': graduate.no_contacto,
            'justificacion': justification,
        },
    )
    messages.success(request, message)
    return redirect('app_egresados:egresado_detail', pk=graduate.pk)


