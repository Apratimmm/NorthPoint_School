from django.apps import AppConfig


class LogicConfig(AppConfig):
    name = "logic"

    def ready(self):
        from . import signals  # noqa: F401
