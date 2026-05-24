# ══════════════════════════════════════════════════════════════
# FORMS — Módulo Ventas
# ══════════════════════════════════════════════════════════════

from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError
from .models import Venta, DetalleVenta
from inventario.models import Producto
from core.models_bimonetario import Cliente


class VentaForm(forms.ModelForm):
    class Meta:
        model  = Venta
        fields = ['cliente', 'metodo_pago', 'referencia_pago',
                  'fecha_estimada_pago', 'observacion']
        widgets = {
            'cliente': forms.Select(attrs={
                'class': 'form-select', 'id': 'id_cliente'}),
            'metodo_pago': forms.Select(attrs={
                'class': 'form-select', 'id': 'id_metodo_pago'}),
            'referencia_pago': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nro. de operación, transferencia o pago móvil'}),
            'fecha_estimada_pago': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date',
                       'id': 'id_fecha_estimada_pago'}),
            'observacion': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'Observación opcional'}),
        }
        labels = {
            'cliente':             'Cliente',
            'metodo_pago':         'Método de pago',
            'referencia_pago':     'Referencia de pago',
            'fecha_estimada_pago': 'Fecha estimada de pago',
            'observacion':         'Observaciones',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset    = Cliente.objects.all().order_by('apellido')
        self.fields['cliente'].required    = False
        self.fields['cliente'].empty_label = '— Sin cliente registrado —'
        self.fields['referencia_pago'].required = False

    def clean(self):
        cleaned = super().clean()
        metodo  = cleaned.get('metodo_pago')
        cliente = cleaned.get('cliente')
        ref     = (cleaned.get('referencia_pago') or '').strip()
        f_pago  = cleaned.get('fecha_estimada_pago')

        if metodo == 'credito':
            if not cliente:
                self.add_error('cliente',
                    'Para ventas a crédito debe seleccionar o registrar el cliente.')
            if not f_pago:
                self.add_error('fecha_estimada_pago',
                    'Para ventas a crédito debe indicar la fecha estimada de pago.')

        # Referencia obligatoria para todos los métodos excepto crédito/fiado
        if metodo != 'credito' and not ref:
            self.add_error('referencia_pago',
                'Debe ingresar la referencia del pago realizado.')

        return cleaned


class DetalleVentaForm(forms.ModelForm):
    class Meta:
        model  = DetalleVenta
        fields = ['producto', 'cantidad', 'precio_unitario']
        widgets = {
            'producto': forms.Select(attrs={
                'class': 'form-select producto-select'}),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control cant-field', 'min': '1', 'placeholder': '0'}),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control precio-field',
                'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
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
            .order_by('nombre'))
        self.fields['producto'].empty_label  = '— Seleccionar producto —'
        self.fields['producto'].required     = False
        self.fields['cantidad'].required     = False
        self.fields['precio_unitario'].required = False

    def clean(self):
        cleaned  = super().clean()
        producto = cleaned.get('producto')
        cantidad = cleaned.get('cantidad')
        precio   = cleaned.get('precio_unitario')

        # Fila completamente vacía → se ignora
        if not producto and not cantidad and not precio:
            return cleaned

        if producto and not cantidad:
            raise ValidationError('Ingresa la cantidad.')
        if producto and not precio:
            raise ValidationError('Ingresa el precio unitario.')

        if producto and cantidad:
            if cantidad < 1:
                raise ValidationError('La cantidad debe ser al menos 1.')
            if cantidad > producto.stock_actual:
                raise ValidationError(
                    f'Stock insuficiente. Disponible: {producto.stock_actual} unidades.')
        return cleaned

    # CORRECCIÓN: has_changed no puede usar cleaned_data (no existe aún en ese punto)
    # Django lo llama antes de la validación para saber si la fila fue tocada.
    # Usamos los datos crudos del POST en su lugar.
    def has_changed(self):
        producto_key = self.add_prefix('producto')
        raw = self.data.get(producto_key, '')
        return bool(raw)


class BaseDetalleFormSet(BaseInlineFormSet):
    """Formset que ignora filas vacías y exige al menos un producto."""

    def clean(self):
        super().clean()
        productos_validos = 0
        for form in self.forms:
            if form.cleaned_data.get('DELETE'):
                continue
            if form.cleaned_data.get('producto'):
                productos_validos += 1
        if productos_validos == 0:
            raise ValidationError('Debes agregar al menos un producto a la venta.')


DetalleVentaFormSet = inlineformset_factory(
    Venta, DetalleVenta,
    form=DetalleVentaForm,
    formset=BaseDetalleFormSet,
    extra=1,
    min_num=0,
    validate_min=False,
    can_delete=True,
)
