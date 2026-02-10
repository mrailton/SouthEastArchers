@extends('layouts.app')

@section('title', 'Edit Event')

@section('content')
<div class="max-w-2xl mx-auto">
    <h1 class="text-4xl font-bold mb-6">Edit Event</h1>
    
    <div class="bg-white p-8 rounded shadow">
        <form method="POST" action="{{ route('admin.events.update', $event) }}" class="space-y-6">
            @csrf
            @method('PUT')
            
            <div>
                <label for="title" class="block text-gray-700 font-bold mb-2">Title *</label>
                <input class="w-full border border-gray-300 rounded px-3 py-2" type="text" id="title" name="title" value="{{ old('title', $event->title) }}" required>
            </div>
            
            <div>
                <label for="description" class="block text-gray-700 font-bold mb-2">Description *</label>
                <textarea class="w-full border border-gray-300 rounded px-3 py-2" id="description" name="description" rows="5" required>{{ old('description', $event->description) }}</textarea>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <label for="start_date" class="block text-gray-700 font-bold mb-2">Start Date *</label>
                    <input class="w-full border border-gray-300 rounded px-3 py-2" type="datetime-local" id="start_date" name="start_date" value="{{ old('start_date', $event->start_date->format('Y-m-d\TH:i')) }}" required>
                </div>
                <div>
                    <label for="end_date" class="block text-gray-700 font-bold mb-2">End Date</label>
                    <input class="w-full border border-gray-300 rounded px-3 py-2" type="datetime-local" id="end_date" name="end_date" value="{{ old('end_date', $event->end_date?->format('Y-m-d\TH:i')) }}">
                </div>
                <div>
                    <label for="location" class="block text-gray-700 font-bold mb-2">Location</label>
                    <input class="w-full border border-gray-300 rounded px-3 py-2" type="text" id="location" name="location" value="{{ old('location', $event->location) }}">
                </div>
                <div>
                    <label for="capacity" class="block text-gray-700 font-bold mb-2">Capacity</label>
                    <input class="w-full border border-gray-300 rounded px-3 py-2" type="number" id="capacity" name="capacity" value="{{ old('capacity', $event->capacity) }}" min="1">
                </div>
            </div>
            
            <div>
                <label class="inline-flex items-center">
                    <input type="checkbox" name="published" value="1" class="rounded border-gray-300" {{ old('published', $event->published) ? 'checked' : '' }}>
                    <span class="ml-2">Published</span>
                </label>
            </div>
            
            <div class="flex gap-4">
                <button type="submit" class="btn-primary py-2 px-6">Update Event</button>
                <a href="{{ route('admin.events.index') }}" class="btn-secondary py-2 px-6">Cancel</a>
            </div>
        </form>
    </div>
</div>
@endsection
