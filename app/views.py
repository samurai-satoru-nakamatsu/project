from django.core.cache import cache
from django.shortcuts import render, redirect
from django.urls import resolve
import googleapiclient.discovery
import pandas as pd
import tweepy

from app.youtube.auth import get_google_auth_url, get_google_auth_credentials, get_google_credentials, credentials_to_dict
from app.youtube.upload_video import initialize_upload
from .models import Video
from .forms import VideoForm

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
            search = youtube.search().list(part='snippet', forMine=True, type='video', maxResults=50).execute()
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
    template_name = 'app/youtube/analytics_api.html'
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

    return render(request, template_name, {'analytics': analytics})

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
        consumer_key = 'r6j3Xyz90agVA4gLrqoJ6erqB'  # API Key
        consumer_secret = 'kCwK8wKtXrQZyxCUs17B0j8WizLLoS0i8z2rK9Mmvxqo2e2jv0'  # API Key Secret
        access_token = '1461296500366282756-SIxQmC3tg0qJBtIkJAlMuoTvcswnsB'
        access_token_secret = '5lGzcDHl3mgWPe7dEHWofLzS5NaTunmQWZrzzmsuVa8oQ'
        bearer_token ='AAAAAAAAAAAAAAAAAAAAAP5fWAEAAAAABC7EwjesfHpc3chubDcCcQ2n8dQ%3DdWfJT96Es2TNQ11ov7wiex43uBD41JNepdjqetQ4YTm9eOeYwS'
        client = tweepy.Client(bearer_token=bearer_token, consumer_key=consumer_key, consumer_secret=consumer_secret, access_token=access_token, access_token_secret=access_token_secret)
        client.create_tweet(text=request.POST['tweet'])
        return redirect('.')
    return render(request, 'app/twitter/index.html')
