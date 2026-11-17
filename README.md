# Seguimiento de egresados · CIEA

Aplicación web Django para la gestión de egresados, trayectorias académicas, seguimientos y auditoría del Centro Industrial y de Energías Alternativas, SENA Regional La Guajira.

## Puesta en marcha

Desde la carpeta del proyecto, activa el entorno virtual y ejecuta:

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abre `http://127.0.0.1:8000/`. El inicio de sesión está en `/accounts/login/` y la administración Django en `/admin/`.

## Configuración inicial

1. Inicia sesión con la cuenta superadministradora.
2. En Django Admin crea los grupos `Administrador`, `Funcionario`, `Egresado` y `Visor`; los grupos no se crean automáticamente para mantener la administración de permisos bajo control del superadministrador.
3. Crea programas y asigna los funcionarios responsables en cada programa. Para permitir consulta global, asigna al grupo o usuario el permiso `Puede consultar todos los programas`.
4. Crea usuarios operativos y asígnales el grupo correspondiente. Para el portal de una persona egresada, vincula su usuario en el registro del egresado.

El usuario superadministrador tiene acceso administrativo. Los funcionarios solo consultan egresados asociados a sus programas, salvo que tengan el permiso de ámbito global. El Visor ve contactos enmascarados; el acceso completo requiere asignar el permiso `Puede consultar datos de contacto completos`.

## Apps Django

- `app_egresados`: personas egresadas y sus trayectorias académicas.
- `app_programa`: catálogo y ámbito de programas de formación.
- `app_seguimiento`: contactos institucionales, autogestión y validación.
- `app_auditoria`: bitácora de operaciones no editable.
- `app_reportes`: tablero y exportación CSV.

Los usuarios y grupos usan `django.contrib.auth` y se administran únicamente desde Django Admin; no existe una app personalizada de usuarios. Las migraciones de separación mantienen los nombres de las tablas anteriores y sus datos.

## Alcance implementado

La primera entrega incluye registro manual y validación de duplicados, trayectoria académica asociada, filtros de consulta, edición de contacto con canales no verificados, seguimiento institucional y autogestionado, aprobación de actualizaciones, privacidad, inactivación lógica, exportación CSV y bitácora.

La carga CSV/XLSX con vista previa y confirmación, fusión de duplicados, novedades académicas con aprobación, verificación real por correo/SMS, alertas configurables, indicadores agregados avanzados y autorizaciones temporales del Visor quedan para siguientes iteraciones del backlog.

## Configuración de despliegue

En producción define `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` y `DJANGO_DEBUG=False` en el entorno. Las cookies `Secure`, HSTS y las cabeceras de seguridad se habilitan cuando `DEBUG` es falso. La base local usa SQLite y los modelos se mantienen compatibles con PostgreSQL.