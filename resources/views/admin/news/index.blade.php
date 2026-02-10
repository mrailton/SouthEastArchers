@extends('layouts.app')

@section('title', 'News')

@section('content')
<div class="max-w-6xl mx-auto">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold">News</h1>
        @can('news.create')
        <a href="{{ route('admin.news.create') }}" class="btn-primary px-4 py-2">Create Article</a>
        @endcan
    </div>
    
    @if($news->count() > 0)
    <div class="bg-white shadow overflow-hidden sm:rounded-md">
        <ul class="divide-y divide-gray-200">
            @foreach($news as $article)
            <li class="px-6 py-4 hover:bg-gray-50">
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        <h3 class="text-lg font-medium text-gray-900">{{ $article->title }}</h3>
                        <p class="mt-1 text-sm text-gray-600">{{ $article->created_at->format('d M Y') }}</p>
                        <span class="badge {{ $article->published ? 'badge-success' : 'badge-warning' }}">
                            {{ $article->published ? 'Published' : 'Draft' }}
                        </span>
                    </div>
                    @can('news.update')
                    <a href="{{ route('admin.news.edit', $article) }}" class="btn-secondary px-3 py-2">Edit</a>
                    @endcan
                </div>
            </li>
            @endforeach
        </ul>
    </div>
    <div class="mt-6">{{ $news->links() }}</div>
    @else
    <p class="text-gray-600">No news articles yet.</p>
    @endif
</div>
@endsection
