from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
import os

class UserManager(BaseUserManager):
    def create_user(self, name, password=None):
        if not name:
            raise ValueError("Users must have a name")
        user = self.model(name=name)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, name, password=None):
        user = self.create_user(name, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    name = models.CharField(max_length=150, unique=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    class Meta:
        verbose_name = "user-info"
        verbose_name_plural = "users-info"

    USERNAME_FIELD = "name"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.name

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

class AboutSection(models.Model):
    SECTION_CHOICES = [
        ("history", "History"),
        ("vision", "Vision"),
        ("mission", "Mission"),
        ("goal", "Goal"),
    ]

    section = models.CharField(
        max_length=20,
        choices=SECTION_CHOICES,
        unique=True,
        help_text="Which section this content belongs to"
    )

    text = models.TextField(
        help_text="The main body text / paragraphs"
    )

    class Meta:
        verbose_name = "about-section"
        verbose_name_plural = "about-sections"

class Messages(models.Model):
    person_name = models.CharField(max_length=100, blank=True)
    person_position = models.CharField(max_length=100, blank=True)
    message_title = models.TextField(
        help_text="The title"
    )
    message_body = models.TextField(
        help_text="The body"
    )
    person_image = models.ImageField(
        upload_to="message/",
        blank=True,
        null=True,
        help_text="Optional image for this section"
    )

class Academic(models.Model):
    SCHOOL_CHOICES = [
        ("primary", "Primary School"),
        ("secondary", "Secondary School"),
    ]

    school = models.CharField(
        max_length=20,
        choices=SCHOOL_CHOICES,
        help_text="Primary or Secondary"
    )

    description = models.TextField(
        help_text="Main description about this school level"
    )

    image = models.ImageField(
        upload_to="academics/",
        blank=True,
        null=True,
        help_text="Image for this section"
    )

    quote = models.TextField(
        blank=True,
        help_text="Optional quote"
    )

    teacher_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="Name of the teacher/head"
    )

    teacher_designation = models.CharField(
        max_length=150,
        blank=True,
        help_text="Designation of the teacher (e.g. Head of Primary)"
    )

    class Meta:
        verbose_name = "academic-section"
        verbose_name_plural = "academic-sections"
        ordering = ["school"]

    def __str__(self):
        return self.get_school_display()


class ContactInfo(models.Model):

    logo = models.ImageField(
        upload_to="logo/",
        blank=True,
        null=True,
        help_text="logo image"
    )

    telephone = models.TextField(
        help_text="You can add multiple numbers. Separate them with a comma or new line."
    )

    email = models.EmailField(
        help_text="Main contact email address"
    )

    facebook_link = models.URLField(
        blank=True,
        null=True,
        help_text="Full Facebook page URL"
    )

    class Meta:
        verbose_name = "contact-info"
        verbose_name_plural = "contact-infos"

    def __str__(self):
        return "School Contact Information"

    def get_telephone_list(self):
        if not self.telephone:
            return []
        numbers = self.telephone.replace(",", "\n").splitlines()
        return [num.strip() for num in numbers if num.strip()]

class Topper(models.Model):
    name = models.CharField(max_length=150)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    image = models.ImageField(upload_to="toppers/", blank=True, null=True)

    class Meta:
        ordering = ["-score"]
        verbose_name = "topper"
        verbose_name_plural = "toppers"

    def __str__(self):
        return f"{self.name} - {self.score}"

class GalleryEvent(models.Model):
    event_name = models.CharField(max_length=200)
    event_date = models.CharField()
    first_name = models.CharField(default=event_name)

    class Meta:
        ordering = ["-id"]
        verbose_name = "gallery-event"
        verbose_name_plural = "gallery-events"

    def __str__(self):
        return f"{self.event_name} ({self.event_date})"

    def delete(self, *args, **kwargs):
        for image in list(self.images.all()):
            image.delete()
        return super().delete(*args, **kwargs)

def gallery_image_upload_path(instance, filename):
    name = (instance.event.event_name or "unnamed").strip().replace(" ", "_").replace("/", "")
    return os.path.join("gallery", name, filename)

class GalleryImage(models.Model):
    event = models.ForeignKey(
        GalleryEvent,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to=gallery_image_upload_path)

    def delete(self, *args, **kwargs):
        if self.image:
            self.image.delete(save=False)
        return super().delete(*args, **kwargs)

    class Meta:
        ordering = ["id"]
        verbose_name = "gallery-image"
        verbose_name_plural = "gallery-images"

    def __str__(self):
        return f"Image for {self.event.event_name}"

class MonthInfo(models.Model):
    MONTH_CHOICES = [
        (1, "Baishakh"),
        (2, "Jestha"),
        (3, "Ashadh"),
        (4, "Shrawan"),
        (5, "Bhadra"),
        (6, "Ashwin"),
        (7, "Kartik"),
        (8, "Mangsir"),
        (9, "Poush"),
        (10, "Magh"),
        (11, "Falgun"),
        (12, "Chaitra"),
    ]

    DAYS_CHOICES = [
        (28, "28"),
        (29, "29"),
        (30, "30"),
        (31, "31"),
        (32, "32"),
    ]

    START_DAY_CHOICES = [
        (1, "Sunday"),
        (2, "Monday"),
        (3, "Tuesday"),
        (4, "Wednesday"),
        (5, "Thursday"),
        (6, "Friday"),
        (7, "Saturday"),
    ]

    month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES, unique=True)
    month_days = models.PositiveSmallIntegerField(choices=DAYS_CHOICES, null=True, blank=True)
    month_start_day = models.PositiveSmallIntegerField(choices=START_DAY_CHOICES, null=True, blank=True)

    class Meta:
        ordering = ["month"]
        verbose_name = "month-info"
        verbose_name_plural = "months-info"

    def __str__(self):
        return self.get_month_display()

class MonthEvent(models.Model):
    month = models.ForeignKey(MonthInfo, on_delete=models.CASCADE, related_name="events")
    event_date = models.PositiveSmallIntegerField()
    event_name = models.CharField(max_length=200)
    event_type = models.CharField(
        max_length=20,
        choices=[("event", "School Event"), ("holiday", "Holiday / Closure")],
        default="event"
    )

    class Meta:
        ordering = ["event_date"]
        verbose_name = "month-event-info"
        verbose_name_plural = "months-event-info"

    def __str__(self):
        return f"{self.event_date} - {self.event_name}"

class Notice(models.Model):
    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("ne", "Nepali"),
    ]
    language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default="en",
        help_text="Language the notice title, date and body are written in.",
    )
    title = models.CharField(max_length=255)
    date = models.CharField(
        max_length=100,
        help_text="Free-form date, e.g. Baisakh 20, 2083 OR 23 Baisakh, 2083",
    )
    body = models.TextField()

    class Meta:
        ordering = ["-id"]
        verbose_name = "notice"
        verbose_name_plural = "notices"

import os
def notice_image_path(instance, filename):
    return os.path.join("notices", str(instance.notice.id), filename)

class NoticeImage(models.Model):
    notice = models.ForeignKey(
        Notice, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to=notice_image_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.title} ({self.date})"

class HomePage(models.Model):
    SECTION_CHOICES = [
        ("text", "Text"),
        ("image", "Image"),
    ]
    section = models.CharField(
        max_length=20,
        choices=SECTION_CHOICES,
        help_text="Which section this content belongs to"
    )
    welcome_message = models.TextField(
        help_text="The text for homepage"
    )
    home_image=models.ImageField(
        upload_to="homepage/",
        blank=True,
        null=True,
        help_text="Image for the homepage"
    )

class FacultyLeader(models.Model):
    name = models.CharField(max_length=150)
    designation = models.CharField(max_length=150, blank=True)
    image = models.ImageField(upload_to="faculty/", blank=True, null=True)

    class Meta:
        verbose_name = "faculty-leader"
        verbose_name_plural = "faculty-leaders"
        ordering = ["name"]

    def __str__(self):
        return self.name

class FacultyMember(models.Model):
    name = models.CharField(max_length=150)
    designation = models.CharField(max_length=150, blank=True)
    department = models.CharField(max_length=150, blank=True)

    class Meta:
        verbose_name = "faculty-member"
        verbose_name_plural = "faculty-members"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} — {self.designation or 'Teacher'}"

class SEEResults(models.Model):
    year = models.IntegerField(default=0)
    candidate_count = models.PositiveIntegerField(default=0)
    pass_rate = models.FloatField(default=0.0)
    average_gpa = models.FloatField(default=0.0)

    class Meta:
        verbose_name = "SEE Results"
