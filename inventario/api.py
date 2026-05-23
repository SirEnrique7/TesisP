from django.http import JsonResponse
from .models import Producto
from .decorators import login_requerido


@login_requerido
def api_sugerencia_cantidad(request):
    """Devuelve la cantidad sugerida de pedido para un producto."""
    producto_id = request.GET.get('producto')
    if not producto_id:
        return JsonResponse({'error': 'Falta producto'}, status=400)
    try:
        producto = Producto.objects.get(pk=producto_id, activo=True)
        return JsonResponse({'sugerencia': producto.cantidad_sugerida_pedido})
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)
