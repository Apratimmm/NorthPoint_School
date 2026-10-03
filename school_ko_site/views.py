from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from logic.models import *
from logic.context_processors import get_contact_info
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
def home(request):
    welcome = HomePage.objects.filter(section="text").first()
    images = list(HomePage.objects.filter(section="image"))
    context = {
        "welcome": welcome,
        "home_images": images,
    }
    return render(request, "home.html", context)

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

def gallery(request):
    events = GalleryEvent.objects.prefetch_related("images").all()
    return render(request, "gallery.html", {"events": events})

def calendar(request):
    return render(request,"calendar.html")

@never_cache
def user_login(request):
    return render(request, 'login.html')

def notices(request):
    notice_list = Notice.objects.all()
    return render(request, "notices.html", {"notices": notice_list})

def results(request):
    SEE = SEEResults.objects.filter(id=1).first()
    toppers = Topper.objects.all()[:5]
    return render(request, "results.html", {"SEE": SEE, "toppers": toppers})

def contact(request):
    return render(request, "contact.html")

def academics(request):
    primary = Academic.objects.filter(school="primary").first()
    secondary = Academic.objects.filter(school="secondary").first()
    return render(request, "academics.html", {"primary": primary, "secondary": secondary})

def faculty(request):
    leaders = FacultyLeader.objects.all()
    members = FacultyMember.objects.all()
    return render(request, "faculty.html", {"leaders": leaders, "members": members})

# def academics(request):
#     schools = {
#         s.school: s for s in Academic.objects.all()
#     }
#
#     context = {
#         "primary": schools.get("primary"),
#         "secondary": schools.get("secondary"),
#     }
#     return render(request, 'academics.html', context)

# MONTH_NAMES = [name for _, name in MonthInfo.MONTH_CHOICES]
# MONTH_NAMES_BY_ID = dict(MonthInfo.MONTH_CHOICES)
#
# def get_month_data(month_id):
#     try:
#         m = MonthInfo.objects.prefetch_related("events").get(month=month_id)
#         return {
#             "month": m.month,
#             "monthName": m.get_month_display(),
#             "daysInMonth": m.month_days or 31,
#             "firstDay": (m.month_start_day or 1) - 1,
#             "events": {
#                 str(e.event_date): {"label": e.event_name, "type": e.event_type}
#                 for e in m.events.all()
#             },
#         }
#     except MonthInfo.DoesNotExist:
#         idx = month_id - 1
#         return {
#             "month": month_id,
#             "monthName": MONTH_NAMES_BY_ID.get(month_id, "Unknown"),
#             "daysInMonth": 31,
#             "firstDay": 0,
#             "events": {},
#         }

# def calendar(request):
#     month_data = get_month_data(1)
#     return render(request, "calendar.html", {
#         "server_data": {
#             "hasData": True,
#             "currentMonth": 1,
#             "month": month_data,
#         }
#     })

# def month_data(request, month_id):
#     month_data = get_month_data(month_id)
#     return JsonResponse(month_data)

# def results(request):
#     yearly_results = YearlyResult.objects.all()[:3]
#     toppers = Topper.objects.all()[:5]
#
#     context = {
#         "yearly_results": yearly_results,
#         "toppers": toppers,
#     }
#     return render(request, "results.html", context)

# def committee(request):
#     committees = Committee.objects.prefetch_related("people").all()
#     for c in committees:
#         members_by_post = {}
#         for p in c.people.all():
#             members_by_post.setdefault(p.post, []).append(p)
#         c.posts_with_members = [
#             (key, label, members_by_post.get(key, []))
#             for key, label in Committee.POST_FIELDS
#             if members_by_post.get(key)
#         ]
#     return render(request, "committee.html", {"committees": committees})
#
#  def notices(request):
#    notice_list = Notice.objects.all()
#    return render(request, "notices.html", {"notices": notice_list})
#
# NEPALI_CHROME = {
#     "notice_word": "सूचना",
#     "date_word": "मिति",
#     "subject_word": "विषय",
#     "principal_word": "प्रिन्सिपल",
# }

# def view_notice(request, notice_id):
#     notice = get_object_or_404(Notice, id=notice_id)
#     signature, _ = PrincipalSignature.objects.get_or_create(id=1)
#     chrome = NEPALI_CHROME if notice.language == "ne" else {}
#     return render(request, "base_notice.html", {"notice": notice, "signature": signature, "chrome": chrome})