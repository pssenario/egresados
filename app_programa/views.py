"""Function-based views for the training program catalog."""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from app_egresados.access import audit_event, has_role, role_required

from .forms import ProgramaForm
from .models import Programa


@role_required('Administrador', 'Funcionario', 'Visor')
def programas_list_view(request):
    """List programs visible to the current user."""
    programs = Programa.objects.all()
    if has_role(request.user, 'Funcionario') and not has_role(
        request.user, 'Administrador'
    ) and not request.user.has_perm('app_egresados.ambito_global_egresados'):
        programs = programs.filter(funcionarios=request.user)
    if not has_role(request.user, 'Administrador'):
        programs = programs.filter(activo=True)
    return render(request, 'app_programa/app_programa_list.html', {
        'programas': programs.distinct(),
        'puede_gestionar': has_role(request.user, 'Administrador'),
    })


@role_required('Administrador')
def programa_create_view(request):
    """Create a program catalog record and write an audit event."""
    form = ProgramaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        program = form.save()
        audit_event(
            request.user,
            'Creación de programa',
            'Programa',
            program.pk,
            after={'nombre': program.nombre, 'codigo': program.codigo},
        )
        messages.success(request, 'El programa quedó registrado.')
        return redirect('app_programa:programa_list')
    return render(request, 'app_programa/app_programa_form.html', {
        'form': form,
        'titulo': 'Crear programa',
        'accion': 'Crear programa',
    })


@role_required('Administrador')
def programa_update_view(request, pk):
    """Update a program and audit its previous and new values."""
    program = get_object_or_404(Programa, pk=pk)
    before = {
        'nombre': program.nombre,
        'codigo': program.codigo,
        'area': program.area,
        'activo': program.activo,
    }
    form = ProgramaForm(request.POST or None, instance=program)
    if request.method == 'POST' and form.is_valid():
        program = form.save()
        audit_event(
            request.user,
            'Actualización de programa',
            'Programa',
            program.pk,
            before=before,
            after={
                'nombre': program.nombre,
                'codigo': program.codigo,
                'area': program.area,
                'activo': program.activo,
            },
        )
        messages.success(request, 'El programa quedó actualizado.')
        return redirect('app_programa:programa_list')
    return render(request, 'app_programa/app_programa_form.html', {
        'form': form,
        'titulo': f'Editar programa · {program.nombre}',
        'accion': 'Guardar cambios',
        'programa': program,
    })