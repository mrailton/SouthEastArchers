<?php

namespace App\Http\Controllers\Admin\News;

use App\Http\Controllers\Controller;
use Illuminate\View\View;

class CreateNewsController extends Controller
{
    /**
     * Display the create news form.
     */
    public function __invoke(): View
    {
        return view('admin.news.create');
    }
}
