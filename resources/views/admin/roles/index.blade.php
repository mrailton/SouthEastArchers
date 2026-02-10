@extends('layouts.app')

@section('title', 'Roles')

@section('content')
<div class="max-w-4xl mx-auto">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold">Roles & Permissions</h1>
        <a href="{{ route('admin.roles.create') }}" class="btn-primary px-4 py-2">Create Role</a>
    </div>
    
    <div class="space-y-4">
        @foreach($roles as $role)
        <div class="bg-white p-6 rounded shadow">
            <div class="flex justify-between items-start">
                <div>
                    <h3 class="text-xl font-bold">{{ $role->name }}</h3>
                    <div class="mt-2 flex flex-wrap gap-1">
                        @foreach($role->permissions as $permission)
                        <span class="badge badge-secondary text-xs">{{ $permission->name }}</span>
                        @endforeach
                    </div>
                </div>
                <div class="flex gap-2">
                    <a href="{{ route('admin.roles.edit', $role) }}" class="btn-secondary px-3 py-1 text-sm">Edit</a>
                    @if($role->name !== 'Admin')
                    <form method="POST" action="{{ route('admin.roles.destroy', $role) }}" onsubmit="return confirm('Delete this role?');">
                        @csrf
                        @method('DELETE')
                        <button type="submit" class="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700">Delete</button>
                    </form>
                    @endif
                </div>
            </div>
        </div>
        @endforeach
    </div>
</div>
@endsection
