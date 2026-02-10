<?php

namespace App\Http\Controllers\Admin\News;

use App\Http\Controllers\Controller;
use App\Models\News;
use Illuminate\View\View;

class EditNewsController extends Controller
{
    /**
     * Display the edit news form.
     */
    public function __invoke(News $news): View
    {
        return view('admin.news.edit', [
            'news' => $news,
        ]);
    }
}
