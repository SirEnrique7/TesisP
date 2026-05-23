# ══════════════════════════════════════════════════════════════
# FORMS — Módulo Ventas
# ══════════════════════════════════════════════════════════════

from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from .models import Venta, DetalleVenta
from inventario.models import Producto
from core.models_bimonetario import Cliente


class VentaForm(forms.ModelForm):
    class Meta:
        model  = Venta
        fields = [
            'cliente', 'metodo_pago',
            'referencia_pago', 'fecha_estimada_pago', 'observacion'
        ]
        widgets = {
            'cliente': forms.Select(attrs={
                'class': 'form-select', 'id': 'id_cliente'
            }),
            'metodo_pago': forms.Select(attrs={
                'class': 'form-select', 'id': 'id_metodo_pago'
            }),
            'referencia_pago': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nro. de operación, transferencia o pago móvil'
            }),
            'fecha_estimada_pago': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date',
                       'id': 'id_fecha_estimada_pago'}
            ),
            'observacion': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'Observación opcional'
            }),
        }
        labels = {
            'cliente':            'Cliente',
            'metodo_pago':        'Método de pago',
            'referencia_pago':    'Referencia de pago',
            'fecha_estimada_pago': 'Fecha estimada de pago',
            'observacion':        'Observaciones',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset  = Cliente.objects.all().order_by('apellido')
        self.fields['cliente'].required  = False
        self.fields['cliente'].empty_label = '— Sin cliente registrado —'

    def clean(self):
        cleaned  = super().clean()
        metodo   = cleaned.get('metodo_pago')
        cliente  = cleaned.get('cliente')
        ref      = cleaned.get('referencia_pago')
        f_pago   = cleaned.get('fecha_estimada_pago')

        # Crédito exige cliente y fecha estimada
        if metodo == 'credito':
            if not cliente:
                raise ValidationError(
                    'Para ventas a crédito debe seleccionar o registrar el cliente.'
                )
            if not f_pago:
                raise ValidationError(
                    'Para ventas a crédito debe indicar la fecha estimada de pago.'
                )

        # Pago inmediato exige referencia
        if metodo in ['punto', 'pago_movil', 'biopago', 'mixto'] and not ref:
            raise ValidationError(
                'Debe ingresar la referencia del pago realizado.'
            )

        return cleaned


class DetalleVentaForm(forms.ModelForm):
    class Meta:
        model  = DetalleVenta
        fields = ['producto', 'cantidad', 'precio_unitario']
        widgets = {
            'producto':       forms.Select(attrs={
                'class': 'form-select producto-select'
            }),
            'cantidad':       forms.NumberInput(attrs={
                'class': 'form-control cant-field', 'min': '1', 'placeholder': '0'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control precio-field',
                'step': '0.01', 'min': '0', 'placeholder': '0.00'
            }),
        }
        labels = {
            'producto':        'Producto',
            'cantidad':        'Cantidad',
            'precio_unitario': 'Precio unit. (Bs.)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto'].queryset = (
            Producto.objects.filter(activo=True, stock_actual__gt=0)
            .order_by('nombre')
        )
        self.fields['producto'].empty_label = '— Seleccionar producto —'

    def clean(self):
        cleaned  = super().clean()
        producto = cleaned.get('producto')
        cantidad = cleaned.get('cantidad')

        # Validar stock disponible en tiempo real
        if producto and cantidad:
            if cantidad > producto.stock_actual:
                raise ValidationError(
                    f'Stock insuficiente. Disponible: {producto.stock_actual} unidades.'
                )
        return cleaned


DetalleVentaFormSet = inlineformset_factory(
    Venta, DetalleVenta,
    form=DetalleVentaForm,
    extra=1, min_num=1,
    validate_min=True, can_delete=True,
)
