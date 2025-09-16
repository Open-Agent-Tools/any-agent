"""Command line interface for Any Agent UI management."""

import click
import json
from pathlib import Path

from .manager import UIBuildManager
from any_agent import __version__


@click.group()
@click.version_option(version=__version__)
def ui_cli() -> None:
    """Any Agent UI Management - Build and manage the React SPA interface."""
    pass


@ui_cli.command()
@click.option(
    "--clean",
    is_flag=True,
    help="Clean existing build artifacts before building",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Verbose output showing build details",
)
def build(clean: bool, verbose: bool) -> None:
    """Build the React SPA UI from source."""
    click.echo("🚀 Any Agent UI Builder")

    # Check prerequisites first
    click.echo("🔍 Checking prerequisites...")
    manager = UIBuildManager()
    prereq_result = manager.check_prerequisites()

    if not prereq_result["success"]:
        click.echo(f"❌ Prerequisites check failed: {prereq_result['error']}")
        click.echo(f"💡 {prereq_result['recommendation']}")
        return

    click.echo(
        f"✅ Node.js {prereq_result['node_version']}, npm {prereq_result['npm_version']}"
    )

    # Clean if requested
    if clean:
        click.echo("🧹 Cleaning existing build artifacts...")
        clean_result = manager.clean_build()
        if clean_result["success"]:
            click.echo("✅ Build artifacts cleaned")
        else:
            click.echo(f"⚠️  Clean failed: {clean_result['error']}")

    # Build the UI
    click.echo("🏗️  Building React SPA...")
    build_result = manager.build_ui()

    if build_result["success"]:
        click.echo("✅ UI build completed successfully!")
        click.echo(f"📁 Output: {build_result['dist_dir']}")
        click.echo(f"📊 Size: {build_result['build_size_mb']} MB")

        if verbose and "stdout" in build_result:
            click.echo("\n📋 Build output:")
            click.echo(build_result["stdout"])

    else:
        click.echo(f"❌ UI build failed: {build_result['error']}")
        if "recommendation" in build_result:
            click.echo(f"💡 {build_result['recommendation']}")

        if verbose and "stdout" in build_result:
            click.echo("\n📋 Build output:")
            click.echo(build_result["stdout"])


@ui_cli.command()
def status() -> None:
    """Show current UI build status and information."""
    click.echo("🚀 Any Agent UI Status")

    manager = UIBuildManager()

    # Check prerequisites
    click.echo("\n🔍 Prerequisites:")
    prereq_result = manager.check_prerequisites()
    if prereq_result["success"]:
        click.echo(f"  ✅ Node.js: {prereq_result['node_version']}")
        click.echo(f"  ✅ npm: {prereq_result['npm_version']}")
    else:
        click.echo(f"  ❌ {prereq_result['error']}")
        click.echo(f"  💡 {prereq_result['recommendation']}")
        return

    # Check build status
    click.echo("\n📦 Build Status:")
    build_info = manager.get_build_info()

    if build_info["built"]:
        click.echo("  ✅ UI is built and ready")
        click.echo(f"  📁 Location: {build_info['dist_dir']}")
        click.echo(f"  📊 Size: {build_info['size_mb']} MB")
        click.echo(f"  📄 Files: {build_info['file_count']}")

        if "package_info" in build_info:
            pkg_info = build_info["package_info"]
            click.echo(f"  📋 Package: {pkg_info['name']} v{pkg_info['version']}")
            click.echo(f"  🔗 Dependencies: {pkg_info['dependencies']}")

    else:
        click.echo("  ❌ UI not built")
        if "error" in build_info:
            click.echo(f"  ⚠️  {build_info['error']}")
        click.echo("  💡 Run 'python -m any_agent.ui build' to build the UI")

    # Show source directory info
    click.echo(f"\n📂 Source: {manager.ui_source_dir}")
    if manager.package_json.exists():
        click.echo("  ✅ package.json found")
    else:
        click.echo("  ❌ package.json not found")


@ui_cli.command()
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force clean without confirmation prompt",
)
def clean(force: bool) -> None:
    """Clean UI build artifacts and dependencies."""
    click.echo("🚀 Any Agent UI Cleaner")

    manager = UIBuildManager()
    build_info = manager.get_build_info()

    if not build_info["built"]:
        click.echo("ℹ️  No build artifacts found to clean")
        return

    # Show what will be cleaned
    click.echo("🗑️  Will clean the following:")
    click.echo(f"  📁 Build directory: {build_info['dist_dir']}")
    click.echo(f"  📊 Size to free: {build_info['size_mb']} MB")

    node_modules = manager.ui_source_dir / "node_modules"
    if node_modules.exists():
        click.echo(f"  📦 Node modules: {node_modules}")

    # Confirm unless force flag is used
    if not force:
        if not click.confirm(
            "⚠️  This will permanently delete build artifacts. Continue?"
        ):
            click.echo("Cleaning cancelled.")
            return

    # Perform cleaning
    click.echo("🧹 Cleaning build artifacts...")
    clean_result = manager.clean_build()

    if clean_result["success"]:
        click.echo("✅ Build artifacts cleaned successfully!")
    else:
        click.echo(f"❌ Cleaning failed: {clean_result['error']}")


@ui_cli.command()
@click.argument(
    "build_context_path", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
def copy(build_context_path: Path) -> None:
    """Copy built UI files to a Docker build context directory."""
    click.echo("🚀 Any Agent UI Copy")

    manager = UIBuildManager()

    # Check if UI is built
    if not manager.is_ui_built():
        click.echo("❌ UI not built - cannot copy files")
        click.echo("💡 Run 'python -m any_agent.ui build' first")
        return

    # Perform copy
    click.echo(f"📁 Copying UI files to: {build_context_path}")
    copy_result = manager.copy_dist_to_context(build_context_path)

    if copy_result["success"]:
        click.echo("✅ UI files copied successfully!")
        click.echo(f"📂 Destination: {copy_result['static_dir']}")
        click.echo(f"📄 Files copied: {copy_result['files_copied']}")
    else:
        click.echo(f"❌ Copy failed: {copy_result['error']}")


@ui_cli.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def info(output_format: str) -> None:
    """Show detailed UI build information."""
    manager = UIBuildManager()

    # Gather all information
    info_data = {
        "prerequisites": manager.check_prerequisites(),
        "build_info": manager.get_build_info(),
        "source_dir": str(manager.ui_source_dir),
        "dist_dir": str(manager.dist_dir),
        "package_json_exists": manager.package_json.exists(),
    }

    if output_format == "json":
        click.echo(json.dumps(info_data, indent=2))
    else:
        # Text format (detailed)
        click.echo("🚀 Any Agent UI - Detailed Information")

        # Prerequisites
        prereq = info_data["prerequisites"]
        click.echo(
            f"\n📋 Prerequisites: {'✅ OK' if prereq['success'] else '❌ FAILED'}"
        )
        if prereq["success"]:
            click.echo(f"  Node.js: {prereq['node_version']}")
            click.echo(f"  npm: {prereq['npm_version']}")
        else:
            click.echo(f"  Error: {prereq['error']}")

        # Build info
        build = info_data["build_info"]
        click.echo(
            f"\n📦 Build Status: {'✅ BUILT' if build['built'] else '❌ NOT BUILT'}"
        )
        if build["built"]:
            click.echo(f"  Size: {build['size_mb']} MB")
            click.echo(f"  Files: {build['file_count']}")
            if "package_info" in build:
                pkg = build["package_info"]
                click.echo(f"  Package: {pkg['name']} v{pkg['version']}")

        # Paths
        click.echo("\n📂 Paths:")
        click.echo(f"  Source: {info_data['source_dir']}")
        click.echo(f"  Build Output: {info_data['dist_dir']}")
        click.echo(
            f"  package.json: {'✅ EXISTS' if info_data['package_json_exists'] else '❌ MISSING'}"
        )


def main() -> None:
    """Entry point for UI CLI."""
    ui_cli()


if __name__ == "__main__":
    main()
