@extends('layouts.app')

@section('title', 'News')

@section('content')
<h1 class="text-4xl font-bold mb-6">Club News</h1>

@if($news->count() > 0)
    <div class="space-y-4">
        @foreach($news as $item)
            <div class="bg-white p-4 rounded shadow">
                <h2 class="text-2xl font-bold">
                    <a href="{{ route('news.show', $item) }}" class="text-blue-600 hover:underline">{{ $item->title }}</a>
                </h2>
                <p class="text-gray-600 text-sm">{{ ($item->published_at ?? $item->created_at)->format('Y-m-d') }}</p>
                <p class="text-gray-700">{{ $item->summary ?? Str::limit($item->content, 200) }}</p>
            </div>
        @endforeach
    </div>

    <div class="mt-6">
        {{ $news->links() }}
    </div>
@else
    <p class="text-gray-700">No news articles yet.</p>
@endif
@endsection
