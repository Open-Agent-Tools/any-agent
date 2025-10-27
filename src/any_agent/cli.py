"""Command line interface for Any Agent framework."""

import click
import json
import logging
from pathlib import Path
from typing import Optional

from . import __version__
from .core.docker_orchestrator import AgentOrchestrator
from .core.localhost_orchestrator import LocalhostOrchestrator
from .core.port_checker import PortChecker
from .ui.manager import UIBuildManager
from .shared.url_utils import localhost_urls


@click.command()
@click.argument("agent_path", type=click.Path(path_type=Path), required=False)
@click.help_option("-h", "--help")
@click.option(
    "-d",
    "--directory",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Agent directory path",
)
@click.option(
    "-f",
    "--framework",
    type=click.Choice(["auto", "adk", "aws-strands", "langchain", "crewai"]),
    default="auto",
    help="Force specific framework detection. Use 'adk' for Google ADK agents (default: auto)",
)
@click.option(
    "--port",
    type=int,
    default=None,
    help="Port for the containerized agent (default: framework-specific)",
)
@click.option("--container-name", type=str, help="Custom name for the container")
@click.option(
    "--no-build",
    is_flag=True,
    help="Skip building Docker image (default: build enabled)",
)
@click.option(
    "--no-run",
    is_flag=True,
    help="Skip running container after building (default: run enabled)",
)
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Configuration file path",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    help="Output directory for generated files",
)
@click.option(
    "--agent-name",
    type=str,
    help="Unique agent identifier for Docker naming",
)
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
@click.option("--version", is_flag=True, help="Show version and exit")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without executing"
)
@click.option(
    "--no-ui",
    is_flag=True,
    help="Disable web UI landing page (default: UI enabled)",
)
@click.option(
    "--skip-a2a-test",
    is_flag=True,
    help="Skip A2A protocol testing in end-to-end tests",
)
@click.option(
    "--a2a-test-timeout",
    type=int,
    default=30,
    help="Timeout for A2A protocol tests in seconds (default: 30)",
)
@click.option(
    "--rebuild-ui",
    is_flag=True,
    help="Force rebuild of React SPA UI even if already built",
)
@click.option(
    "--base-image",
    type=str,
    help="Custom Docker base image (default: python:3.11-slim)",
)
@click.option(
    "--localhost",
    is_flag=True,
    help="Enable localhost development mode (no Docker required)",
)
@click.option(
    "--no-hot-reload",
    is_flag=True,
    help="Disable file watching and hot reload in localhost mode",
)
@click.option(
    "-r",
    "--remove",
    is_flag=True,
    help="Remove all instances of agent from Docker",
)
@click.option(
    "-y",
    "--yes-to-all",
    is_flag=True,
    help="Skip confirmation prompts (use with --remove for non-interactive removal)",
)
@click.option(
    "--package-mac",
    is_flag=True,
    help="Create macOS desktop application bundle (.dmg installer)",
)
@click.option(
    "--test",
    is_flag=True,
    help="Test packaged app locally without creating installer (use with --package-mac)",
)
def main(
    agent_path: Optional[Path],
    directory: Optional[Path],
    framework: str,
    port: int,
    container_name: Optional[str],
    no_build: bool,
    no_run: bool,
    config: Optional[Path],
    output: Optional[Path],
    agent_name: Optional[str],
    verbose: bool,
    version: bool,
    dry_run: bool,
    no_ui: bool,
    skip_a2a_test: bool,
    a2a_test_timeout: int,
    rebuild_ui: bool,
    base_image: Optional[str],
    localhost: bool,
    no_hot_reload: bool,
    remove: bool,
    yes_to_all: bool,
    package_mac: bool,
    test: bool,
) -> None:
    """Any Agent - Universal AI Agent Containerization Framework.

    Automatically containerize AI agents from any framework into standardized,
    protocol-compliant Docker containers with A2A protocol support.

    AGENT_PATH: Path to agent directory (Google ADK, AWS Strands, etc.)

    \b
    Examples:
      # Auto-detect and containerize any agent
      python -m any_agent ./my_agent

      # Google ADK agent with custom name
      python -m any_agent ./adk_agent --framework adk --agent-name my-adk-agent

      # Test mode - see what would happen
      python -m any_agent ./my_agent --dry-run

      # Remove deployed agent
      python -m any_agent ./my_agent --remove
    """
    # Handle version flag first
    if version:
        click.echo(f"any-agent {__version__}")
        return

    # Handle packaging operations (before other validations)
    if package_mac:
        click.echo("📦 Any Agent Framework - Desktop Packaging")
        click.echo(f"📂 Agent Path: {agent_path}")

        # Validate agent_path is provided
        if agent_path is None:
            click.echo("Error: Missing argument 'AGENT_PATH' for packaging.")
            raise click.Abort()

        if not agent_path.exists():
            click.echo(f"Error: Path '{agent_path}' does not exist.")
            raise click.Abort()

        try:
            from .packaging.mac_packager import MacAppPackager

            packager = MacAppPackager()
            result = packager.package(
                agent_path=agent_path,
                test_mode=test,
                verbose=verbose,
            )

            if result["success"]:
                click.echo("\n✅ Packaging completed successfully!")
                if test:
                    click.echo(f"🧪 Test app launched at: {result.get('app_path', 'N/A')}")
                else:
                    click.echo(f"📦 Installer created at: {result.get('dmg_path', 'N/A')}")
            else:
                click.echo(f"\n❌ Packaging failed: {result.get('error', 'Unknown error')}")

        except ImportError:
            click.echo("❌ Packaging module not available. This feature may not be implemented yet.")
        except Exception as e:
            click.echo(f"❌ Packaging failed: {e}")
            if verbose:
                import traceback
                traceback.print_exc()

        return

    # Handle removal operations first (before other validations)
    if remove:
        click.echo("🚀 Any Agent Framework - Agent Removal")
        click.echo(f"📂 Agent Path: {agent_path}")

        try:
            from .core.agent_remover import AgentRemover
            from .core.agent_context import AgentContextManager

            remover = AgentRemover()
            context_manager = AgentContextManager(agent_path) if agent_path else None

            # Get agent name from context or use provided name
            detected_agent_name = (
                context_manager.get_agent_name() if context_manager else None
            )
            final_agent_name = agent_name or detected_agent_name

            if not final_agent_name and agent_path:
                # Try to extract from directory if no context or explicit name
                try:
                    temp_orchestrator = AgentOrchestrator()
                    adapter = temp_orchestrator.detect_framework(agent_path)
                    if adapter:
                        metadata = temp_orchestrator.extract_metadata(
                            agent_path, adapter
                        )
                        final_agent_name = metadata.name
                except Exception:
                    pass

            if not final_agent_name and agent_path:
                final_agent_name = agent_path.name

            # Remove mode - confirm and remove
            if not final_agent_name:
                click.echo(
                    "❌ Could not determine agent name. Please use --agent-name to specify explicitly."
                )
                return

            artifacts = remover.find_agent_artifacts(final_agent_name, context_manager)
            if not artifacts.has_artifacts:
                click.echo(f"No artifacts found for agent '{final_agent_name}'")
                return

            # Show what will be removed
            click.echo(f"🔍 Agent: {final_agent_name}")
            click.echo("Found artifacts to remove:")
            summary = artifacts.summary
            if summary["containers"]:
                status_text = []
                for container in artifacts.containers:
                    status_text.append(f"{container.get('status', 'unknown')}")
                click.echo(
                    f"  🐳 Docker containers: {summary['containers']} ({', '.join(status_text)})"
                )
            if summary["images"]:
                total_size = sum(img.get("size", 0) for img in artifacts.images)
                size_gb = total_size / (1024**3) if total_size > 0 else 0
                click.echo(f"  📦 Docker images: {summary['images']} ({size_gb:.2f}GB)")
            if summary["build_contexts"]:
                click.echo(f"  🗑️  Build contexts: {summary['build_contexts']}")

            # Confirmation prompt (skip if --yes-to-all is used)
            if not yes_to_all:
                if not click.confirm(
                    f"\n⚠️  This will permanently remove all traces of '{final_agent_name}'. Continue?"
                ):
                    click.echo("Removal cancelled.")
                    return

            # Perform removal
            click.echo("🗑️  Removing artifacts...")
            report = remover.remove_agent(
                final_agent_name, context_manager, force=yes_to_all
            )

            # Report results
            if report.success:
                click.echo(f"✅ Successfully removed agent '{final_agent_name}'")
                if report.total_removed > 0:
                    click.echo(f"   Removed {report.total_removed} artifacts")
            else:
                click.echo(f"❌ Removal completed with {report.total_failed} failures")

            if report.errors:
                for error in report.errors:
                    click.echo(f"   Error: {error}")

            return

        except Exception as e:
            click.echo(f"❌ Removal failed: {e}")
            if verbose:
                import traceback

                traceback.print_exc()
            return

    # Check if agent_path is required but not provided
    if agent_path is None:
        click.echo("Error: Missing argument 'AGENT_PATH'.")
        raise click.Abort()

    # Validate that the agent path exists
    if not agent_path.exists():
        click.echo(f"Error: Path '{agent_path}' does not exist.")
        raise click.Abort()

    # Setup logging
    if verbose:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
    else:
        logging.basicConfig(level=logging.WARNING)

    # Use directory if provided, otherwise use agent_path
    target_path = directory or agent_path

    # Dynamic port selection based on framework (do this early so dry-run shows correct port)
    if port is None:
        # Quick framework detection for port selection
        temp_orchestrator = AgentOrchestrator()
        adapter = temp_orchestrator.detect_framework(target_path)
        if adapter:
            framework_name = adapter.__class__.__name__.lower().replace("adapter", "")
            framework_configs = {
                "googleadk": 8035,
                "awsstrands": 8045,
                "langchain": 8055,
                "crewai": 8065,
                "langgraph": 8075,
                "generic": 8085,
            }
            port = framework_configs.get(framework_name, 8080)  # fallback to 8080
            if verbose:
                click.echo(
                    f"🔌 Using framework-specific default port: {port} (detected: {framework_name})"
                )
        else:
            port = 8080  # ultimate fallback
            if verbose:
                click.echo(f"🔌 No framework detected, using fallback port: {port}")

    # Removal/Helmsman functionality has been deprecated and removed

    # Pipeline divergence point - localhost vs Docker
    if localhost:
        click.echo("🏠 Any Agent Framework - Localhost Development Mode")
        click.echo(f"📂 Agent Path: {target_path}")

        # Initialize localhost orchestrator
        localhost_orchestrator = LocalhostOrchestrator()

        try:
            # Run localhost pipeline
            results = localhost_orchestrator.run_localhost_pipeline(
                agent_path=str(target_path),
                output_dir=str(output) if output else None,
                port=port,
                agent_id=agent_name,
                environment="development",
                add_ui=not no_ui,
                enable_hot_reload=not no_hot_reload,
            )

            if results["success"]:
                click.echo("✅ Localhost development server started!")
                click.echo(
                    f"   🌐 Server: {results.get('url', f'http://localhost:{port}/')}"
                )

            else:
                click.echo(
                    f"❌ Localhost setup failed: {results.get('message', 'Unknown error')}"
                )

        except Exception as e:
            click.echo(f"💥 Localhost pipeline failed with exception: {e}")
            if verbose:
                import traceback

                traceback.print_exc()

        return

    # Normal Docker pipeline execution
    click.echo("🚀 Any Agent Framework - MVP Pipeline")
    click.echo(f"📂 Agent Path: {target_path}")

    # Quick port availability check for immediate feedback
    if not dry_run:
        click.echo(f"🔌 Checking port {port} availability...")
        if not PortChecker.is_port_available(port):
            port_info = PortChecker.get_port_info(port)
            error_msg = f"❌ Port {port} is not available"
            if port_info.get("status") == "in_use":
                error_msg += " (already in use)"
            elif port_info.get("status") == "permission_denied":
                error_msg += " (permission denied - try a port > 1024)"

            # Suggest alternative ports
            alternative_port = PortChecker.find_available_port(port + 1, port + 100)
            if alternative_port:
                error_msg += f". Try --port {alternative_port}"
            else:
                error_msg += ". Try a different port number"

            click.echo(error_msg)
            return
        click.echo(f"✅ Port {port} is available")

    if dry_run:
        click.echo("DRY RUN - Would execute the following:")
        click.echo(f"0. Check port {port} availability")
        click.echo(f"1. Detect framework in: {target_path}")
        click.echo("2. Validate agent structure")
        click.echo("3. Extract metadata")
        click.echo("4. Create Docker image")
        click.echo(f"5. Start container on port {port}")
        click.echo("6. Health check")
        click.echo("7. Test agent self-description")
        return

    # Handle UI build if needed (and UI is enabled)
    if not no_ui:
        ui_manager = UIBuildManager()

        # Check if UI build is needed
        if ui_manager.should_rebuild_ui(force_rebuild=rebuild_ui):
            click.echo("🎨 Building React SPA UI...")

            # Check prerequisites first
            prereq_result = ui_manager.check_prerequisites()
            if not prereq_result["success"]:
                click.echo(
                    f"❌ UI build prerequisites not met: {prereq_result['error']}"
                )
                click.echo(f"💡 {prereq_result['recommendation']}")
                click.echo("⚠️  Continuing without UI rebuild...")
            else:
                # Build the UI
                build_result = ui_manager.build_ui()
                if build_result["success"]:
                    if "message" in build_result:
                        # PyPI installation with pre-built assets
                        click.echo(f"✅ {build_result['message']}")
                    else:
                        # Fresh build from source
                        click.echo(
                            f"✅ UI built successfully ({build_result['build_size_mb']} MB)"
                        )
                else:
                    click.echo(f"❌ UI build failed: {build_result['error']}")
                    if "recommendation" in build_result:
                        click.echo(f"💡 {build_result['recommendation']}")
                    click.echo("⚠️  Continuing without UI rebuild...")
        else:
            click.echo("✅ UI already built - using existing build")

    # Initialize orchestrator
    orchestrator = AgentOrchestrator()

    try:
        # Run the full MVP pipeline
        results = orchestrator.run_full_pipeline(
            agent_path=str(target_path),
            output_dir=str(output) if output else None,
            port=port,
            build=not no_build,  # Default True, disabled by --no-build
            run=not no_run,  # Default True, disabled by --no-run
            add_ui=not no_ui,  # UI enabled by default, disabled with --no-ui
            skip_a2a_test=skip_a2a_test,
            a2a_test_timeout=a2a_test_timeout,
            base_image=base_image,
        )

        # Display results
        if results["success"]:
            click.echo("\n✅ MVP Pipeline completed successfully!")

            # Show key results
            if "port_check" in results["steps"]:
                port_info = results["steps"]["port_check"]
                click.echo(f"🔌 Port: {port_info['port']} (available)")

            if "detection" in results["steps"]:
                framework = results["steps"]["detection"]["framework"]
                click.echo(f"🔍 Framework: {framework}")

            if "metadata" in results["steps"]:
                metadata = results["steps"]["metadata"]
                click.echo(f"🤖 Agent: {metadata['agent_name']}")
                if metadata.get("model"):
                    click.echo(f"🧠 Model: {metadata['model']}")

            if "container_start" in results["steps"]:
                container_info = results["steps"]["container_start"]
                if (
                    not container_info.get("skipped")
                    and "container_id" in container_info
                ):
                    click.echo(f"🐳 Container: {container_info['container_id'][:12]}")
                    click.echo(f"🌐 Port: {container_info['port']}")
                elif container_info.get("skipped"):
                    click.echo(
                        f"⏭️  Container startup skipped: {container_info.get('reason', 'Unknown reason')}"
                    )

            # Show test results
            if "e2e_test" in results["steps"]:
                e2e_test_step = results["steps"]["e2e_test"]
                if e2e_test_step.get("skipped"):
                    click.echo("\n🧪 End-to-End Tests: SKIPPED")
                    click.echo(
                        f"   Reason: {e2e_test_step.get('reason', 'Unknown reason')}"
                    )
                elif "test_results" in e2e_test_step:
                    test_results = e2e_test_step["test_results"]
                    click.echo("\n🧪 Test Results:")

                    # HTTP Tests
                    http_tests = test_results.get("http_tests", {})
                    if http_tests:
                        # Health check
                        health = http_tests.get("health_check", {})
                        if "error" not in health:
                            click.echo("  ✅ Health check: PASSED")
                        else:
                            click.echo(f"  ❌ Health check: {health['error']}")

                        # Agent description
                        describe = http_tests.get("describe", {})
                        if "error" not in describe:
                            if describe.get("ui_enabled"):
                                click.echo("  ✅ Agent description: UI AVAILABLE")
                            else:
                                click.echo("  ✅ Agent description: AVAILABLE")
                                if verbose and describe.get("name"):
                                    click.echo(f"     Name: {describe['name']}")
                                    click.echo(
                                        f"     Framework: {describe.get('framework', 'unknown')}"
                                    )
                        else:
                            click.echo(f"  ❌ Agent description: {describe['error']}")

                        # Agent card test
                        agent_card = http_tests.get("agent_card", {})
                        if "error" not in agent_card:
                            click.echo("  ✅ Agent card: AVAILABLE")
                            if verbose:
                                click.echo(
                                    "     Status: Valid JSON structure with required fields"
                                )
                                if agent_card.get("name"):
                                    click.echo(
                                        f"     Agent name found: {agent_card['name']}"
                                    )
                                if agent_card.get("version"):
                                    click.echo(
                                        f"     Version specified: {agent_card['version']}"
                                    )
                                capabilities = agent_card.get("capabilities", [])
                                if capabilities:
                                    click.echo(
                                        f"     Capabilities: {len(capabilities)} declared"
                                    )
                        else:
                            click.echo(f"  ❌ Agent card: {agent_card['error']}")

                    # A2A Protocol Tests
                    a2a_tests = test_results.get("a2a_tests", {})
                    if a2a_tests:
                        if a2a_tests.get("skipped"):
                            click.echo("  ⏭️  A2A protocol tests: SKIPPED")
                            if verbose:
                                click.echo(
                                    f"     Reason: {a2a_tests.get('reason', 'Unknown')}"
                                )
                        elif a2a_tests.get("success"):
                            summary = a2a_tests.get("summary", {})
                            total = summary.get("total", 0)
                            passed = summary.get("passed", 0)
                            duration_ms = summary.get("duration_ms", 0)

                            click.echo(
                                f"  ✅ A2A protocol tests: PASSED ({passed}/{total})"
                            )
                            if verbose:
                                click.echo(f"     Duration: {duration_ms:.1f}ms")
                                for test in a2a_tests.get("tests", []):
                                    status = "✅" if test["success"] else "❌"
                                    click.echo(
                                        f"     {status} {test['scenario']}: {test.get('duration_ms', 0):.1f}ms"
                                    )
                        else:
                            error = a2a_tests.get("error", "Unknown error")
                            click.echo("  ❌ A2A protocol tests: FAILED")
                            if verbose:
                                click.echo(f"     Error: {error}")
                                if a2a_tests.get("recommendation"):
                                    click.echo(
                                        f"     Recommendation: {a2a_tests['recommendation']}"
                                    )

                    # UI Availability Tests
                    ui_tests = test_results.get("ui_tests", {})
                    if ui_tests:
                        if ui_tests.get("success"):
                            click.echo("  ✅ UI availability: PASSED")
                            if verbose:
                                initial = ui_tests.get("initial_load", {})
                                if initial.get("load_time_ms"):
                                    click.echo(
                                        f"     Load time: {initial['load_time_ms']:.1f}ms"
                                    )
                                if ui_tests.get("retry_load") and not ui_tests[
                                    "initial_load"
                                ].get("has_react_root"):
                                    click.echo(
                                        "     ⚠️  Required retry after initial failure"
                                    )
                        else:
                            click.echo("  ❌ UI availability: FAILED")
                            if verbose:
                                initial = ui_tests.get("initial_load", {})
                                retry = ui_tests.get("retry_load", {})

                                if initial.get("error"):
                                    click.echo(
                                        f"     Initial load error: {initial['error']}"
                                    )
                                elif not initial.get("has_react_root"):
                                    click.echo(
                                        "     Issue: React root element not found"
                                    )
                                elif not initial.get("has_js_assets"):
                                    click.echo(
                                        "     Issue: JavaScript assets not found"
                                    )

                                if retry.get("has_react_root") and retry.get(
                                    "has_js_assets"
                                ):
                                    click.echo(
                                        "     Note: UI works after retry - timing issue detected"
                                    )

                                if ui_tests.get("error"):
                                    click.echo(f"     Error: {ui_tests['error']}")
                    else:
                        # Backward compatibility: show old format tests
                        # Health check
                        health = test_results.get("health_check", {})
                        if "error" not in health:
                            click.echo("  ✅ Health check: PASSED")
                        else:
                            click.echo(f"  ❌ Health check: {health['error']}")

                        # Agent description
                        describe = test_results.get("describe", {})
                        if "error" not in describe:
                            if describe.get("ui_enabled"):
                                click.echo("  ✅ Agent description: UI AVAILABLE")
                            else:
                                click.echo("  ✅ Agent description: AVAILABLE")
                        else:
                            click.echo(f"  ❌ Agent description: {describe['error']}")

                        # Agent card test
                        agent_card = test_results.get("agent_card", {})
                        if "error" not in agent_card:
                            click.echo("  ✅ Agent card: AVAILABLE")
                        else:
                            click.echo(f"  ❌ Agent card: {agent_card['error']}")

            # Show appropriate endpoint based on UI setting
            if not no_ui:
                click.echo(f"\n🎉 Agent is ready! Visit: http://localhost:{port}/")
                click.echo(f"   Health check: curl {localhost_urls.health_url(port)}")
            else:
                click.echo(
                    f"\n🎉 Agent is ready! Try: curl {localhost_urls.health_url(port)}"
                )

        else:
            click.echo("\n❌ MVP Pipeline failed!")
            if "error" in results:
                click.echo(f"Error: {results['error']}")

            # Show step details
            for step_name, step_result in results.get("steps", {}).items():
                if "error" in step_result:
                    click.echo(f"  ❌ {step_name}: {step_result['error']}")

                    # Special handling for port check errors
                    if step_name == "port_check" and "suggested_port" in step_result:
                        suggested = step_result["suggested_port"]
                        if suggested:
                            click.echo(f"      💡 Suggestion: Try --port {suggested}")
                        else:
                            click.echo("      💡 Suggestion: Choose a different port")

                elif step_result.get("success"):
                    click.echo(f"  ✅ {step_name}: PASSED")

        # Optionally save full results
        if verbose and output:
            results_file = Path(output) / "pipeline_results.json"
            results_file.parent.mkdir(parents=True, exist_ok=True)
            with open(results_file, "w") as f:
                json.dump(results, f, indent=2)
            click.echo(f"\n📄 Full results saved to: {results_file}")

    except Exception as e:
        click.echo(f"\n💥 Pipeline failed with exception: {e}")
        if verbose:
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    main()
