<?php

namespace App\Http\Controllers\Admin\Shoots;

use App\Enums\ShootLocation;
use App\Http\Controllers\Controller;
use App\Models\Shoot;
use App\Models\User;
use Illuminate\View\View;

class EditShootController extends Controller
{
    /**
     * Display the edit shoot form.
     */
    public function __invoke(Shoot $shoot): View
    {
        $shoot->load('users');

        return view('admin.shoots.edit', [
            'shoot' => $shoot,
            'members' => User::where('is_active', true)->orderBy('name')->get(),
            'locations' => ShootLocation::cases(),
        ]);
    }
}
