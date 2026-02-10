<?php

use App\Http\Controllers\Admin\DashboardController as AdminDashboardController;
use App\Http\Controllers\Admin\Events\CreateEventController;
use App\Http\Controllers\Admin\Events\EditEventController;
use App\Http\Controllers\Admin\Events\EventsIndexController;
use App\Http\Controllers\Admin\Events\StoreEventController;
use App\Http\Controllers\Admin\Events\UpdateEventController;
use App\Http\Controllers\Admin\Members\ActivateAccountController;
use App\Http\Controllers\Admin\Members\ActivateMembershipController;
use App\Http\Controllers\Admin\Members\CreateMemberController;
use App\Http\Controllers\Admin\Members\EditMemberController;
use App\Http\Controllers\Admin\Members\MembersIndexController;
use App\Http\Controllers\Admin\Members\RenewMembershipController;
use App\Http\Controllers\Admin\Members\ShowMemberController;
use App\Http\Controllers\Admin\Members\StoreMemberController;
use App\Http\Controllers\Admin\Members\UpdateMemberController;
use App\Http\Controllers\Admin\News\CreateNewsController;
use App\Http\Controllers\Admin\News\EditNewsController;
use App\Http\Controllers\Admin\News\NewsIndexController as AdminNewsIndexController;
use App\Http\Controllers\Admin\News\StoreNewsController;
use App\Http\Controllers\Admin\News\UpdateNewsController;
use App\Http\Controllers\Admin\Payments\ConfirmPaymentController;
use App\Http\Controllers\Admin\Payments\PendingPaymentsIndexController;
use App\Http\Controllers\Admin\Roles\CreateRoleController;
use App\Http\Controllers\Admin\Roles\DeleteRoleController;
use App\Http\Controllers\Admin\Roles\EditRoleController;
use App\Http\Controllers\Admin\Roles\RolesIndexController;
use App\Http\Controllers\Admin\Roles\StoreRoleController;
use App\Http\Controllers\Admin\Roles\UpdateRoleController;
use App\Http\Controllers\Admin\Shoots\CreateShootController;
use App\Http\Controllers\Admin\Shoots\EditShootController;
use App\Http\Controllers\Admin\Shoots\ShootsIndexController;
use App\Http\Controllers\Admin\Shoots\StoreShootController;
use App\Http\Controllers\Admin\Shoots\UpdateShootController;
use App\Http\Controllers\Admin\ShowSettingsController;
use App\Http\Controllers\Admin\UpdateSettingsController;
use App\Http\Controllers\Member\DashboardController;
use App\Http\Controllers\Member\ShowChangePasswordController;
use App\Http\Controllers\Member\ShowCreditsController;
use App\Http\Controllers\Member\ShowProfileController;
use App\Http\Controllers\Member\ShowShootsHistoryController;
use App\Http\Controllers\Member\UpdatePasswordController as MemberUpdatePasswordController;
use App\Http\Controllers\Member\UpdateProfileController;
use App\Http\Controllers\Payment\ProcessCheckoutController;
use App\Http\Controllers\Payment\ShowCheckoutController;
use App\Http\Controllers\Payment\ShowCreditPurchaseController;
use App\Http\Controllers\Payment\ShowMembershipPaymentController;
use App\Http\Controllers\Payment\ShowPaymentHistoryController;
use App\Http\Controllers\Payment\StoreCreditPurchaseController;
use App\Http\Controllers\Payment\StoreMembershipPaymentController;
use App\Http\Controllers\PublicPages\NewsIndexController;
use App\Http\Controllers\PublicPages\ShowAboutController;
use App\Http\Controllers\PublicPages\ShowEventsController;
use App\Http\Controllers\PublicPages\ShowHomeController;
use App\Http\Controllers\PublicPages\ShowMembershipInfoController;
use App\Http\Controllers\PublicPages\ShowNewsController;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| Public Routes
|--------------------------------------------------------------------------
*/

Route::get('/', ShowHomeController::class)->name('home');
Route::get('/about', ShowAboutController::class)->name('about');
Route::get('/news', NewsIndexController::class)->name('news');
Route::get('/news/{news}', ShowNewsController::class)->name('news.show');
Route::get('/events', ShowEventsController::class)->name('events');
Route::get('/membership', ShowMembershipInfoController::class)->name('membership');

/*
|--------------------------------------------------------------------------
| Member Routes
|--------------------------------------------------------------------------
*/

Route::middleware('auth')->group(function () {
    Route::get('/dashboard', DashboardController::class)->name('dashboard');
    Route::get('/shoots', ShowShootsHistoryController::class)->name('shoots');
    Route::get('/credits', ShowCreditsController::class)->name('credits');

    Route::get('/profile', ShowProfileController::class)->name('profile');
    Route::put('/profile', UpdateProfileController::class)->name('profile.update');

    Route::get('/change-password', ShowChangePasswordController::class)->name('change-password');
    Route::put('/change-password', MemberUpdatePasswordController::class)->name('change-password.update');

    // Payment routes
    Route::prefix('payment')->name('payment.')->group(function () {
        Route::get('/membership', ShowMembershipPaymentController::class)->name('membership');
        Route::post('/membership', StoreMembershipPaymentController::class);
        Route::get('/credits', ShowCreditPurchaseController::class)->name('credits');
        Route::post('/credits', StoreCreditPurchaseController::class);
        Route::get('/checkout/{checkout_id}', ShowCheckoutController::class)->name('checkout');
        Route::post('/checkout/{checkout_id}/process', ProcessCheckoutController::class)->name('checkout.process');
        Route::get('/history', ShowPaymentHistoryController::class)->name('history');
    });
});

/*
|--------------------------------------------------------------------------
| Admin Routes
|--------------------------------------------------------------------------
*/

Route::prefix('admin')->name('admin.')->middleware(['auth', 'can:admin.dashboard.view'])->group(function () {
    Route::get('/', AdminDashboardController::class)->name('dashboard');

    // Members
    Route::prefix('members')->name('members.')->middleware('can:members.read')->group(function () {
        Route::get('/', MembersIndexController::class)->name('index');
        Route::get('/create', CreateMemberController::class)->name('create')->middleware('can:members.create');
        Route::post('/', StoreMemberController::class)->name('store')->middleware('can:members.create');
        Route::get('/{user}', ShowMemberController::class)->name('show');
        Route::get('/{user}/edit', EditMemberController::class)->name('edit')->middleware('can:members.update');
        Route::put('/{user}', UpdateMemberController::class)->name('update')->middleware('can:members.update');
        Route::post('/{user}/activate', ActivateAccountController::class)->name('activate')->middleware('can:members.activate_account');
        Route::post('/{user}/membership/activate', ActivateMembershipController::class)->name('membership.activate')->middleware('can:members.manage_membership');
        Route::post('/{user}/membership/renew', RenewMembershipController::class)->name('membership.renew')->middleware('can:members.manage_membership');
    });

    // Shoots
    Route::prefix('shoots')->name('shoots.')->middleware('can:shoots.read')->group(function () {
        Route::get('/', ShootsIndexController::class)->name('index');
        Route::get('/create', CreateShootController::class)->name('create')->middleware('can:shoots.create');
        Route::post('/', StoreShootController::class)->name('store')->middleware('can:shoots.create');
        Route::get('/{shoot}/edit', EditShootController::class)->name('edit')->middleware('can:shoots.update');
        Route::put('/{shoot}', UpdateShootController::class)->name('update')->middleware('can:shoots.update');
    });

    // Events
    Route::prefix('events')->name('events.')->middleware('can:events.read')->group(function () {
        Route::get('/', EventsIndexController::class)->name('index');
        Route::get('/create', CreateEventController::class)->name('create')->middleware('can:events.create');
        Route::post('/', StoreEventController::class)->name('store')->middleware('can:events.create');
        Route::get('/{event}/edit', EditEventController::class)->name('edit')->middleware('can:events.update');
        Route::put('/{event}', UpdateEventController::class)->name('update')->middleware('can:events.update');
    });

    // News
    Route::prefix('news')->name('news.')->middleware('can:news.read')->group(function () {
        Route::get('/', AdminNewsIndexController::class)->name('index');
        Route::get('/create', CreateNewsController::class)->name('create')->middleware('can:news.create');
        Route::post('/', StoreNewsController::class)->name('store')->middleware('can:news.create');
        Route::get('/{news}/edit', EditNewsController::class)->name('edit')->middleware('can:news.update');
        Route::put('/{news}', UpdateNewsController::class)->name('update')->middleware('can:news.update');
    });

    // Roles
    Route::prefix('roles')->name('roles.')->middleware('can:roles.manage')->group(function () {
        Route::get('/', RolesIndexController::class)->name('index');
        Route::get('/create', CreateRoleController::class)->name('create');
        Route::post('/', StoreRoleController::class)->name('store');
        Route::get('/{role}/edit', EditRoleController::class)->name('edit');
        Route::put('/{role}', UpdateRoleController::class)->name('update');
        Route::delete('/{role}', DeleteRoleController::class)->name('destroy');
    });

    // Settings
    Route::get('/settings', ShowSettingsController::class)->name('settings')->middleware('can:settings.read');
    Route::put('/settings', UpdateSettingsController::class)->name('settings.update')->middleware('can:settings.write');

    // Pending Payments
    Route::prefix('payments')->name('payments.')->middleware('can:payments.manage')->group(function () {
        Route::get('/pending', PendingPaymentsIndexController::class)->name('pending');
        Route::post('/{payment}/confirm', ConfirmPaymentController::class)->name('confirm');
    });
});

require __DIR__ . '/auth.php';
