@extends('layouts.app')

@section('title', 'My Shoots')

@section('content')
<div class="max-w-4xl mx-auto">
    <h1 class="text-3xl font-bold mb-6">My Shoot History</h1>
    
    <div class="bg-blue-100 border-l-4 border-blue-500 p-4 mb-6">
        <p class="text-sm text-blue-700">
            <strong>Credits Remaining:</strong> {{ $user->membership?->creditsRemaining() ?? 0 }}
        </p>
    </div>
    
    @if($shoots->count() > 0)
    <div class="bg-white shadow overflow-hidden sm:rounded-md">
        <ul class="divide-y divide-gray-200">
            @foreach($shoots as $shoot)
            <li class="px-6 py-4">
                <div class="flex items-center justify-between">
                    <div>
                        <h3 class="text-lg font-medium text-gray-900">
                            {{ $shoot->date->format('d M Y') }} - {{ $shoot->location->value }}
                        </h3>
                        @if($shoot->description)
                        <p class="mt-1 text-sm text-gray-600">{{ $shoot->description }}</p>
                        @endif
                    </div>
                    <div class="text-sm text-gray-500">
                        <span class="badge badge-success">
                            Attended
                        </span>
                    </div>
                </div>
            </li>
            @endforeach
        </ul>
    </div>
    
    <div class="mt-6">
        {{ $shoots->links() }}
    </div>
    @else
    <div class="bg-white shadow sm:rounded-lg p-6">
        <p class="text-gray-600">You haven't attended any shoots yet.</p>
    </div>
    @endif
</div>
@endsection
