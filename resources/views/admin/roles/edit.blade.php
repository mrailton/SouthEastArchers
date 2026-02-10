@extends('layouts.app')

@section('title', 'Edit Role')

@section('content')
<div class="max-w-2xl mx-auto">
    <h1 class="text-4xl font-bold mb-6">Edit Role: {{ $role->name }}</h1>
    
    <div class="bg-white p-8 rounded shadow">
        <form method="POST" action="{{ route('admin.roles.update', $role) }}" class="space-y-6">
            @csrf
            @method('PUT')
            
            <div>
                <label for="name" class="block text-gray-700 font-bold mb-2">Role Name *</label>
                <input class="w-full border border-gray-300 rounded px-3 py-2" type="text" id="name" name="name" value="{{ old('name', $role->name) }}" required>
            </div>
            
            <div>
                <label class="block text-gray-700 font-bold mb-2">Permissions</label>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                    @foreach($permissions as $permission)
                    <label class="inline-flex items-center">
                        <input type="checkbox" name="permissions[]" value="{{ $permission->name }}" class="rounded border-gray-300"
                               {{ in_array($permission->name, old('permissions', $role->permissions->pluck('name')->toArray())) ? 'checked' : '' }}>
                        <span class="ml-2 text-sm">{{ $permission->name }}</span>
                    </label>
                    @endforeach
                </div>
            </div>
            
            <div class="flex gap-4">
                <button type="submit" class="btn-primary py-2 px-6">Update Role</button>
                <a href="{{ route('admin.roles.index') }}" class="btn-secondary py-2 px-6">Cancel</a>
            </div>
        </form>
    </div>
</div>
@endsection
