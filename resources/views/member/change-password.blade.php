@extends('layouts.app')

@section('title', 'Change Password')

@section('content')
<div class="max-w-md mx-auto">
    <h1 class="text-4xl font-bold mb-6">Change Password</h1>
    
    <div class="bg-white p-8 rounded shadow">
        <form method="POST" action="{{ route('change-password.update') }}" class="space-y-6">
            @csrf
            @method('PUT')
            
            <div>
                <label for="current_password" class="block text-gray-700 font-bold mb-2">Current Password</label>
                <input class="w-full border border-gray-300 rounded px-3 py-2 @error('current_password') border-red-500 @enderror" 
                       type="password" id="current_password" name="current_password" required>
                @error('current_password')
                    <p class="text-red-500 text-sm mt-1">{{ $message }}</p>
                @enderror
            </div>
            
            <div>
                <label for="password" class="block text-gray-700 font-bold mb-2">New Password</label>
                <input class="w-full border border-gray-300 rounded px-3 py-2 @error('password') border-red-500 @enderror" 
                       type="password" id="password" name="password" required>
                @error('password')
                    <p class="text-red-500 text-sm mt-1">{{ $message }}</p>
                @enderror
            </div>
            
            <div>
                <label for="password_confirmation" class="block text-gray-700 font-bold mb-2">Confirm New Password</label>
                <input class="w-full border border-gray-300 rounded px-3 py-2" 
                       type="password" id="password_confirmation" name="password_confirmation" required>
            </div>
            
            <button type="submit" class="btn-primary py-2 px-6">
                Change Password
            </button>
        </form>
        
        <div class="mt-6">
            <a href="{{ route('profile') }}" class="text-blue-600 hover:underline">&larr; Back to Profile</a>
        </div>
    </div>
</div>
@endsection
