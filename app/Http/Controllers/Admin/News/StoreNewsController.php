<?php

namespace App\Http\Controllers\Admin\News;

use App\Http\Controllers\Controller;
use App\Models\News;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;

class StoreNewsController extends Controller
{
    /**
     * Store a new news article.
     */
    public function __invoke(Request $request): RedirectResponse
    {
        $validated = $request->validate([
            'title' => ['required', 'string', 'max:255'],
            'content' => ['required', 'string'],
            'summary' => ['nullable', 'string', 'max:500'],
            'published' => ['boolean'],
        ]);

        News::create([
            'title' => $validated['title'],
            'content' => $validated['content'],
            'summary' => $validated['summary'] ?? null,
            'published' => $validated['published'] ?? false,
            'published_at' => ($validated['published'] ?? false) ? now() : null,
        ]);

        return redirect()->route('admin.news.index')
            ->with('success', 'News article created successfully.');
    }
}
