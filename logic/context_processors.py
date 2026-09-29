from django.core.cache import cache
from .models import ContactInfo
import cloudinary.api

CACHE_KEY = "site_contact_info"
CACHE_TTL = 60 * 15
VIDEO_CACHE_KEY = "school_video_url"
VIDEO_CACHE_TTL = 60 * 15

def get_contact_info():
    contact = cache.get(CACHE_KEY)

    if contact is None:
        contact = ContactInfo.objects.first()
        cache.set(CACHE_KEY, contact, CACHE_TTL)

    return contact

# def fetch_video():
#     result = cloudinary.api.resources_by_asset_folder(
#         asset_folder="school-video",
#         resource_type="video",
#         max_results=1
#     )
#     resources = result.get("resources", [])
#     if resources:
#         video_url = resources[0].get("secure_url")
#         if video_url:
#             return video_url
#     return None
#
# def get_video_url():
#     url = cache.get(VIDEO_CACHE_KEY)
#
#     if url is None:
#         url = fetch_video()
#         if url:
#             cache.set(VIDEO_CACHE_KEY, url, VIDEO_CACHE_TTL)
#     return url

def global_context(request):
    contact = get_contact_info()

    # video_url = get_video_url()

    context = {}
    if contact:
        context.update({
            "logo_url": contact.logo.url if contact.logo else None,
            "contact_numbers": contact.get_telephone_list(),
            "email_address": contact.email,
            "facebook_link": contact.facebook_link,
        })

    return context
