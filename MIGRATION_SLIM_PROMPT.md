# Migrate SouthEastArchers from FastAPI to Slim Framework 4 with PHP 8.3+

You are helping migrate a FastAPI Python application to a PHP-based backend using modern PHP tools and patterns. This is a complete rewrite, but the business logic, user workflows, and features remain the same.

## Project Context

**Source Application:** SouthEastArchers - a club management system (FastAPI + SQLAlchemy + MySQL)

**Key Features to Preserve:**
- Member management and registration
- Membership status tracking and renewal
- Shoot scheduling and registration
- Credits system (included + purchasable)
- Payment processing (SumUp card payments, cash approvals)
- Admin dashboard and management
- Email notifications
- Scheduled tasks (membership expiry, low-credits reminders)
- User authentication and session management

**Current Database:** MySQL with ~20-30 tables

**Target Stack:**
- PHP 8.3+ with strict types (`declare(strict_types=1)`)
- Slim Framework 4 (lightweight, PSR-15 middleware)
- Doctrine ORM with type hints
- Doctrine Migrations for schema management
- Twig for HTML templates
- Invokable controller classes (`__invoke()` pattern)
- PHPUnit for testing
- Rector for automated code modernization
- PHPStan for static analysis (level 9)

## Architecture

### Directory Structure

```
src/
├── Controllers/          # Invokable controller classes
│   ├── HomeController.php
│   ├── Auth/
│   │   ├── LoginController.php
│   │   ├── RegisterController.php
│   │   └── LogoutController.php
│   ├── Member/
│   │   ├── DashboardController.php
│   │   ├── ShootsController.php
│   │   └── PaymentController.php
│   └── Admin/
│       ├── DashboardController.php
│       ├── MembersController.php
│       ├── ShootsController.php
│       └── PaymentsController.php
├── Entity/              # Doctrine entities (models)
│   ├── User.php
│   ├── Member.php
│   ├── Shoot.php
│   ├── ShootRegistration.php
│   ├── Payment.php
│   ├── PaymentCredit.php
│   ├── News.php
│   └── Setting.php
├── Repository/         # Data access (Doctrine repositories)
│   ├── UserRepository.php
│   ├── MemberRepository.php
│   ├── ShootRepository.php
│   └── PaymentRepository.php
├── Service/           # Business logic
│   ├── UserService.php
│   ├── MembershipService.php
│   ├── PaymentService.php
│   ├── CreditService.php
│   ├── EmailService.php
│   └── SettingService.php
├── DTO/              # Data Transfer Objects (request/response)
│   ├── CreateUserDTO.php
│   ├── UpdateProfileDTO.php
│   └── PaymentDTO.php
├── Middleware/       # PSR-15 middleware
│   ├── AuthMiddleware.php
│   ├── AdminMiddleware.php
│   └── SessionMiddleware.php
├── Exception/        # Custom exceptions
│   ├── AuthenticationException.php
│   ├── AuthorizationException.php
│   └── ValidationException.php
├── Validator/        # Input validation
│   ├── UserValidator.php
│   └── PaymentValidator.php
├── Task/            # Scheduled tasks (cron jobs)
│   ├── ExpireMembershipsTask.php
│   └── LowCreditsReminderTask.php
├── Migration/       # Doctrine migration stubs (generated)
└── Config/
    ├── Database.php
    ├── Routes.php
    ├── Container.php
    └── Middleware.php
public/
├── index.php        # Application entry point
└── assets/          # Static files (CSS, JS, images)
templates/
├── layout.html.twig
├── home.html.twig
├── auth/
│   ├── login.html.twig
│   └── register.html.twig
├── member/
│   ├── dashboard.html.twig
│   ├── shoots.html.twig
│   └── payment.html.twig
└── admin/
    ├── dashboard.html.twig
    ├── members.html.twig
    ├── shoots.html.twig
    └── payments.html.twig
migrations/
├── Version20250106000001.php
└── Version20250106000002.php
tests/
├── Unit/
│   ├── Service/
│   │   ├── PaymentServiceTest.php
│   │   └── MembershipServiceTest.php
│   └── Validator/
│       └── UserValidatorTest.php
├── Integration/
│   ├── Controller/
│   │   ├── AuthControllerTest.php
│   │   └── PaymentControllerTest.php
│   └── Repository/
│       └── UserRepositoryTest.php
└── bootstrap.php
.env
.env.example
composer.json
phpunit.xml
phpstan.neon
rector.php
```

### Key Design Patterns

**Invokable Controllers:** Each controller is a class with `__invoke()` method:

```php
<?php declare(strict_types=1);

namespace App\Controllers\Auth;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use App\Service\UserService;

final class LoginController
{
    public function __construct(private UserService $userService) {}

    public function __invoke(ServerRequestInterface $request, ResponseInterface $response): ResponseInterface
    {
        // Handle login logic
        return $response;
    }
}
```

**Strict Types & Type Hints:** All files start with `declare(strict_types=1)` and use strict type hints:

```php
<?php declare(strict_types=1);

public function getUserById(int $userId): ?User
{
    return $this->entityManager->find(User::class, $userId);
}
```

**Service Layer:** Business logic in services, not controllers:

```php
<?php declare(strict_types=1);

namespace App\Service;

use App\Repository\UserRepository;

final class UserService
{
    public function __construct(private UserRepository $repository) {}

    public function createUser(string $email, string $password, string $name): User
    {
        // Validation, password hashing, user creation
        $user = new User($email, password_hash($password, PASSWORD_BCRYPT), $name);
        $this->repository->save($user);
        return $user;
    }
}
```

**Doctrine Entities with Type Hints:**

```php
<?php declare(strict_types=1);

namespace App\Entity;

use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity(repositoryClass: UserRepository::class)]
#[ORM\Table(name: 'users')]
final class User
{
    #[ORM\Id]
    #[ORM\GeneratedValue]
    #[ORM\Column(type: 'integer')]
    private int $id;

    #[ORM\Column(type: 'string', length: 255, unique: true)]
    private string $email;

    #[ORM\Column(type: 'string', length: 255)]
    private string $password;

    #[ORM\Column(type: 'boolean')]
    private bool $isAdmin = false;

    public function __construct(string $email, string $password, string $name)
    {
        $this->email = $email;
        $this->password = $password;
    }

    public function getId(): int
    {
        return $this->id;
    }

    public function isAdmin(): bool
    {
        return $this->isAdmin;
    }
}
```

**Simple Authorization:** Use `is_admin` flag instead of RBAC:

```php
<?php declare(strict_types=1);

namespace App\Middleware;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;
use App\Exception\AuthorizationException;

final class AdminMiddleware implements MiddlewareInterface
{
    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        $user = $request->getAttribute('user');
        
        if ($user === null || !$user->isAdmin()) {
            throw new AuthorizationException('Admin access required');
        }

        return $handler->handle($request);
    }
}
```

## Data Migration Strategy

### Phase 1: Create New Doctrine Schema

- Create all Doctrine entities and ORM mappings
- Run `php bin/console.php doctrine:migrations:generate` to auto-generate initial migration
- Creates new, clean MySQL schema with same structure as FastAPI version

### Phase 2: One-Time Data Import Command

Create a CLI command `php bin/console.php migrate:import-fastapi-data`:

This command will:

1. Connect to the existing FastAPI MySQL database
2. Read all tables (users, members, shoots, payments, etc.)
3. Transform and insert data into the new Doctrine schema:
   - Copy user data, hash existing passwords if needed
   - Extract RBAC roles/permissions into simple `is_admin` flag (any admin role → true, else false)
   - Copy all business data (members, shoots, payments, credits)
   - Maintain all foreign keys and relationships
   - Preserve timestamps and audit trails

4. Validate data integrity (row counts, referential integrity)
5. Report results (X users imported, Y payments imported, etc.)
6. Mark migration as complete (store in `migration_completed` setting)

**Command structure:**

```php
<?php declare(strict_types=1);

namespace App\Command;

use Doctrine\ORM\EntityManagerInterface;
use PDO;

final class ImportFastApiDataCommand
{
    public function __construct(
        private EntityManagerInterface $entityManager,
        private string $sourceDbUrl, // Environment variable pointing to old database
    ) {}

    public function execute(): void
    {
        // 1. Connect to source database
        // 2. Read all rows from each table
        // 3. Transform and insert into new entities
        // 4. Flush and commit
        // 5. Report statistics
    }
}
```

**Run once after deploying new schema:**

```bash
php bin/console.php migrate:import-fastapi-data
# Output: Imported 150 users, 45 shoots, 312 payments, ...
```

**Idempotent check:** If already run, command exits with "Migration already completed."

### Phase 3: Verification & Cutover

- Verify record counts match original
- Test key workflows (login, register, book shoot, process payment)
- Once verified, old FastAPI schema can be archived/deleted

## Authentication & Sessions

**Session Management:**
- Use PHP `$_SESSION` with secure cookie handling
- Middleware to load user from session on each request
- Simple login controller sets `$_SESSION['user_id']` on successful auth

**Password Hashing:**
- All passwords hashed with `password_hash($password, PASSWORD_BCRYPT)`
- Use `password_verify()` for login

**Admin Check:**
- Simple `$user->isAdmin()` check instead of role/permission lookups

## Configuration

**Database Configuration (`src/Config/Database.php`):**

```php
<?php declare(strict_types=1);

use Doctrine\DBAL\DriverManager;
use Doctrine\ORM\EntityManager;
use Doctrine\ORM\ORMSetup;

$config = ORMSetup::createAttributeMetadataConfiguration(
    paths: [__DIR__ . '/../Entity'],
    isDevMode: $_ENV['APP_ENV'] === 'development',
);

$connection = DriverManager::getConnection([
    'driver' => 'pdo_mysql',
    'url' => $_ENV['DATABASE_URL'],
]);

return EntityManager::create($connection, $config);
```

**Dependency Container (`src/Config/Container.php`):**

Use PSR-11 container (e.g., PHP-DI) for dependency injection:

```php
<?php declare(strict_types=1);

use DI\ContainerBuilder;
use Doctrine\ORM\EntityManagerInterface;

$builder = new ContainerBuilder();

$builder->addDefinitions([
    EntityManagerInterface::class => DI\create(EntityManager::class),
    UserRepository::class => DI\autowire(),
    UserService::class => DI\autowire(),
    // ... more services
]);

return $builder->build();
```

**Routes (`src/Config/Routes.php`):**

```php
<?php declare(strict_types=1);

use Slim\App;

return function (App $app): void {
    // Public routes
    $app->get('/', HomeController::class);
    $app->post('/auth/login', LoginController::class);
    $app->post('/auth/register', RegisterController::class);

    // Member routes (require auth middleware)
    $group = $app->group('/member')->add(AuthMiddleware::class);
    $group->get('/dashboard', MemberDashboardController::class);
    $group->get('/shoots', MemberShootsController::class);

    // Admin routes (require auth + admin middleware)
    $adminGroup = $app->group('/admin')->add(AuthMiddleware::class)->add(AdminMiddleware::class);
    $adminGroup->get('/dashboard', AdminDashboardController::class);
    $adminGroup->get('/members', AdminMembersController::class);
};
```

## Scheduled Tasks

**CLI Entry Point (`bin/console.php`):**

```php
#!/usr/bin/env php
<?php declare(strict_types=1);

require __DIR__ . '/../vendor/autoload.php';

$container = require __DIR__ . '/../src/Config/Container.php';

$commands = [
    new ExpireMembershipsCommand($container->get(MembershipService::class)),
    new LowCreditsReminderCommand($container->get(CreditService::class)),
    new ImportFastApiDataCommand($container->get(EntityManagerInterface::class), $_ENV['SOURCE_DATABASE_URL']),
];

// Simple command dispatcher or use Symfony Console
foreach ($commands as $command) {
    if ($argv[1] === $command->getName()) {
        $command->execute($argv);
        exit(0);
    }
}
```

**Run via Cron:**

```cron
# Expire memberships daily at 00:01
1 0 * * * cd /var/www/app && php bin/console.php migrate:expire-memberships

# Low credits reminder weekly on Monday 09:00
0 9 * * 1 cd /var/www/app && php bin/console.php migrate:low-credits-reminder

# One-time data import (run once after deployment)
# php bin/console.php migrate:import-fastapi-data
```

## Testing

**PHPUnit Configuration (`phpunit.xml`):**

- Test files in `tests/` mirror `src/` structure
- Use Doctrine `TestCase` for database tests
- Mock external services (SumUp API, email)

**Example Test:**

```php
<?php declare(strict_types=1);

namespace App\Tests\Unit\Service;

use PHPUnit\Framework\TestCase;
use App\Service\PaymentService;
use App\Repository\PaymentRepository;

final class PaymentServiceTest extends TestCase
{
    private PaymentService $service;
    private PaymentRepository $repository;

    protected function setUp(): void
    {
        $this->repository = $this->createMock(PaymentRepository::class);
        $this->service = new PaymentService($this->repository);
    }

    public function testCompletePaymentCreatesTransaction(): void
    {
        // Test logic
    }
}
```

## Code Quality Tools

**PHPStan (`phpstan.neon`):**

```neon
parameters:
    level: 9
    paths:
        - src/
        - tests/
    excludePaths:
        - vendor/
    checkMissingIterableValueType: true
    checkGenericClassInNonGenericObjectType: true
```

**Rector (`rector.php`):**

Auto-modernize code to PHP 8.3+ standards:

```bash
vendor/bin/rector process src/
```

## Build & Deployment

**Entry Point (`public/index.php`):**

```php
<?php declare(strict_types=1);

require __DIR__ . '/../vendor/autoload.php';

$app = require __DIR__ . '/../src/Config/Application.php';
$app->run();
```

**Docker Support:**

```dockerfile
FROM php:8.3-fpm

RUN docker-php-ext-install pdo pdo_mysql

COPY . /app
WORKDIR /app

RUN composer install --no-dev --optimize-autoloader

CMD ["php", "-S", "0.0.0.0:8000", "-t", "public/"]
```

## Specific Implementation Tasks

### Task 1: Create Doctrine Entities

Create all entity classes in `src/Entity/`:

- `User.php` — with `isAdmin` boolean flag (replace RBAC)
- `Member.php` — member profile + status
- `Shoot.php` — scheduled shoot
- `ShootRegistration.php` — attendance records
- `Payment.php` — payment records
- `PaymentCredit.php` — credit purchases
- `News.php` — club news/announcements
- `Setting.php` — application settings

All with:
- Doctrine ORM attributes (`#[ORM\...]`)
- Type-hinted properties
- Constructor with required fields
- Getter/setter methods with type hints
- `__toString()` for debugging

### Task 2: Create Doctrine Repositories

Create repository classes in `src/Repository/`:

- Extend `ServiceEntityRepository`
- Implement custom query methods (`findActiveMembers()`, `findExpiredMemberships()`, etc.)
- All methods with strict type hints
- Return types properly declared (`?User`, `array<Payment>`, etc.)

### Task 3: Create Service Layer

Create service classes in `src/Service/`:

- `UserService` — registration, login, profile updates
- `MembershipService` — activate, renew, expire memberships
- `PaymentService` — create, complete, cancel payments (without events, just direct calls)
- `CreditService` — purchase credits, deduct credits
- `EmailService` — send transactional emails (welcome, receipts, reminders)
- `SettingService` — get/set application settings

All services:
- Accept dependencies via constructor
- Contain business logic only (not HTTP logic)
- Use strict types
- Return DTOs or entities
- Throw custom exceptions for error cases

### Task 4: Create Controllers

Create invokable controller classes in `src/Controllers/`:

- Each controller = one action (single responsibility)
- Implement `__invoke(ServerRequestInterface, ResponseInterface): ResponseInterface`
- Inject dependencies via constructor
- Call services, not repositories
- Return JSON or Twig responses
- Handle validation errors gracefully

**Example controller structure:**

```php
<?php declare(strict_types=1);

namespace App\Controllers\Member;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use App\Service\PaymentService;
use App\DTO\PaymentDTO;

final class ProcessPaymentController
{
    public function __construct(
        private PaymentService $paymentService,
    ) {}

    public function __invoke(
        ServerRequestInterface $request,
        ResponseInterface $response,
    ): ResponseInterface {
        $body = $request->getParsedBody();
        
        // Validation
        if (empty($body['amount']) || empty($body['method'])) {
            return $this->jsonError($response, 'Invalid input', 400);
        }

        try {
            $payment = $this->paymentService->processPayment(
                userId: (int) $request->getAttribute('user_id'),
                amount: (float) $body['amount'],
                method: $body['method'],
            );

            return $this->json($response, $payment);
        } catch (PaymentException $e) {
            return $this->jsonError($response, $e->getMessage(), 422);
        }
    }

    private function json(ResponseInterface $response, mixed $data): ResponseInterface
    {
        $response->getBody()->write(json_encode($data));
        return $response->withHeader('Content-Type', 'application/json');
    }

    private function jsonError(ResponseInterface $response, string $message, int $code): ResponseInterface
    {
        $response->getBody()->write(json_encode(['error' => $message]));
        return $response->withStatus($code)->withHeader('Content-Type', 'application/json');
    }
}
```

### Task 5: Create Middleware

Create PSR-15 middleware in `src/Middleware/`:

- `AuthMiddleware` — load user from session, throw exception if not authenticated
- `AdminMiddleware` — check `isAdmin()`, throw exception if not admin
- `SessionMiddleware` — start/manage PHP sessions
- `ExceptionMiddleware` — catch exceptions, return JSON error responses

### Task 6: Create Validators

Create validator classes in `src/Validator/`:

- `UserValidator` — validate email, password strength, name
- `PaymentValidator` — validate payment amounts, methods
- Return validation error collections or throw `ValidationException`

### Task 7: Create DTOs

Create Data Transfer Objects in `src/DTO/`:

- `CreateUserDTO` — input for user registration
- `UpdateProfileDTO` — input for profile updates
- `PaymentDTO` — output for payment responses
- Use constructor promotion for concise syntax

### Task 8: Create Scheduled Tasks

Create task classes in `src/Task/`:

- `ExpireMembershipsTask` — mark expired memberships on configured date
- `LowCreditsReminderTask` — send email reminders to low-credit members
- Both should be callable via CLI

### Task 9: Create the Data Import Command

Create the one-time migration command in `src/Command/ImportFastApiDataCommand.php`:

**Requirements:**

1. Connect to source MySQL database (FastAPI schema) via environment variable `SOURCE_DATABASE_URL`
2. For each table, read all rows from FastAPI database:
   - Transform RBAC data: any `role_id` with admin role → `is_admin = 1`, else `0`
   - Copy all user data (users table)
   - Copy all member data (members table)
   - Copy all shoots (shoots table)
   - Copy all shoot registrations
   - Copy all payments
   - Copy all credits
   - Copy all news/announcements
   - Copy all settings
3. Insert into new Doctrine entities via EntityManager
4. Handle relationships/foreign keys properly
5. Log progress and errors
6. Verify row counts match
7. Set `migration_status = 'completed'` in settings
8. Exit with error if already run (idempotent)

**Example command execution:**

```bash
SOURCE_DATABASE_URL="mysql://user:pass@localhost/old_db" php bin/console.php migrate:import-fastapi-data
# Output:
# Importing users... 150 imported
# Importing members... 145 imported
# Importing shoots... 45 imported
# Importing shoot registrations... 312 imported
# Importing payments... 98 imported
# Importing credits... 267 imported
# Importing news... 12 imported
# Importing settings... 8 imported
# Migration completed successfully!
```

### Task 10: Create Twig Templates

Create HTML templates in `templates/`:

- Use Twig template inheritance (`extends`, `blocks`)
- Create `layout.html.twig` base template
- All pages extend base layout
- Use Twig filters and functions
- Include CSRF token in forms
- Responsive design (Bootstrap 5 or Tailwind)

**Example template:**

```twig
{# templates/member/dashboard.html.twig #}
{% extends "layout.html.twig" %}

{% block title %}Member Dashboard{% endblock %}

{% block content %}
<div class="container mt-5">
    <h1>Welcome, {{ user.name }}</h1>
    
    <div class="row">
        <div class="col-md-4">
            <div class="card">
                <div class="card-body">
                    <h5>Membership Status</h5>
                    <p>{{ membership.status }}</p>
                    <p class="text-muted">Expires: {{ membership.expiresAt|date('Y-m-d') }}</p>
                </div>
            </div>
        </div>
        
        <div class="col-md-4">
            <div class="card">
                <div class="card-body">
                    <h5>Available Credits</h5>
                    <p class="display-4">{{ user.credits }}</p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

## Deliverables

By the end of this refactoring, you should have:

1. ✅ Full PHP 8.3+ Slim Framework 4 application
2. ✅ All Doctrine entities with ORM mappings
3. ✅ All repositories with custom queries
4. ✅ Complete service layer (no business logic in controllers)
5. ✅ All controllers as invokable classes
6. ✅ Middleware for auth, admin, exceptions
7. ✅ Input validators
8. ✅ DTOs for requests/responses
9. ✅ Twig templates for all pages
10. ✅ Doctrine migrations (auto-generated + initial)
11. ✅ One-time data import command
12. ✅ Scheduled task commands (CLI)
13. ✅ PHPUnit test suite (unit + integration)
14. ✅ PHPStan at level 9 passing
15. ✅ Rector config for code modernization
16. ✅ `.env` and `.env.example` files
17. ✅ Docker configuration
18. ✅ `composer.json` with all dependencies
19. ✅ README with setup/deployment instructions

## Key Principles

- **Strict Types:** All files start with `declare(strict_types=1)`
- **Type Safety:** All methods have parameter and return type hints
- **No RBAC:** Simple `is_admin` boolean flag for authorization
- **No Events:** Direct service calls, no event dispatch
- **Clean Architecture:** Controllers → Services → Repositories → Entities
- **Testability:** All classes have dependencies injected, easy to mock
- **Code Quality:** PHPStan level 9, Rector automation, PHPUnit coverage
- **One-Time Migration:** Data import command handles all FastAPI → Slim migration

## Starting Point

Begin with:

1. `composer.json` scaffolding (Slim, Doctrine, Twig, dependencies)
2. Directory structure creation
3. `public/index.php` entry point
4. Doctrine setup and entity creation
5. Data import command (highest priority for preserving data)
6. Controllers and routes
7. Templates
8. Tests
9. Quality checks (PHPStan, Rector)
