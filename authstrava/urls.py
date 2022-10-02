from django.urls import path
from . import views

app_name = "authstrava"

urlpatterns = [
  #'hard way'
  #path("", views.index, name="index"),
  #path("<int:question_id>/", views.detail, name="detail"),
  #path("<int:question_id>/results/", views.results, name="results"),
  #path("<int:question_id>/vote/", views.vote, name="vote"),
  #path("specifics/<int:questin_id>/", views.detail, name="detail"),

  #'generic views' way
  path("", views.IndexView.as_view(), name="index"),
  #path("map/", views.FoliumView.as_view(), name="map"),
  #path("<int:pk>/", views.DetailView.as_view(), name="detail"),
  #path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
  #path("<int:question_id>/vote/", views.vote, name="vote"),
]
