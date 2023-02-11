from django.urls import path
from django.views.generic import TemplateView
from .views import (
    showvideo, youtube_data_api, youtube_data_api_auth, youtube_data_api_oauth2_callback,
    youtube_analytics_api, recommend_view, openlayers_view, leaflet_view, twitter_view
)

urlpatterns = [
    path('', TemplateView.as_view(template_name='app/index.html'), name='top'),
    path('videos/', showvideo, name='videos'),
    path('youtube-data-api/', youtube_data_api, name='youtube_data_api'),
    path('youtube-data-api/channels/', youtube_data_api, name='youtube_data_api_channels'),
    path('youtube-data-api/playlists/', youtube_data_api, name='youtube_data_api_playlists'),
    path('youtube-data-api/video-categories/', youtube_data_api, name='youtube_data_api_video_categories'),
    path('youtube-data-api/videos/', youtube_data_api, name='youtube_data_api_videos'),
    path('youtube-data-api/search/', youtube_data_api, name='youtube_data_api_search'),
    path('youtube-data-api/thumbnails/', youtube_data_api, name='youtube_data_api_thumbnails'),
    path('youtube-data-api/captions/', youtube_data_api, name='youtube_data_api_captions'),
    path('youtube-analytics-api/', youtube_analytics_api, name='youtube_analytics_api'),
    path('youtube-data-api/auth/', youtube_data_api_auth, name='youtube_data_api_auth'),
    path('youtube-data-api/oauth2callback/', youtube_data_api_oauth2_callback, name='youtube_data_api_oauth2_callback'),
    path('recommend/', recommend_view, name='recommend'),
    path('openlayers/', openlayers_view, name='openlayers'),
    path('leaflet/', leaflet_view, name='leaflet'),
    path('twitter/', twitter_view, name='twitter'),
]