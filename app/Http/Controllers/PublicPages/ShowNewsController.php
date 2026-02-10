<?php

namespace App\Http\Controllers\PublicPages;

use App\Http\Controllers\Controller;
use App\Models\News;
use Illuminate\Http\Request;
use Illuminate\View\View;

class ShowNewsController extends Controller
{
    /**
     * Display a news article.
     */
    public function __invoke(Request $request, News $news): View
    {
        abort_unless($news->published, 404);

        return view('public.news.show', [
            'news' => $news,
        ]);
    }
}
