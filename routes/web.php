<?php

use App\Http\Controllers\Admin\DashboardController as AdminDashboardController;
use App\Http\Controllers\Admin\Events\EventCreateController;
use App\Http\Controllers\Admin\Events\EventEditController;
use App\Http\Controllers\Admin\Events\EventIndexController;
use App\Http\Controllers\Admin\Members\ActivateAccountController;
use App\Http\Controllers\Admin\Members\ActivateMembershipController;
use App\Http\Controllers\Admin\Members\MemberCreateController;
use App\Http\Controllers\Admin\Members\MemberEditController;
use App\Http\Controllers\Admin\Members\MemberIndexController;
use App\Http\Controllers\Admin\Members\MemberShowController;
use App\Http\Controllers\Admin\Members\RenewMembershipController;
use App\Http\Controllers\Admin\News\NewsCreateController;
use App\Http\Controllers\Admin\News\NewsEditController;
use App\Http\Controllers\Admin\News\NewsIndexController;
use App\Http\Controllers\Admin\Payments\ConfirmCashPaymentController;
use App\Http\Controllers\Admin\Payments\PendingCashPaymentsController;
use App\Http\Controllers\Admin\Roles\RoleCreateController;
use App\Http\Controllers\Admin\Roles\RoleDeleteController;
use App\Http\Controllers\Admin\Roles\RoleEditController;
use App\Http\Controllers\Admin\Roles\RoleIndexController;
use App\Http\Controllers\Admin\SettingsController;
use App\Http\Controllers\Admin\Shoots\ShootCreateController;
use App\Http\Controllers\Admin\Shoots\ShootEditController;
use App\Http\Controllers\Admin\Shoots\ShootIndexController;
use App\Http\Controllers\Member\ChangePasswordController;
use App\Http\Controllers\Member\CreditsController;
use App\Http\Controllers\Member\DashboardController;
use App\Http\Controllers\Member\ProfileController;
use App\Http\Controllers\Member\ShootsHistoryController;
use App\Http\Controllers\Payment\CheckoutController;
use App\Http\Controllers\Payment\CreditPurchaseController;
use App\Http\Controllers\Payment\MembershipPaymentController;
use App\Http\Controllers\Payment\PaymentHistoryController;
use App\Http\Controllers\PublicPages\AboutController;
use App\Http\Controllers\PublicPages\EventsController;
use App\Http\Controllers\PublicPages\HomeController;
use App\Http\Controllers\PublicPages\MembershipInfoController;
use App\Http\Controllers\PublicPages\NewsListController;
use App\Http\Controllers\PublicPages\NewsShowController;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| Public Routes
|--------------------------------------------------------------------------
*/

Route::get('/', HomeController::class)->name('home');
Route::get('/about', AboutController::class)->name('about');
Route::get('/news', NewsListController::class)->name('news');
Route::get('/news/{news}', NewsShowController::class)->name('news.show');
Route::get('/events', EventsController::class)->name('events');
Route::get('/membership', MembershipInfoController::class)->name('membership');

/*
|--------------------------------------------------------------------------
| Member Routes
|--------------------------------------------------------------------------
*/

Route::middleware('auth')->group(function () {
    Route::get('/dashboard', DashboardController::class)->name('dashboard');
    Route::get('/shoots', ShootsHistoryController::class)->name('shoots');
    Route::get('/credits', CreditsController::class)->name('credits');

    Route::get('/profile', [ProfileController::class, 'show'])->name('profile');
    Route::put('/profile', [ProfileController::class, 'update'])->name('profile.update');

    Route::get('/change-password', [ChangePasswordController::class, 'show'])->name('change-password');
    Route::put('/change-password', [ChangePasswordController::class, 'update'])->name('change-password.update');

    // Payment routes
    Route::prefix('payment')->name('payment.')->group(function () {
        Route::get('/membership', [MembershipPaymentController::class, 'show'])->name('membership');
        Route::post('/membership', [MembershipPaymentController::class, 'store']);
        Route::get('/credits', [CreditPurchaseController::class, 'show'])->name('credits');
        Route::post('/credits', [CreditPurchaseController::class, 'store']);
        Route::get('/checkout/{checkout_id}', [CheckoutController::class, 'show'])->name('checkout');
        Route::post('/checkout/{checkout_id}/process', [CheckoutController::class, 'process'])->name('checkout.process');
        Route::get('/history', PaymentHistoryController::class)->name('history');
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
        Route::get('/', MemberIndexController::class)->name('index');
        Route::get('/create', [MemberCreateController::class, 'show'])->name('create')->middleware('can:members.create');
        Route::post('/', [MemberCreateController::class, 'store'])->name('store')->middleware('can:members.create');
        Route::get('/{user}', MemberShowController::class)->name('show');
        Route::get('/{user}/edit', [MemberEditController::class, 'show'])->name('edit')->middleware('can:members.update');
        Route::put('/{user}', [MemberEditController::class, 'update'])->name('update')->middleware('can:members.update');
        Route::post('/{user}/activate', ActivateAccountController::class)->name('activate')->middleware('can:members.activate_account');
        Route::post('/{user}/membership/activate', ActivateMembershipController::class)->name('membership.activate')->middleware('can:members.manage_membership');
        Route::post('/{user}/membership/renew', RenewMembershipController::class)->name('membership.renew')->middleware('can:members.manage_membership');
    });

    // Shoots
    Route::prefix('shoots')->name('shoots.')->middleware('can:shoots.read')->group(function () {
        Route::get('/', ShootIndexController::class)->name('index');
        Route::get('/create', [ShootCreateController::class, 'show'])->name('create')->middleware('can:shoots.create');
        Route::post('/', [ShootCreateController::class, 'store'])->name('store')->middleware('can:shoots.create');
        Route::get('/{shoot}/edit', [ShootEditController::class, 'show'])->name('edit')->middleware('can:shoots.update');
        Route::put('/{shoot}', [ShootEditController::class, 'update'])->name('update')->middleware('can:shoots.update');
    });

    // Events
    Route::prefix('events')->name('events.')->middleware('can:events.read')->group(function () {
        Route::get('/', EventIndexController::class)->name('index');
        Route::get('/create', [EventCreateController::class, 'show'])->name('create')->middleware('can:events.create');
        Route::post('/', [EventCreateController::class, 'store'])->name('store')->middleware('can:events.create');
        Route::get('/{event}/edit', [EventEditController::class, 'show'])->name('edit')->middleware('can:events.update');
        Route::put('/{event}', [EventEditController::class, 'update'])->name('update')->middleware('can:events.update');
    });

    // News
    Route::prefix('news')->name('news.')->middleware('can:news.read')->group(function () {
        Route::get('/', NewsIndexController::class)->name('index');
        Route::get('/create', [NewsCreateController::class, 'show'])->name('create')->middleware('can:news.create');
        Route::post('/', [NewsCreateController::class, 'store'])->name('store')->middleware('can:news.create');
        Route::get('/{news}/edit', [NewsEditController::class, 'show'])->name('edit')->middleware('can:news.update');
        Route::put('/{news}', [NewsEditController::class, 'update'])->name('update')->middleware('can:news.update');
    });

    // Roles
    Route::prefix('roles')->name('roles.')->middleware('can:roles.manage')->group(function () {
        Route::get('/', RoleIndexController::class)->name('index');
        Route::get('/create', [RoleCreateController::class, 'show'])->name('create');
        Route::post('/', [RoleCreateController::class, 'store'])->name('store');
        Route::get('/{role}/edit', [RoleEditController::class, 'show'])->name('edit');
        Route::put('/{role}', [RoleEditController::class, 'update'])->name('update');
        Route::delete('/{role}', RoleDeleteController::class)->name('destroy');
    });

    // Settings
    Route::get('/settings', [SettingsController::class, 'show'])->name('settings')->middleware('can:settings.read');
    Route::put('/settings', [SettingsController::class, 'update'])->name('settings.update')->middleware('can:settings.write');

    // Pending Payments
    Route::prefix('payments')->name('payments.')->middleware('can:payments.manage')->group(function () {
        Route::get('/pending', PendingCashPaymentsController::class)->name('pending');
        Route::post('/{payment}/confirm', ConfirmCashPaymentController::class)->name('confirm');
    });
});

require __DIR__ . '/auth.php';
