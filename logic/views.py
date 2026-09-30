import pprint

from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import *
from .context_processors import CACHE_KEY
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import os
import resend
import json
import cloudinary.api

resend.api_key = os.environ.get("RESEND_API_KEY")
def verify_user(request):

    if request.method == 'POST':
        name = request.POST.get('name')
        password = request.POST.get('password')

        user = authenticate(request, username=name, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password")
            return redirect("login")

def user_logout(request):
    logout(request)
    return redirect("login")

@login_required
def dashboard(request):
    return render(request, "dashboard.html")

def _delete_image_field(instance, field_name, request, success_message):

    image = getattr(instance, field_name, None)
    if image:
        image.delete(save=False)
        setattr(instance, field_name, None)
        instance.save()
        messages.success(request, success_message)

@login_required
def edit_contact(request):
    contact, _ = ContactInfo.objects.get_or_create(id=1)
    if request.method == "POST":
        form_type = request.POST.get("form_type") or request.POST.get("about") or request.POST.get("about")

        if form_type == "delete_logo":
            _delete_image_field(contact, "logo", request, "Logo deleted.")
            cache.delete(CACHE_KEY)
            return redirect("edit_contact")

        contact.telephone = request.POST.get("telephone", "")
        contact.email = request.POST.get("email", "")
        contact.facebook_link = request.POST.get("facebook_link", "")
        if request.FILES.get("logo"):
            contact.logo = request.FILES["logo"]
        contact.save()
        cache.delete(CACHE_KEY)

        messages.success(request, "Contact information updated successfully!")
        return redirect("edit_contact")

    context = {
        "contact": contact,
    }
    return render(request, "edit_contact.html", context)

@login_required
def edit_academics(request):
    sections = [
        ("primary",   Academic.objects.get_or_create(school="primary")[0],
            ["description", "quote", "teacher_name", "teacher_designation"], "image", "Primary school image deleted.", "primary"),
        ("secondary", Academic.objects.get_or_create(school="secondary")[0],
            ["description", "quote", "teacher_name", "teacher_designation"], "image", "Secondary school image deleted.", "secondary"),
    ]

    if request.method == "POST":
        form_type = request.POST.get("form_type") or request.POST.get("about")

        if form_type and form_type.startswith("delete_"):
            for key, instance, _text_fields, image_field, delete_msg, _section_key in sections:
                if image_field and form_type == f"delete_{key}_{image_field}":
                    _delete_image_field(instance, image_field, request, delete_msg)
                    return redirect("edit_academics")

        for key, instance, text_fields, image_field, _delete_msg, section_key in sections:
            if form_type == section_key:
                for field in text_fields:
                    setattr(instance, field, request.POST.get(f"{section_key}_{field}", ""))
                if image_field and request.FILES.get(f"{section_key}_{image_field}"):
                    setattr(instance, image_field, request.FILES[f"{section_key}_{image_field}"])
                instance.save()
                messages.success(request, f"{key.capitalize()} school content updated successfully!")
                return redirect("edit_academics")

    context = {key: instance for key, instance, *_ in sections}
    return render(request, "edit_academics.html", context)

@login_required
def show_events(request):
    events = GalleryEvent.objects.all().only("id", "event_name", "event_date")
    return render(request, "show_events.html", {"events": events})

@login_required
def add_event(request):
    if request.method == "POST":
        event_name = request.POST.get("event_name", "").strip()
        event_date = request.POST.get("event_date","").strip()

        if not event_name or not event_date:
                messages.error(request, "Title and date both are required.")
                return render(request, "add_event.html", {
                    "title": event_name, "date": event_date })

        event = GalleryEvent.objects.create(
            event_name=event_name,
            event_date=event_date,
            first_name=event_name
        )

        images = request.FILES.getlist("images")
        GalleryImage.objects.bulk_create(
            [GalleryImage(event=event, image=img) for img in images]
        )

        messages.success(request, "Event created successfully!")
        return redirect("show_events")

    return render(request,"add_event.html")

@login_required
def edit_event(request, event_id):
    event = get_object_or_404(GalleryEvent.objects.prefetch_related("images"), id=event_id)

    if request.method == "POST":
        form_type = request.POST.get("form_type") or request.POST.get("about") or request.POST.get("about")

        if form_type == "update_details":
            event_name = request.POST.get("event_name", "").strip()
            event_date = request.POST.get("event_date", "").strip()

            if event_name and event_date:
                event.event_name = event_name
                event.event_date = event_date
                event.save()
                messages.success(request, "Event name and/or date updated successfully!")
            else:
                messages.error(request, "Event name and date are required.")

            return redirect("edit_event", event_id=event.id)

        elif form_type == "add_images":
            images = request.FILES.getlist("images")
            GalleryImage.objects.bulk_create(
                [GalleryImage(event=event, image=img) for img in images]
            )

            messages.success(request, "Images added successfully!")
            return redirect("edit_event", event_id=event.id)

        elif form_type == "delete_image":
            image_id = request.POST.get("image_id")
            image = get_object_or_404(GalleryImage, id=image_id, event=event)
            image.delete()
            messages.success(request, "Image deleted successfully!")
            return redirect("edit_event", event_id=event.id)

    context = {
        "event": event,
    }
    return render(request, "edit_event.html", context)

@login_required
def delete_event(request, event_id):
    event = get_object_or_404(GalleryEvent, id=event_id)
    first_name = event.first_name
    event_name = event.event_name
    event.delete()
    try:
        cloudinary.api.delete_folder(f"gallery/{first_name}")
    except Exception:
        pass
    messages.success(request, f'Event "{event_name}" deleted successfully!')
    return redirect("show_events")

@login_required
def show_notices(request):
    notices = Notice.objects.all().only("id","title","date")
    return render(request, "show_notices.html", {"notices": notices})

@login_required
def  add_notice(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        body = request.POST.get("body", "").strip()
        date = request.POST.get("date", "").strip()
        language = request.POST.get("language", "en").strip()

        images = request.FILES.getlist("images")

        if not title or not date or not images:
                messages.error(request, "Title, date and at least one photo is required.")
                return render(request, "add_notice.html", {
                    "title": title, "body": body, "date": date,
                    "language": language })

        notice = Notice.objects.create(
            title=title,
            body=body,
            date=date,
            language=language
        )

        NoticeImage.objects.bulk_create(
            [NoticeImage(notice=notice, image=img) for img in images]
        )

        messages.success(request, "Notice created successfully!")
        return redirect("show_notices")

    return render(request, "add_notice.html")

@login_required
def edit_notice(request, notice_id):
    notice = get_object_or_404(Notice, id=notice_id)

    if request.method == "POST":
        form_type = request.POST.get("form_type", "update_details")

        if form_type == "add_images":
            images = request.FILES.getlist("images")
            for img in images:
                NoticeImage.objects.create(notice=notice, image=img)
            messages.success(request, "Images uploaded successfully!")
            return redirect("edit_notice", notice_id=notice.id)

        if form_type == "delete_image":
            image_id = request.POST.get("image_id")
            img = get_object_or_404(NoticeImage, id=image_id, notice=notice)
            img.image.delete(save=False)
            img.delete()
            messages.success(request, "Image deleted successfully!")
            return redirect("edit_notice", notice_id=notice.id)

        title = request.POST.get("title", "").strip()
        body = request.POST.get("body", "").strip()
        date = request.POST.get("date", "").strip()

        if not title or not date:
            messages.error(request, "Title and date are required.")
            return render(request, "edit_notice.html", {
                "notice": notice,
                "submitted_title": title,
                "submitted_body": body,
                "submitted_date": date,
            })

        notice.title = title
        notice.date = date
        notice.save()
        messages.success(request, "Notice updated successfully!")
        return redirect("edit_notice", notice_id=notice.id)

    return render(request, "edit_notice.html", {"notice": notice})

@login_required
def delete_notice(request, notice_id):
    notice = get_object_or_404(Notice, id=notice_id)
    notice_title = notice.title
    prefix = f"notices/{notice.id}/"
    try:
        result = cloudinary.api.delete_resources_by_prefix(
            prefix,
            resource_type="image",
            type="upload",
            invalidate=True
        )
        cloudinary.api.delete_folder(f"notices/{notice.id}")

    except Exception as e:
        print(f"Cloudinary deletion error: {e}")

    notice.delete()
    messages.success(request, f'Notice "{notice_title}" deleted successfully!')
    return redirect("show_notices")

@login_required
def edit_about_us(request):
    if request.method == "POST":
        form_type = request.POST.get("form_type") or request.POST.get("about")

        if form_type == "delete_message_image":
            message_id = request.POST.get("message_id")
            msg = Messages.objects.filter(id=message_id).first() if message_id else None
            if msg and msg.person_image:
                msg.person_image.delete(save=False)
                msg.person_image = None
                msg.save()
                messages.success(request, "Person's photo deleted.")
            return redirect("edit_about_us")

        if form_type == "message":
            message_id = request.POST.get("message_id")
            msg = Messages.objects.filter(id=message_id).first() if message_id else None
            if msg:
                msg.message_title = request.POST.get("message_title", "")
                msg.message_body = request.POST.get("message_body", "")
                msg.person_name = request.POST.get("person_name", "")
                msg.person_position = request.POST.get("person_position", "")
                if request.FILES.get("person_image"):
                    msg.person_image = request.FILES["person_image"]
                msg.save()
                messages.success(request, "Message updated successfully!")
            return redirect("edit_about_us")

        if form_type == "history":
            s, _ = AboutSection.objects.get_or_create(section="history")
            s.text = request.POST.get("history", "")
            s.save()
            messages.success(request, "History updated successfully!")

        elif form_type == "vision":
            s, _ = AboutSection.objects.get_or_create(section="vision")
            s.text = request.POST.get("vision", "")
            s.save()
            messages.success(request, "Vision updated successfully!")

        elif form_type == "mission":
            s, _ = AboutSection.objects.get_or_create(section="mission")
            s.text = request.POST.get("mission", "")
            s.save()
            messages.success(request, "Mission updated successfully!")

        elif form_type == "goal":
            s, _ = AboutSection.objects.get_or_create(section="goal")
            s.text = request.POST.get("goal", "")
            s.save()
            messages.success(request, "Goal updated successfully!")

    sections_qs = AboutSection.objects.all()
    sections = {s.section: s for s in sections_qs}
    messagess = list(Messages.objects.all()[:2])
    return render(request, "edit_about_us.html", {
        "sections": sections,
        "messagess": messagess,
    })

# @login_required
# def edit_about(request):
#     sections = [
#         ("history",     AboutSection.objects.get_or_create(section="history")[0],
#             ["heading", "text"], "image", "History image deleted."),
#         ("principal",   AboutSection.objects.get_or_create(section="principal")[0],
#             ["heading", "text", "person_name", "person_title"], "image", "Principal photo deleted."),
#         ("chairperson", AboutSection.objects.get_or_create(section="chairperson")[0],
#             ["heading", "text", "person_name", "person_title"], "image", "Chairperson photo deleted."),
#     ]
#
#     if request.method == "POST":
#         form_type = request.POST.get("form_type") or request.POST.get("about") or request.POST.get("about")
#
#         if form_type and form_type.startswith("delete_"):
#             for key, instance, _text_fields, image_field, delete_msg in sections:
#                 if image_field and form_type == f"delete_{key}_{image_field}":
#                     _delete_image_field(instance, image_field, request, delete_msg)
#                     return redirect("edit_about")
#
#         for section_key, instance, text_fields, image_field, _delete_msg in sections:
#             for field in text_fields:
#                 setattr(instance, field, request.POST.get(f"{section_key}_{field}", ""))
#             if image_field and request.FILES.get(f"{section_key}_{image_field}"):
#                 setattr(instance, image_field, request.FILES[f"{section_key}_{image_field}"])
#             instance.save()
#
#         messages.success(request, "About Us content updated successfully!")
#         return redirect("edit_about")
#
#     context = {key: instance for key, instance, *_ in sections}
#     return render(request, "edit_about.html", context)
#

#
# @require_POST
# def send_email(request):
#     name    = request.POST.get("name", "").strip()
#     email   = request.POST.get("email", "").strip()
#     subject = request.POST.get("subject", "").strip()
#     message = request.POST.get("message", "").strip()
#     actual_message = f"""
#     <p><strong>Name:</strong> {name}</p>
#     <p><strong>Email:</strong> {email}</p>
#     <p><strong>Subject:</strong> {subject}</p>
#     <hr>
#     <p>{message}</p> """
#
#     try:
#         resend.Emails.send({
#             "from": "onboarding@resend.dev",
#             "to": "englishshantinagar@gmail.com",
#             "reply_to": email,
#             "subject": f"Mail received from the school's website",
#             "html": actual_message})
#
#         return JsonResponse({
#             "success": True,
#             "message": "Thank you! Your message has been sent successfully."
#         })
#
#     except Exception:
#             return JsonResponse({
#             "success": False,
#             "message": "Sorry, something went wrong. Please try again later."
#         }, status=500)
#

#
# @login_required
# def edit_results(request):
#     yearly_results = YearlyResult.objects.all()[:3]
#     toppers = Topper.objects.all()[:5]
#
#     if request.method == "POST":
#         form_type = request.POST.get("form_type") or request.POST.get("about") or request.POST.get("about")
#
#         if form_type == "yearly":
#             for i in range(3):
#                 result_id = request.POST.get(f"result_id_{i}")
#                 year = request.POST.get(f"year_{i}")
#
#                 if not year:
#                     continue
#
#                 if result_id:
#                     result = get_object_or_404(YearlyResult, id=result_id)
#                 else:
#                     result = YearlyResult()
#
#                 result.year = year
#                 result.candidates = request.POST.get(f"candidates_{i}") or 0
#                 result.pass_rate = request.POST.get(f"pass_rate_{i}") or 0
#                 result.highest = request.POST.get(f"highest_{i}") or 0
#                 result.highest_scorer_name = request.POST.get(f"highest_scorer_name_{i}") or ""
#                 if request.FILES.get(f"highest_scorer_image_{i}"):
#                     result.highest_scorer_image = request.FILES[f"highest_scorer_image_{i}"]
#                 result.save()
#
#             messages.success(request, "Yearly results saved successfully!")
#
#         elif form_type == "delete_yearly_image":
#             result = get_object_or_404(YearlyResult, id=request.POST.get("result_id"))
#             _delete_image_field(result, "highest_scorer_image", request, "Top scorer photo deleted.")
#
#         elif form_type == "delete_topper_image":
#             topper = get_object_or_404(Topper, id=request.POST.get("topper_id"))
#             _delete_image_field(topper, "image", request, "Topper photo deleted.")
#
#         elif form_type == "topper":
#             for i in range(5):
#                 topper_id = request.POST.get(f"topper_id_{i}")
#                 name = request.POST.get(f"name_{i}")
#
#                 if not name:
#                     continue
#
#                 if topper_id:
#                     topper = get_object_or_404(Topper, id=topper_id)
#                 else:
#                     topper = Topper()
#
#                 topper.name = name
#                 topper.score = request.POST.get(f"score_{i}") or 0
#
#                 if request.FILES.get(f"image_{i}"):
#                     topper.image = request.FILES[f"image_{i}"]
#
#                 topper.save()
#
#             messages.success(request, "Top scorers saved successfully!")
#
#         return redirect("edit_results")
#
#     context = {
#         "yearly_results": yearly_results,
#         "toppers": toppers,
#     }
#     return render(request, "edit_results.html", context)
#

#
# @login_required
# def show_calenders(request):
#     months = MonthInfo.MONTH_CHOICES
#
#     return render(request, "show_calenders.html",{"months": months})
#
# @login_required
# def show_calender(request,month_id):
#     month = MonthInfo.objects.prefetch_related("events").get(month=month_id)
#
#     if month:
#         return render(request, "show_calender.html", {
#             "server_data": {
#                 "hasData": True,
#                 "monthName": month.get_month_display(),
#                 "daysInMonth": month.month_days or 31,
#                 "firstDay": (month.month_start_day or 1) - 1,
#                 "events": {
#                     str(e.event_date): {"label": e.event_name, "type": e.event_type}
#                     for e in month.events.all()
#                 },
#             },
#         })
#
#     return render(request, "show_calender.html", {"server_data": {"hasData": False}})
#
# @login_required
# @require_POST
# def update_month(request):
#     data = json.loads(request.body)
#     month_name = data.get("monthName", "").strip()
#     days_in_month = data.get("daysInMonth")
#     start_day = data.get("startDay")
#     events = data.get("events", [])
#
#     month_choices = {name: num for num, name in MonthInfo.MONTH_CHOICES}
#     month_number = month_choices.get(month_name)
#
#     if month_number is None:
#         return JsonResponse(
#             {"success": False, "message": f"Unknown month name: {month_name}"},
#             status=400,
#         )
#
#     month_info, created = MonthInfo.objects.get_or_create(month=month_number)
#     month_info.month_days = days_in_month
#     month_info.month_start_day = start_day + 1
#     month_info.save()
#
#     month_info.events.all().delete()
#     for ev in events:
#         MonthEvent.objects.create(
#             month=month_info,
#             event_date=ev.get("event_date"),
#             event_name=ev.get("event_name", ""),
#             event_type=ev.get("event_type", "event"),
#         )
#
#     return JsonResponse(
#         {"success": True, "message": "Calendar has been updated !   !"}
#     )
#
# @login_required
# def show_committees(request):
#     committees = Committee.objects.all().only("id", "committee_name")
#     return render(request, "show_committees.html", {"committees": committees})
#
# @login_required
# def add_committee(request):
#     if request.method == "POST":
#         committee_name = request.POST.get("committee_name", "").strip()
#         if not committee_name:
#             messages.error(request, "Committee name is required.")
#             return render(
#                 request,
#                 "add_committee.html",
#                 {
#                     "committee": Committee(
#                         committee_name=committee_name,
#                         description=request.POST.get("description", ""),
#                     ),
#                 },
#             )
#
#         committee = Committee(
#             committee_name=committee_name,
#             description=request.POST.get("description", ""),
#         )
#         committee.save()
#
#         messages.success(request, "Committee created. Add the office bearers now.")
#         return redirect("add_committee_people", committee_id=committee.id)
#
#     return render(
#         request,
#         "add_committee.html",
#         {"committee": Committee(committee_name="")},
#     )
#
# @login_required
# def add_committee_people(request, committee_id):
#     committee = get_object_or_404(Committee, id=committee_id)
#
#     if request.method == "POST":
#         saved = 0
#         i = 0
#         while i < 100:
#             name = request.POST.get(f"name_{i}", "").strip()
#             post = request.POST.get(f"post_{i}", "")
#             file = request.FILES.get(f"image_{i}")
#             if not name:
#                 i += 1
#                 continue
#
#             person, _ = CommitteePeople.objects.get_or_create(
#                 committee=committee,
#                 post=post,
#                 name=name,
#             )
#             if file:
#                 person.image = file
#                 person.save()
#             saved += 1
#             i += 1
#
#         if saved:
#             messages.success(request, f"New office bearer(s) were added.")
#         else:
#             messages.info(request, "No new office bearer(s) were added.")
#         return redirect("show_committees")
#
#     return render(
#         request,
#         "add_committee_people.html",
#         {"committee": committee},
#     )
#
# @login_required
# def delete_committee_people(request, person_id):
#     person = get_object_or_404(CommitteePeople, id=person_id)
#     committee_id = person.committee_id
#     name = person.name
#
#     if person.image:
#         person.image.delete(save=False)
#     person.delete()
#
#     messages.success(request, f'Removed the office bearer from committee.')
#     return redirect("add_committee_people", committee_id=committee_id)
#
# @login_required
# def delete_committee(request, committee_id):
#     committee = get_object_or_404(Committee, id=committee_id)
#     committee_name = committee.committee_name
#
#     for person in list(committee.people.all()):
#         if person.image:
#             person.image.delete(save=False)
#         person.delete()
#
#     committee.delete()
#     cloudinary.api.delete_folder(f"committee/{committee_name}")
#     messages.success(request, f'Committee "{committee_name}" deleted successfully!')
#     return redirect("show_committees")
#

#
# @login_required
# def edit_signature(request):
#     signature, _ = PrincipalSignature.objects.get_or_create(id=1)
#
#     if request.method == "POST":
#         form_type = request.POST.get("form_type") or request.POST.get("about") or request.POST.get("about")
#
#         if form_type == "delete_signature":
#             _delete_image_field(signature, "image", request, "Signature deleted.")
#             return redirect("edit_signature")
#
#         signature.name = request.POST.get("name", "").strip()
#         if request.FILES.get("person_image"):
#             signature.image = request.FILES["image"]
#         signature.save()
#         messages.success(request, "Principal details updated successfully!")
#         return redirect("edit_signature")
#
#     return render(request, "edit_signature.html", {"signature": signature})
#
# @login_required
# def edit_school_video(request):
#     return render(request, 'edit_school_video.html')


