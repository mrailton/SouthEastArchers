@extends('layouts.app')

@section('title', 'Edit ' . $member->name)

@section('content')
<div class="max-w-2xl mx-auto">
    <h1 class="text-4xl font-bold mb-6">Edit {{ $member->name }}</h1>
    
    <div class="bg-white p-8 rounded shadow">
        <form method="POST" action="{{ route('admin.members.update', $member) }}" class="space-y-6">
            @csrf
            @method('PUT')
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <label for="name" class="block text-gray-700 font-bold mb-2">Full Name *</label>
                    <input class="w-full border border-gray-300 rounded px-3 py-2 @error('name') border-red-500 @enderror" 
                           type="text" id="name" name="name" value="{{ old('name', $member->name) }}" required>
                    @error('name')
                        <p class="text-red-500 text-sm mt-1">{{ $message }}</p>
                    @enderror
                </div>
                
                <div>
                    <label for="email" class="block text-gray-700 font-bold mb-2">Email *</label>
                    <input class="w-full border border-gray-300 rounded px-3 py-2 @error('email') border-red-500 @enderror" 
                           type="email" id="email" name="email" value="{{ old('email', $member->email) }}" required>
                    @error('email')
                        <p class="text-red-500 text-sm mt-1">{{ $message }}</p>
                    @enderror
                </div>
                
                <div>
                    <label for="phone" class="block text-gray-700 font-bold mb-2">Phone</label>
                    <input class="w-full border border-gray-300 rounded px-3 py-2 @error('phone') border-red-500 @enderror" 
                           type="tel" id="phone" name="phone" value="{{ old('phone', $member->phone) }}">
                    @error('phone')
                        <p class="text-red-500 text-sm mt-1">{{ $message }}</p>
                    @enderror
                </div>
                
                <div>
                    <label for="qualification" class="block text-gray-700 font-bold mb-2">Qualification *</label>
                    <select class="w-full border border-gray-300 rounded px-3 py-2 @error('qualification') border-red-500 @enderror" 
                            id="qualification" name="qualification" required>
                        <option value="none" {{ old('qualification', $member->qualification) == 'none' ? 'selected' : '' }}>None</option>
                        <option value="beginner" {{ old('qualification', $member->qualification) == 'beginner' ? 'selected' : '' }}>Beginner Course Completed</option>
                        <option value="ai" {{ old('qualification', $member->qualification) == 'ai' ? 'selected' : '' }}>Archery Ireland Member</option>
                        <option value="ifaf" {{ old('qualification', $member->qualification) == 'ifaf' ? 'selected' : '' }}>Irish Field Archery Federation Member</option>
                    </select>
                    @error('qualification')
                        <p class="text-red-500 text-sm mt-1">{{ $message }}</p>
                    @enderror
                </div>
            </div>
            
            <div>
                <label class="inline-flex items-center">
                    <input type="checkbox" name="is_active" value="1" class="rounded border-gray-300" {{ old('is_active', $member->is_active) ? 'checked' : '' }}>
                    <span class="ml-2">Account active</span>
                </label>
            </div>
            
            <div>
                <label class="block text-gray-700 font-bold mb-2">Roles</label>
                <div class="space-y-2">
                    @foreach($roles as $role)
                    <label class="inline-flex items-center mr-4">
                        <input type="checkbox" name="roles[]" value="{{ $role->name }}" class="rounded border-gray-300" 
                               {{ in_array($role->name, old('roles', $member->roles->pluck('name')->toArray())) ? 'checked' : '' }}>
                        <span class="ml-2">{{ $role->name }}</span>
                    </label>
                    @endforeach
                </div>
            </div>
            
            <div class="flex gap-4">
                <button type="submit" class="btn-primary py-2 px-6">
                    Update Member
                </button>
                <a href="{{ route('admin.members.show', $member) }}" class="btn-secondary py-2 px-6">
                    Cancel
                </a>
            </div>
        </form>
    </div>
</div>
@endsection
