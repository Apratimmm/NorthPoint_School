from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import *
from .context_processors import CACHE_KEY
from django.http import JsonResponse, Http404
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

        cache.clear()

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
            cache.clear()

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
    event_pk = event.id
    event_name = event.event_name
    event.delete()
    try:
        cloudinary.api.delete_folder(f"gallery/{event_pk}")
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
        cache.clear()

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
        notice.body = body
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

            message_title = request.POST.get("message_title", "")
            message_body = request.POST.get("message_body", "")
            person_name = request.POST.get("person_name", "")
            person_position = request.POST.get("person_position", "")

            if msg:
                msg.message_title = message_title
                msg.message_body = message_body
                msg.person_name = person_name
                msg.person_position = person_position
                if request.FILES.get("person_image"):
                    msg.person_image = request.FILES["person_image"]
                msg.save()
                messages.success(request, "Message updated successfully!")
            else:
                new_msg = Messages.objects.create(
                    message_title=message_title,
                    message_body=message_body,
                    person_name=person_name,
                    person_position=person_position,
                )
                if request.FILES.get("person_image"):
                    new_msg.person_image = request.FILES["person_image"]
                    new_msg.save()
                messages.success(request, "Message added successfully!")
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

@login_required
def edit_school_video(request):
    return render(request, 'edit_school_video.html')

@login_required
def edit_homepage(request):
    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == "delete_home_image":
            image_id = request.POST.get("image_id")
            img = HomePage.objects.filter(id=image_id, section="image").first()
            if img:
                img.home_image.delete(save=False)
                img.delete()
                messages.success(request, "Image deleted successfully!")
            return redirect("edit_homepage")

        if form_type == "add_image":
            images = request.FILES.getlist("home_image")
            if images:
                HomePage.objects.bulk_create([
                    HomePage(section="image", home_image=img) for img in images
                ])
                cache.clear()
                messages.success(request, f"{len(images)} homepage image(s) added successfully!")
            return redirect("edit_homepage")

        if form_type == "welcome_message":
            welcome, _ = HomePage.objects.get_or_create(section="text")
            welcome.welcome_message = request.POST.get("welcome_message", "")
            welcome.save()
            messages.success(request, "Welcome message updated successfully!")
            return redirect("edit_homepage")

    context = {
        "welcome": HomePage.objects.filter(section="text").first(),
        "images": HomePage.objects.filter(section="image"),
    }
    return render(request, 'edit_homepage.html', context)

@login_required
def edit_results(request):
    return render(request,'edit_results.html')

@login_required
def edit_SEE_results(request):
    SEE, _ = SEEResults.objects.get_or_create(id=1)
    if request.method == "POST":
        SEE.year = int(request.POST.get("year", "") or 0)
        SEE.candidate_count = int(request.POST.get("candidate_count", 0) or 0)
        SEE.pass_rate = float(request.POST.get("pass_rate", 0) or 0)
        SEE.average_gpa = float(request.POST.get("average_gpa", 0) or 0)
        SEE.save()
        messages.success(request, "SEE information updated!")
        return redirect("edit_SEE_results")
    return render(request, "edit_SEE_results.html", {"SEE": SEE})

@login_required
def edit_SEE_toppers(request):
    toppers = list(SEEToppers.objects.all()[:5])

    for i in range(5):
        if i >= len(toppers):
            toppers.append(SEEToppers.objects.create(score=0))

    if request.method == "POST":
        form_type = request.POST.get("form_type") or request.POST.get("about")

        if form_type == "delete_topper_image":
            topper_id = request.POST.get("topper_id")
            topper = SEEToppers.objects.filter(id=topper_id).first()
            if topper and topper.image:
                topper.image.delete(save=False)
                topper.image = None
                topper.save()
                messages.success(request, "Image deleted.")
            return redirect("edit_SEE_toppers")

        if form_type == "topper":
            topper_id = request.POST.get("topper_id")
            topper = SEEToppers.objects.filter(id=topper_id).first()
            if topper:
                topper.name = request.POST.get("name", "").strip()
                try:
                    topper.score = float(request.POST.get("score", 0) or 0)
                except:
                    topper.score = 0
                if request.FILES.get("image"):
                    topper.image = request.FILES["image"]
                topper.save()
                messages.success(request, "Topper updated!")
            return redirect("edit_SEE_toppers")
    return render(request, "edit_SEE_toppers.html", {"toppers": toppers})

@login_required
def edit_Plus2_results(request):
    PLUS2, _ = Plus2Results.objects.get_or_create(id=1)
    if request.method == "POST":
        PLUS2.year = int(request.POST.get("year", "") or 0)
        PLUS2.candidate_count = int(request.POST.get("candidate_count", 0) or 0)
        PLUS2.pass_rate = float(request.POST.get("pass_rate", 0) or 0)
        PLUS2.average_gpa = float(request.POST.get("average_gpa", 0) or 0)
        PLUS2.save()
        messages.success(request, "Plus2 information updated!")
        return redirect("edit_Plus2_results")
    return render(request, "edit_Plus2_results.html", {"PLUS2": PLUS2})

@login_required
def show_streams(request):
    return render(request, "show_streams.html", {"streams": Plus2Toppers.STREAM_CHOICES})

@login_required
def edit_Plus2_toppers(request, stream):
    stream_labels = dict(Plus2Toppers.STREAM_CHOICES)
    if stream not in stream_labels:
        raise Http404("Unknown stream")

    if request.method == "POST":
        form_type = request.POST.get("form_type") or request.POST.get("about")

        if form_type == "delete_topper_image":
            topper_id = request.POST.get("topper_id")
            topper = Plus2Toppers.objects.filter(id=topper_id).first()
            if topper and topper.image:
                topper.image.delete(save=False)
                topper.image = None
                topper.save()
                messages.success(request, "Image deleted.")
            return redirect("edit_Plus2_toppers", stream=stream)

        if form_type == "topper":
            topper_id_raw = request.POST.get("topper_id", "").strip()
            name = request.POST.get("name", "").strip()
            score_raw = request.POST.get("score", "0").strip()
            try:
                wanted_score = float(score_raw) if score_raw not in ("", "None", "nan") else 0.0
            except (TypeError, ValueError):
                wanted_score = 0.0

            if not topper_id_raw:
                messages.error(request, "No topper ID submitted.")
                return redirect("edit_Plus2_toppers", stream=stream)

            try:
                topper_id = int(topper_id_raw)
            except (TypeError, ValueError):
                messages.error(request, f"Invalid topper ID: {topper_id_raw!r}")
                return redirect("edit_Plus2_toppers", stream=stream)

            topper = Plus2Toppers.objects.filter(id=topper_id).first()
            if not topper:
                messages.error(request, f"Topper id={topper_id} not found in stream {stream!r}.")
                return redirect("edit_Plus2_toppers", stream=stream)

            topper.name = name
            posted_stream = request.POST.get("stream", "").strip()
            if posted_stream in stream_labels:
                topper.stream = posted_stream
            topper.score = wanted_score
            if request.FILES.get("image"):
                topper.image = request.FILES["image"]
            topper.save()
            after = Plus2Toppers.objects.get(id=topper.id)
            messages.success(
                request,
                "Topper data updated!")
            return redirect("edit_Plus2_toppers", stream=stream)

    rows = list(Plus2Toppers.objects.filter(stream=stream))
    for _ in range(len(rows), 5):
        rows.append(Plus2Toppers.objects.create(score=0, stream=stream))
    return render(request, "edit_Plus2_toppers.html", {
        "stream": stream,
        "stream_label": stream_labels[stream],
        "toppers": rows,
        "streams": Plus2Toppers.STREAM_CHOICES,
    })

@require_POST
def send_email(request):
    name    = request.POST.get("name", "").strip()
    email   = request.POST.get("email", "").strip()
    subject = request.POST.get("subject", "").strip()
    message = request.POST.get("message", "").strip()
    actual_message = f"""
    <p><strong>Name:</strong> {name}</p>
    <p><strong>Email:</strong> {email}</p>
    <p><strong>Subject:</strong> {subject}</p>
    <hr>
    <p>{message}</p> """

    try:
        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": "northpoint222@gmail.com",
            "reply_to": email,
            "subject": f"Mail received from the school's website",
            "html": actual_message})

        return JsonResponse({
            "success": True,
            "message": "Sent!"
        })

    except Exception:
            return JsonResponse({
            "success": False,
            "message": "Failed - please retry."
        }, status=500)

@login_required
def show_months(request):
    months = MonthInfo.MONTH_CHOICES

    return render(request, "show_months.html", {"months": months})

@login_required
def show_calendar(request,month_id):
    month = MonthInfo.objects.prefetch_related("events").filter(month=month_id).first()

    if month:
        return render(request, "show_calendar.html", {
            "server_data": {
                "hasData": True,
                "monthName": month.get_month_display(),
                "daysInMonth": month.month_days or 31,
                "firstDay": (month.month_start_day or 1) - 1,
                "events": {
                    str(e.event_date): {"label": e.event_name, "type": e.event_type}
                    for e in month.events.all()
                },
            },
        })

    return render(request, "show_calendar.html", {"server_data": {"hasData": False}})

@login_required
@require_POST
def update_month(request):
    data = json.loads(request.body)
    month_name = data.get("monthName", "").strip()
    days_in_month = data.get("daysInMonth")
    start_day = data.get("startDay")
    events = data.get("events", [])

    month_choices = {name: num for num, name in MonthInfo.MONTH_CHOICES}
    month_number = month_choices.get(month_name)

    if month_number is None:
        return JsonResponse(
            {"success": False, "message": f"Unknown month name: {month_name}"},
            status=400,
        )

    month_info, created = MonthInfo.objects.get_or_create(month=month_number)
    month_info.month_days = days_in_month
    month_info.month_start_day = start_day + 1
    month_info.save()

    month_info.events.all().delete()
    for ev in events:
        MonthEvent.objects.create(
            month=month_info,
            event_date=ev.get("event_date"),
            event_name=ev.get("event_name", ""),
            event_type=ev.get("event_type", "event"),
        )

    return JsonResponse(
        {"success": True, "message": "Calendar has been updated !   !"}
    )

@login_required
def edit_faculty(request):
    return render(request, "edit_faculty.html")

@login_required
def edit_leaders(request):
    leaders = FacultyLeader.objects.all()
    if request.method == "POST":
        form_type = request.POST.get("form_type", "")

        if form_type == "delete_leader":
            lid = request.POST.get("leader_id")
            leader = FacultyLeader.objects.filter(id=lid).first()
            if leader:
                if leader.image: leader.image.delete(save=False)
                leader.delete()
                messages.success(request, "Leader deleted.")
            return redirect("edit_leaders")

        leader_id = request.POST.get("leader_id")
        name = request.POST.get("name", "").strip()
        designation = request.POST.get("designation", "").strip()
        if leader_id:
            leader = FacultyLeader.objects.filter(id=leader_id).first()
            if leader and name:
                leader.name = name
                leader.designation = designation
                if request.FILES.get("image"):
                    if leader.image: leader.image.delete(save=False)
                    leader.image = request.FILES["image"]
                leader.save()
                messages.success(request, "Leader updated!")
        else:
            if name:
                leader = FacultyLeader.objects.create(name=name, designation=designation)
                if request.FILES.get("image"):
                    leader.image = request.FILES["image"]
                    leader.save()
                messages.success(request, "Leader added!")
        return redirect("edit_leaders")
    return render(request, "edit_leaders.html", {"leaders": leaders})

@login_required
def edit_table(request):
    members = FacultyMember.objects.all()
    if request.method == "POST":
        form_type = request.POST.get("form_type", "")
        if form_type == "delete_member":
            mid = request.POST.get("member_id")
            member = FacultyMember.objects.filter(id=mid).first()
            if member: member.delete(); messages.success(request, "Member deleted.")
            return redirect("edit_table")
        member_id = request.POST.get("member_id")
        name = request.POST.get("name", "").strip()
        designation = request.POST.get("designation", "").strip()
        department = request.POST.get("department", "").strip()
        if member_id:
            m = FacultyMember.objects.filter(id=member_id).first()
            if m and name:
                m.name = name; m.designation = designation; m.department = department; m.save()
                messages.success(request, "Member updated!")
        else:
            if name:
                FacultyMember.objects.create(name=name, designation=designation, department=department)
                messages.success(request, "Member added!")
        return redirect("edit_table")
    return render(request, "edit_table.html", {"members": members})

