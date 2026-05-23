from django.db import models
from django.utils import timezone


class Compra(models.Model):
    ESTADO_CHOICES = [
        ('pendiente',  'Pendiente de aprobación'),
        ('aprobada',   'Aprobada'),
        ('recibida',   'Recibida'),
        ('rechazada',  'Rechazada'),
        ('cancelada',  'Cancelada'),
    ]
    PAGO_CHOICES = [
        ('contado', 'Contado'),
        ('credito', 'Crédito'),
    ]

    creada_por           = models.ForeignKey('core.Usuario', on_delete=models.SET_NULL,
                                              null=True, related_name='compras_creadas')
    aprobada_por         = models.ForeignKey('core.Usuario', on_delete=models.SET_NULL,
                                              null=True, blank=True, related_name='compras_aprobadas')
    proveedor            = models.ForeignKey('inventario.Proveedor', on_delete=models.PROTECT,
                                              related_name='compras')
    fecha_creacion       = models.DateTimeField(auto_now_add=True)
    fecha_aprobacion     = models.DateTimeField(null=True, blank=True)
    fecha_estimada       = models.DateField(null=True, blank=True,
                                             verbose_name='Fecha estimada de entrega')
    fecha_recepcion      = models.DateTimeField(null=True, blank=True,
                                                verbose_name='Fecha real de recepción')
    estado               = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')
    modalidad_pago       = models.CharField(max_length=10, choices=PAGO_CHOICES,
                                             null=True, blank=True)
    pagado               = models.BooleanField(default=False)
    fecha_vencimiento    = models.DateField(null=True, blank=True,
                                             verbose_name='Fecha límite de pago')
    # CORRECCIÓN: campo referencia_documento que faltaba
    referencia_documento = models.CharField(max_length=100, blank=True,
                                             verbose_name='Referencia / Nro. documento')
    numero_referencia    = models.CharField(max_length=30, unique=True, blank=True,
                                             verbose_name='Referencia interna')
    observacion          = models.TextField(blank=True)
    motivo_rechazo       = models.TextField(blank=True)
    total                = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.numero_referencia:
            self.numero_referencia = f"OC-{self.id:05d}"
            Compra.objects.filter(pk=self.pk).update(numero_referencia=self.numero_referencia)

    def calcular_total(self):
        from django.db.models import Sum
        resultado = self.detalles.aggregate(t=Sum('subtotal'))['t']
        self.total = resultado or 0
        self.save(update_fields=['total'])

    def puede_aprobar(self, usuario):
        return usuario.es_admin() and self.estado == 'pendiente'

    def puede_recibir(self, usuario):
        return usuario.es_admin() and self.estado == 'aprobada'

    def puede_cancelar(self, usuario):
        return self.estado in ['pendiente'] and (
            usuario.es_admin() or self.creada_por == usuario
        )

    @property
    def credito_vencido(self):
        from datetime import date
        return (self.modalidad_pago == 'credito' and not self.pagado
                and self.fecha_vencimiento
                and self.fecha_vencimiento < date.today())

    def get_modalidad_pago_display(self):
        return dict(self.PAGO_CHOICES).get(self.modalidad_pago, '—')

    def __str__(self):
        return f"{self.numero_referencia} — {self.proveedor} ({self.get_estado_display()})"

    class Meta:
        ordering     = ['-fecha_creacion']
        verbose_name = 'Orden de compra'


class DetalleCompra(models.Model):
    compra            = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='detalles')
    producto          = models.ForeignKey('inventario.Producto', on_delete=models.PROTECT)
    cantidad_pedida   = models.IntegerField()
    cantidad_recibida = models.IntegerField(default=0)
    precio_unitario   = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal          = models.DecimalField(max_digits=14, decimal_places=2, editable=False, default=0)

    @property
    def entrega_incompleta(self):
        return self.cantidad_recibida < self.cantidad_pedida

    @property
    def diferencia(self):
        return self.cantidad_pedida - self.cantidad_recibida

    def save(self, *args, **kwargs):
        cant = self.cantidad_recibida if self.cantidad_recibida > 0 else self.cantidad_pedida
        self.subtotal = cant * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.producto.nombre} — pedido:{self.cantidad_pedida}/recibido:{self.cantidad_recibida}"
