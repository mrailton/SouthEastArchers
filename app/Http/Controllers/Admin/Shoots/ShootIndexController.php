<?php

namespace App\Http\Controllers\Admin\Shoots;

use App\Http\Controllers\Controller;
use App\Models\Shoot;
use Illuminate\Http\Request;
use Illuminate\View\View;

class ShootIndexController extends Controller
{
    /**
     * Display the shoots list.
     */
    public function __invoke(Request $request): View
    {
        $shoots = Shoot::with('users')
            ->orderByDesc('date')
            ->paginate(20);

        return view('admin.shoots.index', [
            'shoots' => $shoots,
        ]);
    }
}
