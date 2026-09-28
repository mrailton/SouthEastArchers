<?php

declare(strict_types=1);

use App\Http\Controllers\AboutController;
use App\Http\Controllers\Auth\LoginController;
use App\Http\Controllers\Auth\ProcessLogoutController;
use App\Http\Controllers\Auth\StoreLoginController;
use App\Http\Controllers\IndexController;
use App\Http\Controllers\MembershipController;
use Illuminate\Support\Facades\Route;

Route::get('/', IndexController::class)->name('index');
Route::get('/about', AboutController::class)->name('about');
Route::get('/membership', MembershipController::class)->name('membership');

Route::middleware(['guest'])->group(function (): void {
    Route::get('/login', LoginController::class)->name('login');
    Route::post('/login', StoreLoginController::class)->name('login.post');
});

Route::middleware(['auth'])->group(function (): void {
    Route::post('/logout', ProcessLogoutController::class)->name('logout');
});
