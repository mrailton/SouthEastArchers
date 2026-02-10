@extends('layouts.app')

@section('title', 'Create News')

@section('content')
<div class="max-w-2xl mx-auto">
    <h1 class="text-4xl font-bold mb-6">Create News Article</h1>
    
    <div class="bg-white p-8 rounded shadow">
        <form method="POST" action="{{ route('admin.news.store') }}" class="space-y-6">
            @csrf
            
            <div>
                <label for="title" class="block text-gray-700 font-bold mb-2">Title *</label>
                <input class="w-full border border-gray-300 rounded px-3 py-2" type="text" id="title" name="title" value="{{ old('title') }}" required>
            </div>
            
            <div>
                <label for="summary" class="block text-gray-700 font-bold mb-2">Summary</label>
                <textarea class="w-full border border-gray-300 rounded px-3 py-2" id="summary" name="summary" rows="2">{{ old('summary') }}</textarea>
            </div>
            
            <div>
                <label for="content" class="block text-gray-700 font-bold mb-2">Content *</label>
                <textarea class="w-full border border-gray-300 rounded px-3 py-2" id="content" name="content" rows="10" required>{{ old('content') }}</textarea>
            </div>
            
            <div>
                <label class="inline-flex items-center">
                    <input type="checkbox" name="published" value="1" class="rounded border-gray-300" {{ old('published') ? 'checked' : '' }}>
                    <span class="ml-2">Publish immediately</span>
                </label>
            </div>
            
            <div class="flex gap-4">
                <button type="submit" class="btn-primary py-2 px-6">Create Article</button>
                <a href="{{ route('admin.news.index') }}" class="btn-secondary py-2 px-6">Cancel</a>
            </div>
        </form>
    </div>
</div>
@endsection
