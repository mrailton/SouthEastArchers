@extends('layouts.app')

@section('title', 'Shoots')

@section('content')
<div class="max-w-6xl mx-auto">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold">Shoots</h1>
        @can('shoots.create')
        <a href="{{ route('admin.shoots.create') }}" class="btn-primary px-4 py-2">
            Create Shoot
        </a>
        @endcan
    </div>
    
    @if($shoots->count() > 0)
    <div class="bg-white shadow overflow-hidden sm:rounded-md">
        <ul class="divide-y divide-gray-200">
            @foreach($shoots as $shoot)
            <li class="px-6 py-4 hover:bg-gray-50">
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        <h3 class="text-lg font-medium text-gray-900">
                            {{ $shoot->date->format('d M Y') }} - {{ $shoot->location->value }}
                        </h3>
                        @if($shoot->description)
                        <p class="mt-1 text-sm text-gray-600">{{ $shoot->description }}</p>
                        @endif
                        <p class="mt-1 text-sm text-gray-500">
                            {{ $shoot->users->count() }} attendees
                            @if($shoot->users->count() > 0)
                            <span class="ml-2">({{ $shoot->users->pluck('name')->join(', ') }})</span>
                            @endif
                        </p>
                    </div>
                    @can('shoots.update')
                    <a href="{{ route('admin.shoots.edit', $shoot) }}" 
                       class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                        Edit
                    </a>
                    @endcan
                </div>
            </li>
            @endforeach
        </ul>
    </div>
    
    <div class="mt-6">
        {{ $shoots->links() }}
    </div>
    @else
    <p class="text-gray-600">No shoots recorded yet.</p>
    @endif
</div>
@endsection
