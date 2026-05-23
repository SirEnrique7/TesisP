# ══════════════════════════════════════════════════════════════
# FORMS — Módulo Compras (versión definitiva)
# ══════════════════════════════════════════════════════════════

from django import forms
from django.forms import inlineformset_factory
from .models import Compra, DetalleCompra
from inventario.models import Producto


class CompraForm(forms.ModelForm):
    class Meta:
        model  = Compra
        fields = ['proveedor', 'fecha_estimada', 'observacion']
        widgets = {
            'proveedor':     forms.Select(attrs={'class': 'form-select'}),
            'fecha_estimada': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'observacion':   forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'Motivo del pedido u observación'
            }),
        }
        labels = {
            'proveedor':     'Proveedor',
            'fecha_estimada': 'Fecha estimada de entrega',
            'observacion':   'Observaciones',
        }


class DetalleCompraForm(forms.ModelForm):
    class Meta:
        model  = DetalleCompra
        fields = ['producto', 'cantidad_pedida', 'precio_unitario']
        widgets = {
            'producto':        forms.Select(attrs={'class': 'form-select producto-select'}),
            'cantidad_pedida': forms.NumberInput(attrs={
                'class': 'form-control cant-field', 'min': '1', 'placeholder': '0'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control precio-field',
                'step': '0.01', 'min': '0', 'placeholder': '0.00'
            }),
        }
        labels = {
            'producto':        'Producto',
            'cantidad_pedida': 'Cantidad',
            'precio_unitario': 'Precio unit. (Bs.)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto'].queryset = (
            Producto.objects.filter(activo=True).order_by('nombre')
        )
        self.fields['producto'].empty_label = '— Seleccionar —'


DetalleCompraFormSet = inlineformset_factory(
    Compra, DetalleCompra,
    form=DetalleCompraForm,
    extra=1, min_num=1,
    validate_min=True, can_delete=True,
)


class AprobarCompraForm(forms.Form):
    DECISION_CHOICES = [
        ('aprobada',  'Aprobar orden'),
        ('rechazada', 'Rechazar orden'),
    ]
    decision       = forms.ChoiceField(
        choices=DECISION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    motivo_rechazo = forms.CharField(
        required=False, label='Motivo del rechazo',
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 2,
            'placeholder': 'Obligatorio si rechaza'
        })
    )

    def clean(self):
        cleaned  = super().clean()
        if cleaned.get('decision') == 'rechazada' and not cleaned.get('motivo_rechazo'):
            raise forms.ValidationError('Debe indicar el motivo del rechazo.')
        return cleaned


class RecepcionCompraForm(forms.ModelForm):
    """Datos de pago y recepción física — rellenados por el Admin al llegar el proveedor."""
    class Meta:
        model  = Compra
        fields = [
            'modalidad_pago', 'fecha_vencimiento',
            'referencia_documento', 'fecha_recepcion',
        ]
        widgets = {
            'modalidad_pago': forms.Select(
                attrs={'class': 'form-select', 'id': 'id_modalidad_pago'}
            ),
            'fecha_vencimiento': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date', 'id': 'id_fecha_venc'}
            ),
            'referencia_documento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nro. factura, nota de entrega o referencia bancaria'
            }),
            'fecha_recepcion': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'class': 'form-control', 'type': 'datetime-local'}
            ),
        }
        labels = {
            'modalidad_pago':      'Modalidad de pago',
            'fecha_vencimiento':   'Fecha límite (si es crédito)',
            'referencia_documento': 'Referencia / Nro. de documento',
            'fecha_recepcion':     'Fecha y hora de recepción',
        }

    def clean(self):
        cleaned   = super().clean()
        modalidad = cleaned.get('modalidad_pago')
        venc      = cleaned.get('fecha_vencimiento')
        ref       = cleaned.get('referencia_documento')

        if not ref:
            raise forms.ValidationError(
                'La referencia del documento es obligatoria para auditoría.'
            )
        if modalidad == 'credito' and not venc:
            raise forms.ValidationError(
                'Debe indicar la fecha límite de pago para crédito.'
            )
        return cleaned


class DetalleRecepcionForm(forms.ModelForm):
    class Meta:
        model   = DetalleCompra
        fields  = ['cantidad_recibida']
        widgets = {
            'cantidad_recibida': forms.NumberInput(attrs={
                'class': 'form-control text-center', 'min': '0'
            })
        }
        labels = {'cantidad_recibida': 'Recibido'}


class MarcarPagadoForm(forms.Form):
    confirmacion = forms.BooleanField(
        label='Confirmo que el pago fue realizado',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
