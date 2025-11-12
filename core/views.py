from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from news.models import News
from events.models import Event


def index(request):
    """Homepage with latest news and upcoming events"""
    latest_news = News.objects.filter(published=True).order_by('-created_at')[:3]
    upcoming_events = Event.objects.filter(
        published=True,
        event_date__gte=timezone.now()
    ).order_by('event_date')[:3]

    context = {
        'news': latest_news,
        'events': upcoming_events,
    }
    return render(request, 'core/index.html', context)


def about(request):
    """About page"""
    return render(request, 'core/about.html')


def news_list(request):
    """List all published news articles"""
    news = News.objects.filter(published=True).order_by('-created_at')
    context = {'news': news}
    return render(request, 'core/news_list.html', context)


def news_detail(request, pk):
    """Display a single news article"""
    news = get_object_or_404(News, pk=pk, published=True)
    context = {'news': news}
    return render(request, 'core/news_detail.html', context)


def events_list(request):
    """List all upcoming published events"""
    events = Event.objects.filter(
        published=True,
        event_date__gte=timezone.now()
    ).order_by('event_date')
    context = {'events': events}
    return render(request, 'core/events_list.html', context)


def event_detail(request, pk):
    """Display a single event"""
    event = get_object_or_404(Event, pk=pk, published=True)
    context = {'event': event}
    return render(request, 'core/event_detail.html', context)


@login_required
def dashboard(request):
    """Member dashboard"""
    membership = request.user.memberships.filter(is_active=True).first()
    context = {'membership': membership}
    return render(request, 'core/dashboard.html', context)
