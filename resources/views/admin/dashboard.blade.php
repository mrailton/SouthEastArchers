@extends('layouts.app')

@section('title', 'Admin Dashboard')

@section('content')
<h1 class="text-4xl font-bold mb-6">Admin Dashboard</h1>

<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
    <div class="bg-white p-6 rounded shadow">
        <h3 class="text-gray-600 text-sm font-bold">Total Members</h3>
        <p class="text-3xl font-bold">{{ $totalMembers }}</p>
    </div>
    
    <div class="bg-white p-6 rounded shadow">
        <h3 class="text-gray-600 text-sm font-bold">Active Memberships</h3>
        <p class="text-3xl font-bold">{{ $activeMemberships }}</p>
    </div>
    
    <div class="bg-white p-6 rounded shadow">
        <h3 class="text-gray-600 text-sm font-bold">Memberships Expiring in 30 Days</h3>
        <p class="text-3xl font-bold">{{ $expiringSoon }}</p>
    </div>
</div>

<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
    <div class="bg-white p-6 rounded shadow">
        <h3 class="text-xl font-bold mb-4">Management</h3>
        <ul class="space-y-2">
            @can('members.read')
            <li><a href="{{ route('admin.members.index') }}" class="text-blue-600 hover:underline">Manage Members</a></li>
            @endcan
            @can('shoots.read')
            <li><a href="{{ route('admin.shoots.index') }}" class="text-blue-600 hover:underline">Manage Shoots</a></li>
            @endcan
            @can('news.read')
            <li><a href="{{ route('admin.news.index') }}" class="text-blue-600 hover:underline">Manage News</a></li>
            @endcan
            @can('events.read')
            <li><a href="{{ route('admin.events.index') }}" class="text-blue-600 hover:underline">Manage Events</a></li>
            @endcan
            @can('settings.read')
            <li><a href="{{ route('admin.settings') }}" class="text-blue-600 hover:underline">Application Settings</a></li>
            @endcan
            @can('roles.manage')
            <li><a href="{{ route('admin.roles.index') }}" class="text-blue-600 hover:underline">Manage Roles &amp; Permissions</a></li>
            @endcan
            @can('payments.manage')
            <li><a href="{{ route('admin.payments.pending') }}" class="text-blue-600 hover:underline">Pending Cash Payments</a></li>
            @endcan
        </ul>
    </div>
    
    <div class="bg-white p-6 rounded shadow">
        <h3 class="text-xl font-bold mb-4">Recent Members</h3>
        @if($recentMembers->count() > 0)
        <ul class="space-y-2">
            @foreach($recentMembers as $member)
            <li class="text-gray-700">
                <a href="{{ route('admin.members.show', $member) }}" class="text-blue-600 hover:underline">{{ $member->name }}</a>
                <span class="text-sm text-gray-500">- {{ $member->created_at->format('d/m/Y') }}</span>
            </li>
            @endforeach
        </ul>
        @else
        <p class="text-gray-500">No recent members</p>
        @endif
    </div>
</div>
@endsection
