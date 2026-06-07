from django.apps import AppConfig

class ComprasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'compras'
    verbose_name = 'Gestión de Compras y Abastecimiento'

    def ready(self):
        # Al importar aquí adentro, Django ya cargó todo y no se rompe
        import compras.signals  # noqa