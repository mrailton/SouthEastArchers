@extends('layouts.app')

@section('title', 'Events')

@section('content')
<h1 class="text-4xl font-bold mb-6">Upcoming Events</h1>

@if($events->count() > 0)
    <div class="space-y-4">
        @foreach($events as $event)
            <div class="bg-white p-4 rounded shadow">
                <h2 class="text-2xl font-bold">{{ $event->title }}</h2>
                <p class="text-gray-600 text-sm">{{ $event->start_date->format('Y-m-d H:i') }}</p>
                @if($event->location)
                    <p class="text-gray-600">Location: {{ $event->location }}</p>
                @endif
                <p class="text-gray-700">{{ Str::limit($event->description, 200) }}</p>
            </div>
        @endforeach
    </div>

    <div class="mt-6">
        {{ $events->links() }}
    </div>
@else
    <p class="text-gray-700">No upcoming events.</p>
@endif
@endsection
