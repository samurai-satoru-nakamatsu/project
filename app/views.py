from distutils.util import strtobool
from django.core.cache import cache
from django.shortcuts import render, redirect
from django.urls import resolve
import googleapiclient.discovery
import pandas as pd
import tweepy
import pprint
import os
from formtools.wizard.views import SessionWizardView
from django.conf import settings
from django.core.files.storage import FileSystemStorage

from app.youtube.auth import get_google_auth_url, get_google_auth_credentials, get_google_credentials, credentials_to_dict
from app.youtube.upload_video import initialize_upload
from .models import Video
from .forms import ContactForm1, ContactForm2, VideoForm
from .graph.graph import google_analytics_graph

def showvideo(request):
    form= VideoForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()

    videos = Video.objects.all().order_by('-created_at')
    context= {
        'videos': videos,
        'form': form
    }
    return render(request, 'app/videos.html', context)


def youtube_data_api(request):
    if not request.session.get('credentials'):
        return redirect('youtube_data_api_auth')

    API_SERVICE_NAME = 'youtube'
    API_VERSION = 'v3'

    credentials = get_google_credentials(request.session.get('credentials'))
    youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
    request.session['credentials'] = credentials_to_dict(credentials)

    template_name = ''
    context = {}
    if resolve(request.path).url_name == 'youtube_data_api':
        template_name = 'app/youtube/index.html'
        context['credentials'] = credentials
        if request.method == 'POST':
            del request.session['credentials']
            return redirect('.')
    elif resolve(request.path).url_name == 'youtube_data_api_channels':
        channels = youtube.channels().list(mine=True, part='snippet').execute()
        template_name = 'app/youtube/channels.html'
        context['channels'] = channels
    elif resolve(request.path).url_name == 'youtube_data_api_video_categories':
        video_categories = youtube.videoCategories().list(part='snippet', hl='ja', regionCode='jp').execute()
        template_name =  'app/youtube/video_categories.html'
        context['video_categories'] = video_categories
    elif resolve(request.path).url_name == 'youtube_data_api_videos':
        template_name = 'app/youtube/videos.html'
        if request.method == 'POST':
            options = type('', (object,), {
                'keywords': request.POST.get('keywords'),
                'title': request.POST.get('title'),
                'description': request.POST.get('description'),
                'category': request.POST.get('category'),
                'privacyStatus': request.POST.get('privacyStatus'),
                'madeForKids': strtobool(request.POST.get('madeForKids')),
                'file': request.FILES.get('file').temporary_file_path()
            })
            initialize_upload(youtube, options)

        video_categories = youtube.videoCategories().list(part='snippet', hl='ja', regionCode='jp').execute()
        context['video_categories'] = video_categories
                    
    elif resolve(request.path).url_name == 'youtube_data_api_playlists':
        template_name = 'app/youtube/playlists.html'
        playlists = cache.get('youtube_data_api_playlists')
        if not playlists:
            playlists = youtube.playlists().list(mine=True, part='snippet', maxResults=50).execute()
            cache.set('youtube_data_api_playlists', playlists)
        context['playlists'] = playlists
    elif resolve(request.path).url_name == 'youtube_data_api_search':
        template_name = 'app/youtube/search.html'
        search = cache.get('youtube_data_api_search')
        if not search:
            search = youtube.search().list(part='id,snippet', forMine=True, type='video', maxResults=50).execute()
            cache.set('youtube_data_api_search', search)
        context['search'] = search
    elif resolve(request.path).url_name == 'youtube_data_api_thumbnails':
        template_name = 'app/youtube/thumbnails.html'

        if request.method == 'POST':
            youtube.thumbnails().set(
                videoId=request.POST.get('video_id'),
                media_body=request.FILES.get('file').temporary_file_path(),
            ).execute()
            cache.delete('youtube_data_api_search')

        search = cache.get('youtube_data_api_search')
        if not search:
            search = youtube.search().list(part='snippet', forMine=True, type='video', maxResults=50).execute()
            cache.set('youtube_data_api_search', search)
        context['search'] = search
    elif resolve(request.path).url_name == 'youtube_data_api_captions':
        template_name = 'app/youtube/captions.html'

        search = cache.get('youtube_data_api_search')
        if not search:
            search = youtube.search().list(part='snippet', forMine=True, type='video', maxResults=50).execute()
            cache.set('youtube_data_api_search', search)
        context['search'] = search
        
        if request.GET.get('video_id'):
            context['captions'] = youtube.captions().list(part='snippet', videoId=request.GET.get('video_id')).execute()
        
    return render(request, template_name, context)


def youtube_analytics_api(request):
    if not request.session.get('credentials'):
        return redirect('youtube_data_api_auth')

    API_SERVICE_NAME = 'youtubeAnalytics'
    API_VERSION = 'v2'

    credentials = get_google_credentials(request.session.get('credentials'))
    youtube_analytics = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)


    start_date = '2022-01-01'
    end_date = '2022-12-31'
    if request.GET:
        if request.GET.get('start_date'):
            start_date = request.GET.get('start_date')
        if request.GET.get('end_date'):
            end_date = request.GET.get('end_date')

    analytics = youtube_analytics.reports().query(
        ids='channel==MINE',
        startDate=start_date,
        endDate=end_date,
        metrics='estimatedMinutesWatched,views,likes,subscribersGained',
        dimensions='day',
        sort='day'
    ).execute()

    graph = google_analytics_graph(analytics)

    return render(request, 'app/youtube/analytics_api.html', {'analytics': analytics, 'graph': graph})

def youtube_data_api_auth(request):
    google_auth_url, state = get_google_auth_url()
    request.session['state'] = state
    return redirect(google_auth_url)

def youtube_data_api_oauth2_callback(request):
    state = request.session.get('state')
    code = request.GET.get('code', '')
    credentials = get_google_auth_credentials(state, request.build_absolute_uri())
    request.session['credentials'] = credentials
    return redirect('youtube_data_api')


def recommend_view(request):
    links_csv = pd.read_csv('app/MovieLens/ml-latest-small/links.csv')
    return render(request, 'app/recommend/index.html', {'links_csv': links_csv})


def openlayers_view(request):
    return render(request, 'app/openlayers/index.html')


def leaflet_view(request):
    return render(request, 'app/leaflet/index.html')


def twitter_view(request):
    if request.method == 'POST' and request.POST.get('tweet'):
        consumer_key = os.environ.get('TWITTER_CONSUMER_KEY')
        consumer_secret = os.environ.get('TWITTER_CONSUMER_SECRET')
        access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
        access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
        bearer_token =os.environ.get('TWITTER_BEARER_TOKEN')
        client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        client.create_tweet(text=request.POST['tweet'])
        return redirect('.')
    return render(request, 'app/twitter/index.html')


class WizardView(SessionWizardView):
    form_list = [('step1', ContactForm1), ('step2', ContactForm2)]
    template_name = 'app/wizard/wizard_form.html'
    file_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'wizard'))

    def done(self, form_list, **kwargs):
        form_data = [form.cleaned_data for form in form_list]
        print(form_data)
        return redirect('wizard_done')
    
    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form, **kwargs)
        form_step1_files = self.storage.get_step_files('step1')
        context['step1_file'] = form_step1_files['step1-file'] if form_step1_files else None
        return context
    
    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if step == 'step2':
            form_step1_files = self.storage.get_step_files('step1')
            kwargs['step1_file'] = form_step1_files['step1-file'] if form_step1_files else None
        return kwargs

