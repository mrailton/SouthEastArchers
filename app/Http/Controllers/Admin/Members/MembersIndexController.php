<?php

namespace App\Http\Controllers\Admin\Members;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\View\View;

class MembersIndexController extends Controller
{
    /**
     * Display the members list.
     */
    public function __invoke(Request $request): View
    {
        $members = User::with(['membership', 'roles'])
            ->orderBy('name')
            ->paginate(20);

        return view('admin.members.index', [
            'members' => $members,
        ]);
    }
}
