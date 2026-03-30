"""Code quality CLI commands."""

import os
import sys

import click

lint_cli = click.Group("lint", help="Code quality commands")


@lint_cli.command("check")
def lint_check():
    """Run linting and format checks with Ruff"""
    click.echo("=== Running Ruff Linting ===")
    exit_code_lint = os.system("ruff check app/ tests/")

    click.echo("\n=== Checking Code Format ===")
    exit_code_format = os.system("ruff format --check app/ tests/")

    if exit_code_lint == 0 and exit_code_format == 0:
        click.echo("\n✓ All checks passed!")
        sys.exit(0)
    else:
        click.echo("\n💡 Tip: Run 'flask lint fix' to auto-fix issues")
        sys.exit(1)


@lint_cli.command("fix")
def lint_fix():
    """Auto-fix linting and formatting issues with Ruff"""
    click.echo("=== Running Ruff Linting with --fix ===")
    exit_code_lint = os.system("ruff check --fix app/ tests/")

    click.echo("\n=== Formatting Code ===")
    exit_code_format = os.system("ruff format app/ tests/")

    if exit_code_lint == 0 and exit_code_format == 0:
        click.echo("\n✓ All issues fixed!")
        sys.exit(0)
    else:
        sys.exit(1)


@lint_cli.command("format")
@click.option("--check", is_flag=True, help="Check only, do not modify files")
def lint_format(check):
    """Format code with Ruff"""
    if check:
        click.echo("Checking code format with ruff...")
        exit_code = os.system("ruff format --check app/ tests/")
    else:
        click.echo("Formatting code with ruff...")
        exit_code = os.system("ruff format app/ tests/")
        if exit_code == 0:
            click.echo("✓ Code formatted!")

    sys.exit(exit_code >> 8)


@lint_cli.command("all")
@click.option("--fix", is_flag=True, help="Auto-fix issues")
def lint_all(fix):
    """Run all linting checks and formatting"""
    click.echo("=== Running Ruff Linting ===")
    if fix:
        exit_code_lint = os.system("ruff check --fix app/ tests/")
    else:
        exit_code_lint = os.system("ruff check app/ tests/")

    click.echo("\n=== Running Ruff Format ===")
    if fix:
        exit_code_format = os.system("ruff format app/ tests/")
    else:
        exit_code_format = os.system("ruff format --check app/ tests/")

    click.echo("\n=== Checking Module Boundaries ===")
    exit_code_imports = os.system("lint-imports")

    if exit_code_lint == 0 and exit_code_format == 0 and exit_code_imports == 0:
        click.echo("\n✓ All checks passed!")
        sys.exit(0)
    else:
        if not fix:
            click.echo("\n💡 Tip: Run 'flask lint all --fix' to auto-fix all issues")
        sys.exit(1)


@lint_cli.command("typecheck")
def lint_typecheck():
    """Run mypy type checking"""
    click.echo("Running mypy type checking...")
    exit_code = os.system("mypy app/")
    if exit_code == 0:
        click.echo("✓ Type checking passed!")
    sys.exit(exit_code >> 8)


@lint_cli.command("imports")
def lint_imports():
    """Check module boundary contracts with import-linter"""
    click.echo("Checking module boundaries...")
    exit_code = os.system("lint-imports")
    if exit_code == 0:
        click.echo("✓ Module boundary checks passed!")
    sys.exit(exit_code >> 8)
