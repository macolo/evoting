from django.urls import path
from . import views

app_name = 'ballot'

urlpatterns = [
    path('vote/<str:token>/', views.vote_view, name='vote'),
    path('vote/<str:token>/submit/', views.submit_vote, name='submit_vote'),
    path('vote-closed/', views.vote_closed, name='vote_closed'),
    path('already-voted/', views.already_voted, name='already_voted'),
    path('vote-success/<int:voting_event_id>/', views.vote_success, name='vote_success'),
]
