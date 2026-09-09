from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from django.contrib.auth import views as auth_views
# Inside your urlpatterns in urls.py:
# path('logout/', LogoutView.as_view(), name='logout'),
urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("signin/", views.signin, name="signin"),
    path("signout/", views.signout, name="signout"),
    path("", views.home, name="home"),
    path(
        "agent/dashboard/",
        views.agent_dashboard,
        name="agent_dashboard"
    ),

    path(
        "agent/add-property/",
        views.add_property,
        name="add_property"),
    path('home/', views.home_view, name='homes'),
    path('properties/', views.property_list_view, name='property_list'),
    path('search/', views.search_hub_view, name='search_hub'),
    path('property/<int:pk>/', views.property_detail, name='property_detail'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('term/', views.terms_view, name='term'),
    path('privacy/', views.privacy_view, name='privacy'),

    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('property/<int:pk>/toggle-status/', views.toggle_property_status, name='toggle_property_status'),
    path('property/<int:pk>/delete/', views.delete_property, name='delete_property'),
    path('password-reset/',
         auth_views.PasswordResetView.as_view(template_name='password_reset.html'),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),
         name='password_reset_confirm'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),
         name='password_reset_complete'),
]