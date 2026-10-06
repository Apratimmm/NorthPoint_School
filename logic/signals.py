from django.core.cache import cache
from django.db.models.signals import post_delete, post_save

from . import models

CONTENT_MODELS = (
    models.AboutSection,
    models.Messages,
    models.Academic,
    models.ContactInfo,
    models.SEEToppers,
    models.GalleryEvent,
    models.GalleryImage,
    models.MonthInfo,
    models.MonthEvent,
    models.Notice,
    models.NoticeImage,
    models.HomePage,
    models.FacultyLeader,
    models.FacultyMember,
    models.SEEResults,
    models.Plus2Results,
    models.Plus2Toppers,
)

def clear_site_cache(**kwargs):
    cache.clear()

for _model in CONTENT_MODELS:
    post_save.connect(
        clear_site_cache,
        sender=_model,
        dispatch_uid=f"clear_site_cache_on_save_{_model.__name__}",
    )
    post_delete.connect(
        clear_site_cache,
        sender=_model,
        dispatch_uid=f"clear_site_cache_on_delete_{_model.__name__}",
    )
