# Guía de Arranque — Inversiones Ramón
## Sistema de Gestión Web | Django 4.2

---

## ¿Qué necesitas antes de empezar?

- **Python 3.10 o superior** instalado en tu computadora
- El archivo **`inversiones_ramon_final.zip`** descargado

Para verificar que tienes Python instalado, abre una terminal o símbolo del sistema y escribe:

```
python --version
```

Debe mostrar algo como `Python 3.10.x` o superior. Si no lo tienes, descárgalo desde **python.org**.

---

## PASO 1 — Descomprimir el proyecto

Descomprime el ZIP en la ubicación donde quieras trabajar.
Dentro del ZIP hay una carpeta llamada `proyecto/`. Entra en ella:

**Windows:**
```
cd C:\ruta\donde\descomprimiste\proyecto
```

**Linux / Mac:**
```
cd /ruta/donde/descomprimiste/proyecto
```

Deberías ver estos archivos al hacer `dir` (Windows) o `ls` (Linux/Mac):
```
manage.py
requirements.txt
arranque_rapido.sh
inversiones_ramon/
core/
inventario/
compras/
ventas/
reportes/
```

---

## PASO 2 — Crear el entorno virtual

Un entorno virtual aísla las dependencias del proyecto para que no interfieran con otros proyectos de Python.

```
python -m venv venv
```

Luego **activarlo**:

**Windows:**
```
venv\Scripts\activate
```

**Linux / Mac:**
```
source venv/bin/activate
```

Sabrás que está activo porque la terminal mostrará `(venv)` al inicio de la línea.

---

## PASO 3 — Instalar dependencias

Con el entorno virtual activo, instala los paquetes necesarios:

```
pip install -r requirements.txt
```

Esto instala Django 4.2, requests y beautifulsoup4 (para el scraper de la tasa BCV).

---

## PASO 4 — Crear la base de datos

Ejecuta las migraciones para crear todas las tablas:

```
python manage.py migrate
```

Verás una lista de tablas creándose. Al final debe decir:
```
Running migrations:
  Applying core.0001_initial... OK
  Applying inventario.0001_initial... OK
  Applying compras.0001_initial... OK
  Applying ventas.0001_initial... OK
  ...
```

---

## PASO 5 — Crear los usuarios iniciales

Ejecuta este comando para crear el admin, el encargado y las categorías base:

```
python manage.py shell
```

Se abrirá una consola de Python. Copia y pega esto completo, luego presiona Enter:

```python
from core.models import Usuario
from inventario.models import Categoria

for nombre in ['Alimentos y Bebidas','Limpieza e Higiene','Papelería','Electrónica','Otros']:
    Categoria.objects.get_or_create(nombre=nombre)

if not Usuario.objects.filter(username='admin').exists():
    u = Usuario.objects.create_superuser(
        username='admin', password='Admin2024!',
        email='admin@inversiones.com',
        first_name='Administrador', last_name='Principal',
    )
    u.rol = 'admin'
    u.cedula = 'V-00000000'
    u.save()
    print("Admin creado")

if not Usuario.objects.filter(username='encargado').exists():
    e = Usuario.objects.create_user(
        username='encargado', password='Encargado2024!',
        email='encargado@inversiones.com',
        first_name='Carlos', last_name='Pérez',
    )
    e.rol = 'encargado'
    e.cedula = 'V-11111111'
    e.save()
    print("Encargado creado")

exit()
```

---

## PASO 6 — Correr el servidor

```
python manage.py runserver
```

Verás:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL+BREAK (Windows) or CTRL+C (Linux/Mac).
```

---

## PASO 7 — Abrir el sistema en el navegador

Abre **Google Chrome** o cualquier navegador y entra a:

```
http://127.0.0.1:8000
```

Redirige automáticamente al login.

---

## Credenciales de acceso

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `Admin2024!` | Administrador — acceso total |
| `encargado` | `Encargado2024!` | Encargado — acceso operativo |

---

## Qué puede hacer cada rol

### Administrador
- Ver dashboard con ventas del día, cuentas por cobrar y pagar
- Gestionar productos, categorías y proveedores
- Aprobar o rechazar solicitudes de inventario del encargado
- Crear y aprobar órdenes de compra
- Registrar recepción de mercancía y actualizar stock
- Registrar ventas al contado y a crédito
- Ver e imprimir facturas
- Gestionar cuentas por pagar a proveedores
- Gestionar cuentas por cobrar a clientes
- Ver todos los reportes e inteligencia de negocios
- Dar de alta/baja al personal
- Ver el log de auditoría

### Encargado
- Ver productos y su stock disponible
- Enviar solicitudes de reposición de inventario al admin
- Registrar ventas (no ve precios de compra ni márgenes)
- Ver sus propias ventas e imprimir facturas

---

## Mapa del sistema

```
http://127.0.0.1:8000/                    → Dashboard
http://127.0.0.1:8000/inventario/         → Productos, solicitudes
http://127.0.0.1:8000/compras/            → Órdenes de compra
http://127.0.0.1:8000/ventas/             → Ventas y facturas
http://127.0.0.1:8000/reportes/           → Reportes e inteligencia
http://127.0.0.1:8000/clientes/           → Gestión de clientes
http://127.0.0.1:8000/cuentas-pagar/      → Deudas con proveedores
http://127.0.0.1:8000/cuentas-cobrar/     → Deudas de clientes
http://127.0.0.1:8000/usuarios/           → Gestión de personal
http://127.0.0.1:8000/auditoria/          → Log de acciones
```

---

## Checklist de prueba rápida

Después de entrar como admin, sigue estos pasos para confirmar que todo funciona:

- [ ] Dashboard carga correctamente con las estadísticas
- [ ] Crear un proveedor en Administración → Proveedores
- [ ] Crear una categoría en Administración → Categorías
- [ ] Crear un producto con stock inicial
- [ ] Entrar como encargado — verificar que no ve precios de compra
- [ ] Como encargado, crear una solicitud de inventario
- [ ] Como admin, aprobar la solicitud — verificar que el stock sube
- [ ] Crear una orden de compra, aprobarla y registrar recepción
- [ ] Registrar una venta al contado con referencia de pago
- [ ] Registrar una venta a crédito con cliente y fecha estimada
- [ ] Verificar que se generó la cuenta por cobrar automáticamente
- [ ] Registrar un pago del cliente — verificar que la venta pasa a PAGADA
- [ ] Ir a Reportes → Tendencias → confirma que el motor carga
- [ ] Ir a Reportes → Abastecimiento Crítico

---

## Solución de problemas comunes

**"No module named django"**
El entorno virtual no está activado. Ejecuta `venv\Scripts\activate` (Windows) o `source venv/bin/activate` (Linux/Mac).

**"Table doesn't exist"**
Las migraciones no se aplicaron. Ejecuta `python manage.py migrate`.

**"Port 8000 already in use"**
Otro proceso usa el puerto. Usa un puerto diferente:
```
python manage.py runserver 8080
```
Luego entra a `http://127.0.0.1:8080`.

**La tasa BCV no aparece**
Es normal la primera vez si no hay conexión a internet o el BCV tiene el sitio caído. El sistema usa la última tasa disponible como respaldo. No afecta ninguna otra funcionalidad.

**"Invalid credentials" al hacer login**
Verifica que ejecutaste el Paso 5 correctamente. Puedes crear un nuevo superusuario con:
```
python manage.py createsuperuser
```
Luego desde el shell asigna `u.rol = 'admin'` como se explicó arriba.

---

## Para apagar el servidor

Presiona `CTRL + C` en la terminal donde corre el servidor.

---

*Inversiones Ramón — Sistema de Gestión Interno*
*Desarrollado con Django 4.2 | Caicara de Maturín, Monagas, Venezuela*
