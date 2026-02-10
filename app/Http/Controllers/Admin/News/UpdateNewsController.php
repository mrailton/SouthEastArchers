<?php

namespace App\Http\Controllers\Admin\News;

use App\Http\Controllers\Controller;
use App\Models\News;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;

class UpdateNewsController extends Controller
{
    /**
     * Update the news article.
     */
    public function __invoke(Request $request, News $news): RedirectResponse
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
