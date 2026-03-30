"""Testing CLI commands."""

import os
import sys

import click

test_cli = click.Group("test", help="Testing commands")


@test_cli.command("run")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("-c", "--coverage", is_flag=True, help="Run with coverage report")
@click.option("-k", "--keyword", help="Run tests matching keyword")
def test_run(verbose, coverage, keyword):
    """Run test suite"""
    cmd = "pytest"

    if verbose:
        cmd += " -v"

    if coverage:
        cmd += " --cov=app --cov-report=term-missing --no-cov-on-fail"

    if keyword:
        cmd += f' -k "{keyword}"'

    click.echo(f"Running: {cmd}")
    exit_code = os.system(cmd)
    sys.exit(exit_code >> 8)


@test_cli.command("file")
@click.argument("filepath")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
def test_file(filepath, verbose):
    """Run specific test file"""
    cmd = f"pytest {filepath}"
    if verbose:
        cmd += " -v"

    click.echo(f"Running: {cmd}")
    exit_code = os.system(cmd)
    sys.exit(exit_code >> 8)


@test_cli.command("coverage")
def test_coverage():
    """Run tests with coverage report"""
    click.echo("Running tests with coverage...")
    os.system("pytest --cov=app --cov-report=term-missing --cov-report=html")
    click.echo("\nHTML coverage report generated in htmlcov/")
