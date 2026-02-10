@extends('layouts.app')

@section('title', 'Profile')

@section('content')
<div class="max-w-2xl mx-auto">
    <h1 class="text-4xl font-bold mb-6">Your Profile</h1>
    
    <div class="bg-white p-8 rounded shadow">
        <form method="POST" action="{{ route('profile.update') }}" class="space-y-6">
            @csrf
            @method('PUT')
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <label for="name" class="block text-gray-700 font-bold mb-2">Name</label>
                    <input class="w-full border border-gray-300 rounded px-3 py-2 @error('name') border-red-500 @enderror" 
                           type="text" id="name" name="name" value="{{ old('name', $user->name) }}" required>
                    @error('name')
                        <p class="text-red-500 text-sm mt-1">{{ $message }}</p>
                    @enderror
                </div>
                
                <div>
                    <label for="email" class="block text-gray-700 font-bold mb-2">Email</label>
                    <input class="w-full border border-gray-300 rounded px-3 py-2 bg-gray-100" 
                           type="email" id="email" value="{{ $user->email }}" disabled>
                </div>
                
                <div>
                    <label for="phone" class="block text-gray-700 font-bold mb-2">Phone</label>
                    <input class="w-full border border-gray-300 rounded px-3 py-2 @error('phone') border-red-500 @enderror" 
                           type="tel" id="phone" name="phone" value="{{ old('phone', $user->phone) }}">
                    @error('phone')
                        <p class="text-red-500 text-sm mt-1">{{ $message }}</p>
                    @enderror
                </div>
            </div>
            
            <button type="submit" class="btn-primary py-2 px-6">
                Update Profile
            </button>
        </form>
        
        <hr class="my-8">
        
        <div>
            <a href="{{ route('change-password') }}" class="text-blue-600 hover:underline">Change your password</a>
        </div>
    </div>
</div>
@endsection
