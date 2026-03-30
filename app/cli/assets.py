"""Asset building CLI commands."""

import os
import sys

import click

assets_cli = click.Group("assets", help="Asset building commands")


@assets_cli.command("build")
def assets_build():
    """Build production assets with Vite"""
    click.echo("Building production assets...")
    exit_code = os.system("npm run build")
    if exit_code == 0:
        click.echo("✓ Assets built successfully!")
    sys.exit(exit_code >> 8)


@assets_cli.command("watch")
def assets_watch():
    """Watch and rebuild assets on change"""
    click.echo("Starting Vite dev server...")
    exit_code = os.system("npm run dev")
    sys.exit(exit_code >> 8)
