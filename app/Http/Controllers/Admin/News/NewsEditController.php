<?php

namespace App\Http\Controllers\Admin\News;

use App\Http\Controllers\Controller;
use App\Models\News;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;

class NewsEditController extends Controller
{
    /**
     * Display the edit news form.
     */
    public function show(Request $request, News $news): View
    {
        return view('admin.news.edit', [
            'news' => $news,
        ]);
    }

    /**
     * Update the news article.
     */
    public function update(Request $request, News $news): RedirectResponse
    {
        $validated = $request->validate([
            'title' => ['required', 'string', 'max:255'],
            'content' => ['required', 'string'],
            'summary' => ['nullable', 'string', 'max:500'],
            'published' => ['boolean'],
        ]);

        $wasPublished = $news->published;
        $nowPublished = $validated['published'] ?? false;

        $news->update([
            'title' => $validated['title'],
            'content' => $validated['content'],
            'summary' => $validated['summary'] ?? null,
            'published' => $nowPublished,
            'published_at' => (! $wasPublished && $nowPublished) ? now() : $news->published_at,
        ]);

        return redirect()->route('admin.news.index')
            ->with('success', 'News article updated successfully.');
    }
}
