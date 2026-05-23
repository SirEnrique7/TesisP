# ══════════════════════════════════════════════════════════════
# FORMS — Cuentas por Pagar / Cobrar + Cliente
# ══════════════════════════════════════════════════════════════

from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models_bimonetario import CuentaPorPagar, CuentaPorCobrar, Cliente


# ─────────────────────────────────────────────
# ABONO A PROVEEDOR
# ─────────────────────────────────────────────

class AbonoProveedorForm(forms.Form):
    monto_bs   = forms.DecimalField(
        label='Monto a pagar (Bs.)',
        min_value=Decimal('0.01'),
        max_digits=14, decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'step': '0.01', 'placeholder': '0.00'
        })
    )
    referencia = forms.CharField(
        label='Referencia bancaria / legal',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nro. de transferencia, operación o nota de entrega'
        })
    )

    def __init__(self, *args, cuenta=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cuenta = cuenta

    def clean_monto_bs(self):
        monto = self.cleaned_data['monto_bs']
        if self.cuenta and monto > self.cuenta.saldo_restante:
            raise ValidationError(
                f'El monto supera el saldo restante '
                f'(Bs. {self.cuenta.saldo_restante}).'
            )
        return monto


# ─────────────────────────────────────────────
# PAGO DE CLIENTE
# ─────────────────────────────────────────────

class PagoClienteForm(forms.Form):
    monto_bs   = forms.DecimalField(
        label='Monto recibido (Bs.)',
        min_value=Decimal('0.01'),
        max_digits=14, decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'step': '0.01', 'placeholder': '0.00'
        })
    )
    referencia = forms.CharField(
        label='Referencia bancaria / legal',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nro. de transferencia o pago móvil'
        })
    )

    def __init__(self, *args, cuenta=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cuenta = cuenta

    def clean_monto_bs(self):
        monto = self.cleaned_data['monto_bs']
        if self.cuenta and monto > self.cuenta.saldo_restante:
            raise ValidationError(
                f'El monto supera el saldo restante '
                f'(Bs. {self.cuenta.saldo_restante}).'
            )
        return monto


# ─────────────────────────────────────────────
# CLIENTE
# ─────────────────────────────────────────────

class ClienteForm(forms.ModelForm):
    class Meta:
        model  = Cliente
        fields = ['cedula_rif', 'nombre', 'apellido', 'telefono', 'direccion']
        widgets = {
            'cedula_rif': forms.TextInput(attrs={'class': 'form-control',
                                                  'placeholder': 'V-00000000 o J-00000000-0'}),
            'nombre':     forms.TextInput(attrs={'class': 'form-control'}),
            'apellido':   forms.TextInput(attrs={'class': 'form-control'}),
            'telefono':   forms.TextInput(attrs={'class': 'form-control',
                                                  'placeholder': '0414-0000000'}),
            'direccion':  forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'cedula_rif': 'Cédula / RIF',
            'nombre':     'Nombre',
            'apellido':   'Apellido',
            'telefono':   'Teléfono',
            'direccion':  'Dirección',
        }
