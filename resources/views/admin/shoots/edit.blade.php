@extends('layouts.app')

@section('title', 'Edit Shoot')

@section('content')
<div class="max-w-2xl mx-auto">
    <h1 class="text-4xl font-bold mb-6">Edit Shoot</h1>
    
    <div class="bg-white p-8 rounded shadow">
        <form method="POST" action="{{ route('admin.shoots.update', $shoot) }}" class="space-y-6">
            @csrf
            @method('PUT')
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <label for="date" class="block text-gray-700 font-bold mb-2">Date *</label>
                    <input class="w-full border border-gray-300 rounded px-3 py-2 @error('date') border-red-500 @enderror" 
                           type="date" id="date" name="date" value="{{ old('date', $shoot->date->format('Y-m-d')) }}" required>
                    @error('date')
                        <p class="text-red-500 text-sm mt-1">{{ $message }}</p>
                    @enderror
                </div>
                
                <div>
                    <label for="location" class="block text-gray-700 font-bold mb-2">Location *</label>
                    <select class="w-full border border-gray-300 rounded px-3 py-2 @error('location') border-red-500 @enderror" 
                            id="location" name="location" required>
                        @foreach($locations as $location)
                        <option value="{{ $location->value }}" {{ old('location', $shoot->location->value) == $location->value ? 'selected' : '' }}>
                            {{ $location->value }}
                        </option>
                        @endforeach
                    </select>
                    @error('location')
                        <p class="text-red-500 text-sm mt-1">{{ $message }}</p>
                    @enderror
                </div>
            </div>
            
            <div>
                <label for="description" class="block text-gray-700 font-bold mb-2">Description</label>
                <textarea class="w-full border border-gray-300 rounded px-3 py-2 @error('description') border-red-500 @enderror" 
                          id="description" name="description" rows="3">{{ old('description', $shoot->description) }}</textarea>
                @error('description')
                    <p class="text-red-500 text-sm mt-1">{{ $message }}</p>
                @enderror
            </div>
            
            <div>
                <label class="block text-gray-700 font-bold mb-2">Attendees</label>
                <p class="text-sm text-gray-500 mb-2">Credits will be adjusted when changing attendees.</p>
                <div class="max-h-60 overflow-y-auto border rounded p-3 space-y-2">
                    @foreach($members as $member)
                    <label class="flex items-center">
                        <input type="checkbox" name="attendees[]" value="{{ $member->id }}" class="rounded border-gray-300"
                               {{ in_array($member->id, old('attendees', $shoot->users->pluck('id')->toArray())) ? 'checked' : '' }}>
                        <span class="ml-2">{{ $member->name }}</span>
                        @if($member->membership)
                        <span class="ml-2 text-sm text-gray-500">({{ $member->membership->creditsRemaining() }} credits)</span>
                        @endif
                    </label>
                    @endforeach
                </div>
            </div>
            
            <div class="flex gap-4">
                <button type="submit" class="btn-primary py-2 px-6">Update Shoot</button>
                <a href="{{ route('admin.shoots.index') }}" class="btn-secondary py-2 px-6">Cancel</a>
            </div>
        </form>
    </div>
</div>
@endsection
