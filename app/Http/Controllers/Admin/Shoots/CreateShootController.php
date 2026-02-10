<?php

namespace App\Http\Controllers\Admin\Shoots;

use App\Enums\ShootLocation;
use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\View\View;

class CreateShootController extends Controller
{
    /**
     * Display the create shoot form.
     */
    public function __invoke(): View
    {
        return view('admin.shoots.create', [
            'members' => User::where('is_active', true)->orderBy('name')->get(),
            'locations' => ShootLocation::cases(),
        ]);
    }
}
