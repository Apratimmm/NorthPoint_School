from django.urls import path
from .views import *
from logic.views import *

urlpatterns = [
    path('', home, name='home'),
    path('about_us/', about_us, name='about_us'),
    path('login/', user_login, name='login'),
    path('verify_user/',verify_user, name='verify_user'),
    path('gallery/', gallery, name='gallery'),
    path('calendar/', calendar, name='calendar'),
    path('notices/', notices, name='notices'),
    path('results/', results, name='results'),
    path('contact/', contact, name='contact'),
    path('academics/', academics, name='academics'),
    path('faculty',faculty, name='faculty'),
    path('dashboard/', dashboard, name='dashboard'),
    path('logout/', user_logout, name='logout'),
    path('edit_contact/', edit_contact, name='edit_contact'),
    path('edit_academics/', edit_academics, name='edit_academics'),
    path('show_events/', show_events, name='show_events'),
    path('add_event/', add_event, name='add_event'),
    path('edit_event/<int:event_id>/', edit_event, name='edit_event'),
    path('delete_event/<int:event_id>/', delete_event, name='delete_event'),
    path('show_notices/', show_notices, name='show_notices'),
    path('add_notice/', add_notice, name='add_notice'),
    path('edit_notice/<int:notice_id>/', edit_notice, name='edit_notice'),
    path('delete_notice/<int:notice_id>/', delete_notice, name='delete_notice'),
    # path('month_data/<int:month_id>/', month_data, name='month_data'),
    # path('contact/', contact, name='contact'),
    # path('committee/', committee, name='committee'),

    # path('edit_school_video/', edit_school_video, name='edit_school_video'),
    # path('edit_about/', edit_about, name='edit_about'),

    # path('send_email/', send_email, name='send_mail'),

    # path('edit_results/', edit_results, name='edit_results'),

    # path('edit_calender/', show_calenders, name='show_calenders'),
    # path('show_calender/<int:month_id>', show_calender, name='show_calender'),
    # path('update_month/', update_month, name='update_month'),
    # path('show_committees/', show_committees, name='show_committees'),
    # path('add_committee/', add_committee, name='add_committee'),
    # path('add_committee_people/<int:committee_id>/', add_committee_people, name='add_committee_people'),
    # path('delete_committee_people/<int:person_id>/', delete_committee_people, name='delete_committee_people'),
    # path('delete_committee/<int:committee_id>/', delete_committee, name='delete_committee'),


    # path('edit_signature/', edit_signature, name='edit_signature'),
    # path('view_notice/<int:notice_id>/', view_notice, name='view_notice'),

]
