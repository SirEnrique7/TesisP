#!/bin/bash
echo "=== Inversiones Ramón — Arranque ==="

# 1. Instalar dependencias
echo "[1/5] Instalando dependencias..."
pip install -r requirements.txt -q

# 2. Migraciones en orden
echo "[2/5] Ejecutando migraciones..."
python manage.py makemigrations core
python manage.py makemigrations inventario
python manage.py makemigrations compras
python manage.py makemigrations ventas
python manage.py makemigrations reportes
python manage.py migrate

# 3. Verificar
echo "[3/5] Verificando tablas..."
python manage.py check

# 4. Datos iniciales
echo "[4/5] Cargando datos iniciales..."
python manage.py shell << 'PYEOF'
from core.models import Usuario
from inventario.models import Categoria

categorias = ['Alimentos y Bebidas','Limpieza e Higiene','Papelería','Electrónica','Otros']
for c in categorias:
    Categoria.objects.get_or_create(nombre=c)

if not Usuario.objects.filter(username='admin').exists():
    u = Usuario.objects.create_superuser(
        username='admin', password='Admin2024!',
        email='admin@inversiones.com',
        first_name='Administrador', last_name='Principal',
        cedula='V-00000000',
    )
    u.rol = 'admin'
    u.save()
    print("Admin creado: usuario=admin / contraseña=Admin2024!")

if not Usuario.objects.filter(username='encargado').exists():
    e = Usuario.objects.create_user(
        username='encargado', password='Encargado2024!',
        email='encargado@inversiones.com',
        first_name='Encargado', last_name='Almacén',
        cedula='V-11111111',
    )
    e.rol = 'encargado'
    e.save()
    print("Encargado creado: usuario=encargado / contraseña=Encargado2024!")
PYEOF

# 5. Correr servidor
echo "[5/5] Iniciando servidor en http://127.0.0.1:8000"
echo ""
echo "  Admin:     usuario=admin      contraseña=Admin2024!"
echo "  Encargado: usuario=encargado  contraseña=Encargado2024!"
echo ""
python manage.py runserver
