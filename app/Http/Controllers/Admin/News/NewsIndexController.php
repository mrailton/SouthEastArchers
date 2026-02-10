<?php

namespace App\Http\Controllers\Admin\News;

use App\Http\Controllers\Controller;
use App\Models\News;
use Illuminate\Http\Request;
use Illuminate\View\View;

class NewsIndexController extends Controller
{
    /**
     * Display the news list.
     */
    public function __invoke(Request $request): View
    {
        $news = News::orderByDesc('created_at')
            ->paginate(20);

        return view('admin.news.index', [
            'news' => $news,
        ]);
    }
}
