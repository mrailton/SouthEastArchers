@extends('layouts.app')

@section('title', 'Create Member')

@section('content')
<div class="max-w-2xl mx-auto">
    <h1 class="text-4xl font-bold mb-6">Create Member</h1>
    
    <div class="bg-white p-8 rounded shadow">
        <form method="POST" action="{{ route('admin.members.store') }}" class="space-y-6">
            @csrf
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <label for="name" class="block text-gray-700 font-bold mb-2">Full Name *</label>
                    <input class="w-full border border-gray-300 rounded px-3 py-2 @error('name') border-red-500 @enderror" 
                           type="text" id="name" name="name" value="{{ old('name') }}" required>
                    @error('name')
                        <p class="text-red-500 text-sm mt-1">{{ $message }}</p>
                    @enderror
                </div>
                
                <div>
                    <label for="email" class="block text-gray-700 font-bold mb-2">Email *</label>
                    <input class="w-full border border-gray-300 rounded px-3 py-2 @error('email') border-red-500 @enderror" 
                           type="email" id="email" name="email" value="{{ old('email') }}" required>
                    @error('email')
                        <p class="text-red-500 text-sm mt-1">{{ $message }}</p>
                    @enderror
                </div>
                
                <div>
                    <label for="phone" class="block text-gray-700 font-bold mb-2">Phone</label>
                    <input class="w-full border border-gray-300 rounded px-3 py-2 @error('phone') border-red-500 @enderror" 
                           type="tel" id="phone" name="phone" value="{{ old('phone') }}">
                    @error('phone')
                        <p class="text-red-500 text-sm mt-1">{{ $message }}</p>
                    @enderror
                </div>
                
                <div>
                    <label for="qualification" class="block text-gray-700 font-bold mb-2">Qualification *</label>
                    <select class="w-full border border-gray-300 rounded px-3 py-2 @error('qualification') border-red-500 @enderror" 
                            id="qualification" name="qualification" required>
                        <option value="none" {{ old('qualification') == 'none' ? 'selected' : '' }}>None</option>
                        <option value="beginner" {{ old('qualification') == 'beginner' ? 'selected' : '' }}>Beginner Course Completed</option>
                        <option value="ai" {{ old('qualification') == 'ai' ? 'selected' : '' }}>Archery Ireland Member</option>
                        <option value="ifaf" {{ old('qualification') == 'ifaf' ? 'selected' : '' }}>Irish Field Archery Federation Member</option>
                    </select>
                    @error('qualification')
                        <p class="text-red-500 text-sm mt-1">{{ $message }}</p>
                    @enderror
                </div>
                
                <div>
                    <label for="password" class="block text-gray-700 font-bold mb-2">Password *</label>
                    <input class="w-full border border-gray-300 rounded px-3 py-2 @error('password') border-red-500 @enderror" 
                           type="password" id="password" name="password" required>
                    @error('password')
                        <p class="text-red-500 text-sm mt-1">{{ $message }}</p>
                    @enderror
                </div>
                
                <div>
                    <label for="password_confirmation" class="block text-gray-700 font-bold mb-2">Confirm Password *</label>
                    <input class="w-full border border-gray-300 rounded px-3 py-2" 
                           type="password" id="password_confirmation" name="password_confirmation" required>
                </div>
            </div>
            
            <div>
                <label class="inline-flex items-center">
                    <input type="checkbox" name="is_active" value="1" class="rounded border-gray-300" {{ old('is_active') ? 'checked' : '' }}>
                    <span class="ml-2">Activate account immediately</span>
                </label>
            </div>
            
            <div>
                <label class="block text-gray-700 font-bold mb-2">Roles</label>
                <div class="space-y-2">
                    @foreach($roles as $role)
                    <label class="inline-flex items-center mr-4">
                        <input type="checkbox" name="roles[]" value="{{ $role->name }}" class="rounded border-gray-300" 
                               {{ in_array($role->name, old('roles', [])) ? 'checked' : '' }}>
                        <span class="ml-2">{{ $role->name }}</span>
                    </label>
                    @endforeach
                </div>
            </div>
            
            <div class="flex gap-4">
                <button type="submit" class="btn-primary py-2 px-6">
                    Create Member
                </button>
                <a href="{{ route('admin.members.index') }}" class="btn-secondary py-2 px-6">
                    Cancel
                </a>
            </div>
        </form>
    </div>
</div>
@endsection
