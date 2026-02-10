@extends('layouts.app')

@section('title', 'Dashboard')

@section('content')
<div class="max-w-4xl mx-auto">
    <h1 class="text-3xl font-bold mb-6">Dashboard</h1>
    
    {{-- Pending Membership Alert --}}
    @if($membership && $membership->status === \App\Enums\MembershipStatus::Pending)
    <div class="mb-6 bg-yellow-50 border-l-4 border-yellow-400 p-4">
        <div class="flex">
            <div class="flex-shrink-0">
                <svg class="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                </svg>
            </div>
            <div class="ml-3">
                <h3 class="text-sm font-medium text-yellow-800">
                    Membership Pending Activation
                </h3>
                <div class="mt-2 text-sm text-yellow-700">
                    <p>
                        Your membership is awaiting payment confirmation. 
                        If you've paid by cash, an administrator will activate your membership once payment is received.
                    </p>
                </div>
            </div>
        </div>
    </div>
    @endif
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {{-- Membership Card --}}
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-semibold mb-4">Membership</h2>
            @if($membership)
            <div class="space-y-2">
                <p><span class="font-medium">Status:</span> 
                    @if($membership->isActive())
                        <span class="badge badge-success">Active</span>
                    @elseif($membership->status === \App\Enums\MembershipStatus::Pending)
                        <span class="badge badge-warning">Pending Payment</span>
                    @else
                        <span class="badge badge-danger">{{ $membership->status->value }}</span>
                    @endif
                </p>
                <p><span class="font-medium">Expires:</span> {{ $membership->expiry_date->format('d M Y') }}</p>
                <p><span class="font-medium">Credits Remaining:</span> 
                    <span class="text-2xl font-bold text-blue-600">{{ $membership->creditsRemaining() }}</span>
                </p>
            </div>
            @else
            <p class="text-gray-600">No active membership</p>
            <a href="{{ route('payment.membership') }}" class="mt-4 inline-block btn-primary px-4 py-2">
                Purchase Membership
            </a>
            @endif
        </div>
        
        {{-- Activity Card --}}
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-semibold mb-4">Activity</h2>
            <div class="space-y-2">
                <p><span class="font-medium">Shoots Attended:</span> 
                    <span class="text-2xl font-bold text-green-600">{{ $shootsAttended }}</span>
                </p>
                <a href="{{ route('shoots') }}" class="block text-blue-600 hover:underline mt-4">
                    View shoot history →
                </a>
            </div>
        </div>
    </div>
    
    {{-- Quick Actions --}}
    <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-xl font-semibold mb-4">Quick Actions</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <a href="{{ route('profile') }}" class="text-center p-4 border border-gray-300 rounded hover:bg-gray-50">
                <div class="text-2xl mb-2">👤</div>
                <div>Edit Profile</div>
            </a>
            <a href="{{ route('payment.credits') }}" class="text-center p-4 border border-gray-300 rounded hover:bg-gray-50">
                <div class="text-2xl mb-2">💳</div>
                <div>Purchase Credits</div>
            </a>
            <a href="{{ route('shoots') }}" class="text-center p-4 border border-gray-300 rounded hover:bg-gray-50">
                <div class="text-2xl mb-2">🎯</div>
                <div>Shoot History</div>
            </a>
        </div>
    </div>
</div>
@endsection
