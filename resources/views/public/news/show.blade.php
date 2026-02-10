<x-app-layout>
    <x-slot name="title">{{ $news->title }}</x-slot>

    <article class="bg-white p-8 rounded shadow max-w-2xl">
        <h1 class="text-4xl font-bold mb-4">{{ $news->title }}</h1>
        <p class="text-gray-600 mb-4">Published: {{ ($news->published_at ?? $news->created_at)->format('Y-m-d H:i') }}</p>
        <div class="prose prose-lg text-gray-700">{!! nl2br(e($news->content)) !!}</div>
        <a href="{{ route('news') }}" class="text-blue-600 hover:underline mt-6 inline-block">&larr; Back to news</a>
    </article>
</x-app-layout>
