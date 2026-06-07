from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Compra

@receiver(post_save, sender=Compra)
def procesar_cambio_estado_compra(sender, instance, created, **kwargs):
    """
    Disparador automático que se ejecuta cada vez que una Compra se guarda.
    """
    if not created:  # Es una actualización, no una creación
        if instance.estado == 'recibida':
            # TODO: Aquí programarás el aumento de stock físico
            pass