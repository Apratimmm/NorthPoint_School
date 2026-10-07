from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from logic.models import *
from logic.context_processors import get_contact_info
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Prefetch
from django.views.decorators.cache import never_cache, cache_page

PAGE_CACHE_SECONDS = 300

@cache_page(PAGE_CACHE_SECONDS)
def home(request):
    welcome = HomePage.objects.filter(section="text").first()
    images = list(HomePage.objects.filter(section="image"))
    context = {
        "welcome": welcome,
        "home_images": images,
    }
    return render(request, "home.html", context)

@cache_page(PAGE_CACHE_SECONDS)
def about_us(request):
    sections = {s.section: s for s in AboutSection.objects.all()}
    messages = list(Messages.objects.all()[:2])
    message_1 = messages[0]
    message_2 = messages[1]
    return render(request, "about_us.html", {
        "history": sections.get("history"),
        "vision": sections.get("vision"),
        "mission": sections.get("mission"),
        "goal": sections.get("goal"),
        "message_1": message_1,
        "message_2": message_2,
    })

@cache_page(PAGE_CACHE_SECONDS)
def gallery(request):
    from django.core.paginator import Paginator
    events = GalleryEvent.objects.prefetch_related("images").only("id", "event_name", "event_date")
    paginator = Paginator(events, 4)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    return render(request, "gallery.html", {"page_obj": page_obj})

@never_cache
def user_login(request):
    return render(request, 'login.html')

@cache_page(PAGE_CACHE_SECONDS)
def notices(request):
    from django.core.paginator import Paginator
    notice_list = (
        Notice.objects.prefetch_related("images")
        .only("id", "title", "date", "body")
    )
    paginator = Paginator(notice_list, 4)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    return render(request, "notices.html", {"page_obj": page_obj})

@cache_page(PAGE_CACHE_SECONDS)
def results(request):
    SEE = SEEResults.objects.filter(id=1).first()
    toppers = SEEToppers.objects.all()[:5]
    PLUS2 = Plus2Results.objects.filter(id=1).first()
    plus2_toppers_by_stream = []
    fallback_used = False
    for stream_value, stream_label in Plus2Toppers.STREAM_CHOICES:
        stream_toppers = list(Plus2Toppers.objects.filter(stream=stream_value)[:5])
        plus2_toppers_by_stream.append({
            "label": stream_label,
            "value": stream_value,
            "toppers": stream_toppers,
            "display": True,
        })

    main_streams = {"humanities", "management", "computer_science"}

    def _stream_has_data(toppers):
        return any(t.name for t in toppers)

    main_has_data = any(
        _stream_has_data(next(s["toppers"] for s in plus2_toppers_by_stream if s["value"] == v))
        for v in main_streams
    )
    for s in plus2_toppers_by_stream:
        if s["value"] in main_streams:
            s["display"] = _stream_has_data(s["toppers"])
        else:
            s["display"] = (not main_has_data)
            if not main_has_data:
                fallback_used = True
    return render(request, "results.html", {
        "SEE": SEE,
        "toppers": toppers,
        "PLUS2": PLUS2,
        "plus2_toppers_by_stream": plus2_toppers_by_stream,
        "plus2_fallback_used": fallback_used,
    })

@cache_page(PAGE_CACHE_SECONDS)
def contact(request):
    return render(request, "contact.html")

@cache_page(PAGE_CACHE_SECONDS)
def academics(request):
    primary = Academic.objects.filter(school="primary").first()
    secondary = Academic.objects.filter(school="secondary").first()
    return render(request, "academics.html", {"primary": primary, "secondary": secondary})

@cache_page(PAGE_CACHE_SECONDS)
def faculty(request):
    leaders = FacultyLeader.objects.all()
    members = FacultyMember.objects.all()
    return render(request, "faculty.html", {"leaders": leaders, "members": members})

@cache_page(PAGE_CACHE_SECONDS)
def calendar(request):
    from datetime import date
    default_month = (date.today().month + 8) % 12 + 1
    raw = request.GET.get("month")
    try:
        month_id = int(raw) if raw else default_month
    except (TypeError, ValueError):
        month_id = default_month
    if month_id < 1 or month_id > 12:
        month_id = default_month

    month_info = (
        MonthInfo.objects
        .prefetch_related(
            Prefetch("events", queryset=MonthEvent.objects.only("id", "month_id", "event_date", "event_name", "event_type").order_by("event_date"))
        )
        .only("id", "month", "month_days", "month_start_day")
        .filter(month=month_id)
        .first()
    )

    events = list(month_info.events.all()) if month_info else []
    events_by_day = {}
    for e in events:
        events_by_day.setdefault(e.event_date, []).append(e)

    days = month_info.month_days if month_info and month_info.month_days else 31
    start = (month_info.month_start_day - 1) if month_info and month_info.month_start_day else 0

    grid = []
    week = []
    for _ in range(start):
        week.append({"day": None, "events": []})
    for d in range(1, days + 1):
        week.append({"day": d, "events": events_by_day.get(d, [])})
        if len(week) == 7:
            grid.append(week)
            week = []
    if week:
        while len(week) < 7:
            week.append({"day": None, "events": []})
        grid.append(week)

    prev_month = month_id - 1 if month_id > 1 else 12
    next_month = month_id + 1 if month_id < 12 else 1
    MONTH_NAMES = {num: name for num, name in MonthInfo.MONTH_CHOICES}

    return render(request, "calendar.html", {
        "month_info": month_info,
        "month_id": month_id,
        "month_name": (month_info.get_month_display() if month_info
                       else MONTH_NAMES.get(month_id, "")),
        "grid": grid,
        "events": events,
        "prev_month": prev_month,
        "next_month": next_month,
    })