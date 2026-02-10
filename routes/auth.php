<?php

use App\Http\Controllers\Auth\DestroySessionController;
use App\Http\Controllers\Auth\SendVerificationEmailController;
use App\Http\Controllers\Auth\ShowConfirmPasswordController;
use App\Http\Controllers\Auth\ShowForgotPasswordController;
use App\Http\Controllers\Auth\ShowLoginController;
use App\Http\Controllers\Auth\ShowRegisterController;
use App\Http\Controllers\Auth\ShowResetPasswordController;
use App\Http\Controllers\Auth\ShowVerifyEmailController;
use App\Http\Controllers\Auth\StoreConfirmPasswordController;
use App\Http\Controllers\Auth\StoreForgotPasswordController;
use App\Http\Controllers\Auth\StoreLoginController;
use App\Http\Controllers\Auth\StoreRegisterController;
use App\Http\Controllers\Auth\StoreResetPasswordController;
use App\Http\Controllers\Auth\UpdatePasswordController;
use App\Http\Controllers\Auth\VerifyEmailController;
use Illuminate\Support\Facades\Route;

Route::middleware('guest')->group(function () {
    Route::get('register', ShowRegisterController::class)
        ->name('register');

    Route::post('register', StoreRegisterController::class);

    Route::get('login', ShowLoginController::class)
        ->name('login');

    Route::post('login', StoreLoginController::class);

    Route::get('forgot-password', ShowForgotPasswordController::class)
        ->name('password.request');

    Route::post('forgot-password', StoreForgotPasswordController::class)
        ->name('password.email');

    Route::get('reset-password/{token}', ShowResetPasswordController::class)
        ->name('password.reset');

    Route::post('reset-password', StoreResetPasswordController::class)
        ->name('password.store');
});

Route::middleware('auth')->group(function () {
    Route::get('verify-email', ShowVerifyEmailController::class)
        ->name('verification.notice');

    Route::get('verify-email/{id}/{hash}', VerifyEmailController::class)
        ->middleware(['signed', 'throttle:6,1'])
        ->name('verification.verify');

    Route::post('email/verification-notification', SendVerificationEmailController::class)
        ->middleware('throttle:6,1')
        ->name('verification.send');

    Route::get('confirm-password', ShowConfirmPasswordController::class)
        ->name('password.confirm');

    Route::post('confirm-password', StoreConfirmPasswordController::class);

    Route::put('password', UpdatePasswordController::class)->name('password.update');

    Route::post('logout', DestroySessionController::class)
        ->name('logout');
});
