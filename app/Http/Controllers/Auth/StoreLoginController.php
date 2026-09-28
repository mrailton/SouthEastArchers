<?php

declare(strict_types=1);

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;

class StoreLoginController extends Controller
{
    public function __invoke(Request $request): RedirectResponse
    {
        $request->validate([
            'email' => ['required', 'email'],
            'password' => ['required']
        ]);

        if ( ! Auth::attempt($request->only('email', 'password'))) {
            return redirect()->back()->withErrors(['email' => 'We were unable to authenticate you using the provided credentials'])->withInput();
        }

        $request->session()->regenerate();

        return redirect()->intended(route('index'))->with('success', 'You have successfully logged in');
    }
}
