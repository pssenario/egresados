"""Focused tests for alumni permissions and core business validations."""

from datetime import date, timedelta

from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .forms import EgresadoForm
from app_auditoria.models import Bitacora
from app_programa.models import Programa
from app_seguimiento.models import Seguimiento

from .models import Egresado, TrayectoriaAcademica


class EgresadoBusinessRulesTests(TestCase):
    """Verify identity, contact, academic date, and consent rules."""

    def setUp(self):
        """Create one program and an authorized staff account for each test."""
        self.programa = Programa.objects.create(nombre='Energías renovables')
        self.user = User.objects.create_user(username='funcionario', password='test-pass-123')
        group, _ = Group.objects.get_or_create(name='Funcionario')
        self.user.groups.add(group)
        self.programa.funcionarios.add(self.user)

    def test_create_form_requires_a_contact_channel(self):
        """Reject graduate creation when neither email nor phone is supplied."""
        form = EgresadoForm(data={
            'tipo_documento': 'CC',
            'numero_documento': '1001',
            'nombres': 'Ana',
            'apellidos': 'Pérez',
            'programa': self.programa.pk,
            'fecha_titulacion': date.today().isoformat(),
        })
        self.assertFalse(form.is_valid())
        self.assertIn('correo o un teléfono', str(form.errors))

    def test_duplicate_identity_is_rejected(self):
        """Reject a second record with the same document type and number."""
        Egresado.objects.create(
            tipo_documento='CC', numero_documento='1002',
            nombres='Ana', apellidos='Pérez',
        )
        form = EgresadoForm(data={
            'tipo_documento': 'CC',
            'numero_documento': '1002',
            'nombres': 'Ana María',
            'apellidos': 'Pérez',
            'correo': 'ana@example.com',
            'programa': self.programa.pk,
            'fecha_titulacion': date.today().isoformat(),
        })
        self.assertFalse(form.is_valid())
        self.assertIn('registro #', str(form.errors))

    def test_future_graduation_date_is_rejected(self):
        """Reject academic associations with a future graduation date."""
        graduate = Egresado.objects.create(
            tipo_documento='CC', numero_documento='1003',
            nombres='Ana', apellidos='Pérez',
        )
        trajectory = TrayectoriaAcademica(
            egresado=graduate,
            programa=self.programa,
            fecha_titulacion=date.today() + timedelta(days=1),
        )
        with self.assertRaises(ValidationError):
            trajectory.save()

    def test_create_form_reports_future_graduation_date(self):
        """Show academic date errors in the form instead of failing on save."""
        form = EgresadoForm(data={
            'tipo_documento': 'CC',
            'numero_documento': '1005',
            'nombres': 'Ana',
            'apellidos': 'Pérez',
            'correo': 'ana@example.com',
            'programa': self.programa.pk,
            'fecha_titulacion': (date.today() + timedelta(days=1)).isoformat(),
        })
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_titulacion', form.errors)

    def test_follow_up_requires_company_and_sector_for_employed(self):
        """Require employer and sector details for employed graduates."""
        graduate = Egresado.objects.create(
            tipo_documento='CC', numero_documento='1004',
            nombres='Ana', apellidos='Pérez', autorizacion_datos=True,
        )
        follow_up = Seguimiento(
            egresado=graduate,
            fecha_contacto=date.today(),
            medio=Seguimiento.Medio.TELEFONO,
            estado_ocupacional=Egresado.EstadoOcupacional.EMPLEADO,
            relacion_empleo=Seguimiento.RelacionEmpleo.RELACIONADO,
            observaciones='Contacto realizado.',
            responsable=self.user,
        )
        with self.assertRaises(ValidationError):
            follow_up.save()

    def test_only_staff_can_open_create_view(self):
        """Require login and a manager role for manual graduate creation."""
        response = self.client.get(reverse('app_egresados:egresado_create'))
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.user)
        self.assertEqual(
            self.client.get(reverse('app_egresados:egresado_create')).status_code,
            200,
        )

    def test_login_uses_the_portal_template(self):
        """Render the custom institutional login screen."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Trayectorias que impulsan a La Guajira.')

    def test_dashboard_and_directory_render_for_staff(self):
        """Ensure the main authenticated pages render with their app templates."""
        self.client.force_login(self.user)
        self.assertEqual(
            self.client.get(reverse('app_reportes:dashboard')).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse('app_egresados:egresado_list')).status_code,
            200,
        )

    def test_program_catalog_has_its_own_app_and_users_stay_in_django_admin(self):
        """Keep program management separate while using Django's built-in users."""
        self.client.force_login(self.user)
        self.assertEqual(
            self.client.get(reverse('app_programa:programa_list')).status_code,
            200,
        )
        self.assertTrue(admin.site.is_registered(User))
        self.assertFalse(any(
            installed_app == 'app_usuarios'
            for installed_app in __import__('django.conf').conf.settings.INSTALLED_APPS
        ))

    def test_superuser_sees_administrator_navigation_without_group(self):
        """Show all administrator menu options to an ungrouped Django superuser."""
        superuser = User.objects.create_superuser(
            username='root-menu',
            email='root-menu@example.com',
            password='test-pass-123',
        )
        self.client.force_login(superuser)
        response = self.client.get(reverse('app_reportes:dashboard'))
        self.assertContains(response, 'Validar seguimientos')
        self.assertContains(response, 'Programas')
        self.assertContains(response, 'Bitácora')
        self.assertContains(response, 'Administración')

    def test_admin_can_create_program_through_program_app(self):
        """Create a program with its app-owned view and append an audit event."""
        admin_group, _ = Group.objects.get_or_create(name='Administrador')
        admin_user = User.objects.create_user(username='admin-programas', password='test-pass-123')
        admin_user.groups.add(admin_group)
        self.client.force_login(admin_user)
        response = self.client.post(reverse('app_programa:programa_create'), {
            'nombre': 'Hidrógeno verde',
            'codigo': 'HV-01',
            'area': 'Energías alternativas',
            'activo': 'on',
        })
        self.assertEqual(response.status_code, 302)
        program = Programa.objects.get(codigo='HV-01')
        self.assertTrue(Bitacora.objects.filter(
            entidad='Programa', entidad_id=program.pk
        ).exists())

    def test_followup_and_audit_apps_render_their_own_templates(self):
        """Render follow-up, self-service, and audit pages from their owning apps."""
        graduate = Egresado.objects.create(
            tipo_documento='CC', numero_documento='2010',
            nombres='María', apellidos='López', autorizacion_datos=True,
        )
        TrayectoriaAcademica.objects.create(
            egresado=graduate,
            programa=self.programa,
            fecha_titulacion=date.today(),
        )
        self.client.force_login(self.user)
        follow_up_response = self.client.get(
            reverse('app_seguimiento:seguimiento_create', args=[graduate.pk])
        )
        self.assertEqual(follow_up_response.status_code, 200)
        self.assertTemplateUsed(
            follow_up_response,
            'app_seguimiento/app_seguimiento_form.html',
        )
        pending_response = self.client.get(
            reverse('app_seguimiento:seguimientos_pendientes')
        )
        self.assertEqual(pending_response.status_code, 200)

        alumni = User.objects.create_user(username='portal-egresado', password='test-pass-123')
        alumni_group, _ = Group.objects.get_or_create(name='Egresado')
        alumni.groups.add(alumni_group)
        graduate.usuario = alumni
        graduate.save(update_fields=['usuario'])
        self.client.force_login(alumni)
        self.assertEqual(
            self.client.get(reverse('app_seguimiento:autogestion_create')).status_code,
            200,
        )

        admin_group, _ = Group.objects.get_or_create(name='Administrador')
        admin_user = User.objects.create_user(username='auditor-admin', password='test-pass-123')
        admin_user.groups.add(admin_group)
        self.client.force_login(admin_user)
        audit_response = self.client.get(reverse('app_auditoria:bitacora'))
        self.assertEqual(audit_response.status_code, 200)
        self.assertTemplateUsed(
            audit_response,
            'app_auditoria/app_auditoria_audit.html',
        )

    def test_staff_scope_is_limited_to_assigned_programs(self):
        """Hide graduates whose programs are outside the staff assignment."""
        other_program = Programa.objects.create(nombre='Minería sostenible')
        visible = Egresado.objects.create(
            tipo_documento='CC', numero_documento='2001',
            nombres='Ana', apellidos='Pérez',
        )
        hidden = Egresado.objects.create(
            tipo_documento='CC', numero_documento='2002',
            nombres='Luis', apellidos='Gómez',
        )
        for graduate, program in (
            (visible, self.programa),
            (hidden, other_program),
        ):
            TrayectoriaAcademica.objects.create(
                egresado=graduate,
                programa=program,
                fecha_titulacion=date.today(),
            )
        self.client.force_login(self.user)
        response = self.client.get(reverse('app_egresados:egresado_list'))
        self.assertContains(response, 'Ana Pérez')
        self.assertNotContains(response, 'Luis Gómez')

    def test_visor_contact_details_are_masked(self):
        """Mask contact details in the directory and individual profile."""
        visor = User.objects.create_user(username='visor', password='test-pass-123')
        group, _ = Group.objects.get_or_create(name='Visor')
        visor.groups.add(group)
        graduate = Egresado.objects.create(
            tipo_documento='CC', numero_documento='2003',
            nombres='Sara', apellidos='Díaz',
            correo='sara.diaz@example.com', telefono='3005551234',
            direccion='Calle Secreta 123',
        )
        TrayectoriaAcademica.objects.create(
            egresado=graduate,
            programa=self.programa,
            fecha_titulacion=date.today(),
        )
        self.client.force_login(visor)
        list_response = self.client.get(reverse('app_egresados:egresado_list'))
        self.assertContains(list_response, 's***@example.com')
        self.assertNotContains(list_response, 'sara.diaz@example.com')
        detail_response = self.client.get(
            reverse('app_egresados:egresado_detail', args=[graduate.pk])
        )
        self.assertContains(detail_response, '***-***-1234')
        self.assertNotContains(detail_response, '3005551234')
        self.assertContains(detail_response, 'Datos protegidos')
        self.assertNotContains(detail_response, 'Calle Secreta 123')

    def test_manual_creation_creates_program_and_audit(self):
        """Persist the first academic association and audit manual creation."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('app_egresados:egresado_create'),
            {
                'tipo_documento': 'CC',
                'numero_documento': '2004',
                'nombres': 'Elena',
                'apellidos': 'Ruiz',
                'correo': 'elena@example.com',
                'programa': self.programa.pk,
                'ficha': '123456',
                'fecha_titulacion': date.today().isoformat(),
            },
        )
        self.assertEqual(response.status_code, 302)
        graduate = Egresado.objects.get(numero_documento='2004')
        self.assertEqual(graduate.trayectorias.count(), 1)
        self.assertEqual(Bitacora.objects.filter(entidad_id=graduate.pk).count(), 1)

    def test_staff_can_add_a_distinct_program_to_a_graduate(self):
        """Allow a second program while rejecting a duplicate association."""
        graduate = Egresado.objects.create(
            tipo_documento='CC', numero_documento='2007',
            nombres='Elena', apellidos='Ruiz',
        )
        TrayectoriaAcademica.objects.create(
            egresado=graduate,
            programa=self.programa,
            fecha_titulacion=date.today(),
        )
        second_program = Programa.objects.create(nombre='Energía solar')
        second_program.funcionarios.add(self.user)
        self.client.force_login(self.user)
        url = reverse('app_egresados:trayectoria_create', args=[graduate.pk])
        response = self.client.post(url, {
            'programa': second_program.pk,
            'ficha': '654321',
            'fecha_titulacion': date.today().isoformat(),
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(graduate.trayectorias.count(), 2)
        duplicate_response = self.client.post(url, {
            'programa': self.programa.pk,
            'fecha_titulacion': date.today().isoformat(),
        })
        self.assertEqual(duplicate_response.status_code, 200)
        self.assertEqual(graduate.trayectorias.count(), 2)

    def test_no_contact_preference_blocks_staff_outreach(self):
        """Prevent a follow-up when the graduate requested no contact."""
        graduate = Egresado.objects.create(
            tipo_documento='CC', numero_documento='2005',
            nombres='Sara', apellidos='Díaz', autorizacion_datos=True,
        )
        TrayectoriaAcademica.objects.create(
            egresado=graduate,
            programa=self.programa,
            fecha_titulacion=date.today(),
        )
        self.client.force_login(self.user)
        self.client.post(
            reverse('app_egresados:privacidad_update', args=[graduate.pk]),
            {'accion': 'no_contacto'},
        )
        graduate.refresh_from_db()
        self.assertTrue(graduate.no_contacto)
        response = self.client.get(
            reverse('app_seguimiento:seguimiento_create', args=[graduate.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(graduate.seguimientos.count(), 0)

    def test_alumni_can_revoke_data_consent(self):
        """Allow an authenticated graduate to revoke consent with an audit event."""
        alumni = User.objects.create_user(username='egresada', password='test-pass-123')
        group, _ = Group.objects.get_or_create(name='Egresado')
        alumni.groups.add(group)
        graduate = Egresado.objects.create(
            usuario=alumni,
            tipo_documento='CC', numero_documento='2006',
            nombres='Sara', apellidos='Díaz', autorizacion_datos=True,
        )
        self.client.force_login(alumni)
        response = self.client.post(
            reverse('app_egresados:privacidad_update', args=[graduate.pk]),
            {'accion': 'revocar'},
        )
        graduate.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(graduate.autorizacion_datos)
        self.assertTrue(Bitacora.objects.filter(entidad_id=graduate.pk).exists())

    def test_inactivation_requires_a_reason_and_preserves_audit(self):
        """Require an inactivation reason and retain an audit event."""
        admin_group, _ = Group.objects.get_or_create(name='Administrador')
        admin_user = User.objects.create_user(username='admin', password='test-pass-123')
        admin_user.groups.add(admin_group)
        graduate = Egresado.objects.create(
            tipo_documento='CC', numero_documento='1006',
            nombres='Ana', apellidos='Pérez',
        )
        self.client.force_login(admin_user)
        url = reverse('app_egresados:egresado_inactivate', args=[graduate.pk])
        self.client.post(url, {})
        graduate.refresh_from_db()
        self.assertTrue(graduate.activo)
        self.client.post(url, {'motivo': Egresado.MotivoInactivacion.RETIRO})
        graduate.refresh_from_db()
        self.assertFalse(graduate.activo)
        self.assertEqual(Bitacora.objects.filter(entidad_id=graduate.pk).count(), 1)

    def test_unassigned_user_cannot_browse_alumni(self):
        """Restrict authenticated accounts without an allowed group."""
        unassigned = User.objects.create_user(username='sin-rol', password='test-pass-123')
        self.client.force_login(unassigned)
        self.assertEqual(
            self.client.get(reverse('app_egresados:egresado_list')).status_code,
            403,
        )