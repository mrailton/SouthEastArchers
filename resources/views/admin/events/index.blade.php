@extends('layouts.app')

@section('title', 'Events')

@section('content')
<div class="max-w-6xl mx-auto">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold">Events</h1>
        @can('events.create')
        <a href="{{ route('admin.events.create') }}" class="btn-primary px-4 py-2">Create Event</a>
        @endcan
    </div>
    
    @if($events->count() > 0)
    <div class="bg-white shadow overflow-hidden sm:rounded-md">
        <ul class="divide-y divide-gray-200">
            @foreach($events as $event)
            <li class="px-6 py-4 hover:bg-gray-50">
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        <h3 class="text-lg font-medium text-gray-900">{{ $event->title }}</h3>
                        <p class="mt-1 text-sm text-gray-600">{{ $event->start_date->format('d M Y, H:i') }}</p>
                        @if($event->location)
                        <p class="mt-1 text-sm text-gray-500">Location: {{ $event->location }}</p>
                        @endif
                        <span class="badge {{ $event->published ? 'badge-success' : 'badge-warning' }}">
                            {{ $event->published ? 'Published' : 'Draft' }}
                        </span>
                    </div>
                    @can('events.update')
                    <a href="{{ route('admin.events.edit', $event) }}" class="btn-secondary px-3 py-2">Edit</a>
                    @endcan
                </div>
            </li>
            @endforeach
        </ul>
    </div>
    <div class="mt-6">{{ $events->links() }}</div>
    @else
    <p class="text-gray-600">No events yet.</p>
    @endif
</div>
@endsection
