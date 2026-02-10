<?php

namespace App\Http\Controllers\PublicPages;

use App\Http\Controllers\Controller;
use App\Models\News;
use Illuminate\Http\Request;
use Illuminate\View\View;

class NewsIndexController extends Controller
{
    /**
     * Display the news listing page.
     */
    public function __invoke(Request $request): View
    {
        $news = News::where('published', true)
            ->orderByDesc('published_at')
            ->paginate(10);

        return view('public.news.index', [
            'news' => $news,
        ]);
    }
}
