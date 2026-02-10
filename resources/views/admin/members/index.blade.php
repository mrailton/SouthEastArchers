@extends('layouts.app')

@section('title', 'Members')

@section('content')
<div class="max-w-6xl mx-auto">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold">Members</h1>
        @can('members.create')
        <a href="{{ route('admin.members.create') }}" class="btn-primary px-4 py-2">
            Create Member
        </a>
        @endcan
    </div>
    
    <div class="bg-white shadow overflow-hidden sm:rounded-md">
        <ul class="divide-y divide-gray-200">
            @foreach($members as $member)
            <li class="px-6 py-4 hover:bg-gray-50 {{ $member->membership?->status === \App\Enums\MembershipStatus::Pending ? 'bg-yellow-50' : '' }}">
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        <div class="flex items-center">
                            <h3 class="text-lg font-medium text-gray-900">
                                {{ $member->name }}
                                @foreach($member->roles as $role)
                                <span class="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                                    {{ $role->name }}
                                </span>
                                @endforeach
                                @if($member->roles->isEmpty())
                                <span class="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                    Member
                                </span>
                                @endif
                                @unless($member->is_active)
                                <span class="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                    Inactive
                                </span>
                                @endunless
                                @if($member->membership?->status === \App\Enums\MembershipStatus::Pending)
                                <span class="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                    ⚠ Pending Payment
                                </span>
                                @endif
                            </h3>
                        </div>
                        <p class="mt-1 text-sm text-gray-600">{{ $member->email }}</p>
                        @if($member->membership)
                        <p class="mt-1 text-sm text-gray-500">
                            Membership: 
                            <span class="font-medium {{ $member->membership->status === \App\Enums\MembershipStatus::Active ? 'text-green-600' : ($member->membership->status === \App\Enums\MembershipStatus::Pending ? 'text-yellow-600' : 'text-gray-600') }}">
                                {{ ucfirst($member->membership->status->value) }}
                            </span>
                            | Credits: {{ $member->membership->creditsRemaining() }}
                        </p>
                        @else
                        <p class="mt-1 text-sm text-gray-500">No membership</p>
                        @endif
                    </div>
                    <div class="flex gap-2">
                        <a href="{{ route('admin.members.show', $member) }}" 
                           class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                            View
                        </a>
                        @can('members.update')
                        <a href="{{ route('admin.members.edit', $member) }}" 
                           class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                            Edit
                        </a>
                        @endcan
                    </div>
                </div>
            </li>
            @endforeach
        </ul>
    </div>
    
    <div class="mt-6">
        {{ $members->links() }}
    </div>
</div>
@endsection
