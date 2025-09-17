"""Localhost development orchestrator for Any Agent framework."""

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

from .framework_detector import FrameworkDetector
from .env_loader import EnvironmentLoader
from .port_checker import PortChecker
from .dependency_installer import DependencyInstaller
from .agent_context import AgentContextManager
from ..localhost.fastapi_generator import LocalhostFastAPIGenerator
from ..localhost.server import LocalhostServer
from ..localhost.file_watcher import create_file_watcher
from ..localhost.ui_dev_server import UIDevServerManager
from ..ui.manager import UIBuildManager
from ..shared.url_utils import localhost_urls

logger = logging.getLogger(__name__)


class LocalhostOrchestrator:
    """Separate orchestrator for localhost development mode."""

    def __init__(self):
        """Initialize localhost orchestrator."""
        # Reuse existing components
        self.framework_detector = FrameworkDetector(
            supported_frameworks=["google_adk", "aws_strands"]
        )
        self.env_loader = EnvironmentLoader()
        self.dependency_installer = DependencyInstaller()

        # Localhost-specific components
        self.fastapi_generator = LocalhostFastAPIGenerator()
        self.localhost_server = LocalhostServer()
        self.ui_dev_server = UIDevServerManager()
        self.ui_build_manager = UIBuildManager()
        self.file_watcher = None  # Will be created when needed

        # Store state for hot reload
        self.current_agent_path = None
        self.current_metadata = None
        self.current_output_path = None
        self.current_add_ui = False

    def run_localhost_pipeline(
        self,
        agent_path: str,
        output_dir: Optional[str] = None,
        port: int = 8080,
        helmsman_enabled: bool = False,
        helmsman_url: str = "http://localhost:7080",
        agent_id: Optional[str] = None,
        environment: str = "development",
        add_ui: bool = False,
        enable_hot_reload: bool = True,
    ) -> Dict[str, Any]:
        """
        Run the localhost development pipeline.

        Args:
            agent_path: Path to agent directory
            output_dir: Output directory for build artifacts
            port: Port to run server on
            helmsman_enabled: Enable Helmsman registration
            helmsman_url: Helmsman service URL
            agent_id: Agent identifier
            environment: Environment type
            add_ui: Enable UI integration
            enable_hot_reload: Enable file watching and auto-restart

        Returns:
            Dict with results from localhost pipeline
        """
        results: Dict[str, Any] = {"success": False, "steps": {}}
        agent_path_obj = Path(agent_path)

        try:
            print("🏗️  Starting localhost development pipeline...")

            # Store state for hot reload
            self.current_agent_path = agent_path_obj
            self.current_output_path = (
                Path(output_dir) if output_dir else agent_path_obj / ".any_agent"
            )
            self.current_add_ui = add_ui

            # Step 1: Framework Detection (reuse existing)
            print("🔍 Detecting framework...")
            adapter = self.framework_detector.detect_framework(agent_path_obj)
            if not adapter:
                return {
                    "success": False,
                    "message": "No supported framework detected",
                    "steps": {"detection": {"status": "failed", "framework": None}},
                }

            framework_name = adapter.__class__.__name__.replace("Adapter", "").lower()
            print(f"   Framework detected: {framework_name}")
            results["steps"]["detection"] = {
                "status": "success",
                "framework": framework_name,
            }

            # Step 2: Agent Validation (reuse existing)
            print("✅ Validating agent structure...")
            validation = adapter.validate(agent_path_obj)
            if not validation.is_valid:
                return {
                    "success": False,
                    "message": f"Agent validation failed: {'; '.join(validation.errors)}",
                    "steps": dict(
                        results["steps"],
                        validation={"status": "failed", "errors": validation.errors},
                    ),
                }
            results["steps"]["validation"] = {"status": "success"}

            # Step 3: Install Dependencies (localhost-specific)
            print("📦 Installing agent dependencies...")
            dependency_success = self.dependency_installer.install_agent_dependencies(
                agent_path_obj
            )
            if not dependency_success:
                print("   ⚠️  Warning: Some dependencies could not be installed")
                logger.warning("Dependency installation failed, but continuing...")
            else:
                print("   ✅ Dependencies installed successfully")
            results["steps"]["dependencies"] = {
                "status": "success" if dependency_success else "warning",
                "installed": dependency_success,
            }

            # Step 4: Extract Metadata (reuse existing)
            print("📋 Extracting agent metadata...")
            metadata = adapter.extract_metadata(agent_path_obj)
            self.current_metadata = metadata  # Store for hot reload
            print(f"   Agent: {metadata.name}")
            results["steps"]["metadata"] = {
                "status": "success",
                "agent_name": metadata.name,
            }

            # Initialize context for localhost deployment
            context_manager = AgentContextManager(agent_path_obj)
            context_manager.update_build_info(
                agent_name=metadata.name,
                framework=adapter.__class__.__name__.replace("Adapter", "").lower(),
                deployment_type="localhost",
                model=getattr(metadata, 'model', None)
            )

            # Step 5: Load Environment (reuse existing, but make optional for localhost)
            print("🌍 Loading environment variables...")
            try:
                env_vars = self.env_loader.load_env_with_priority(agent_path_obj)
                print(f"   Loaded {len(env_vars)} environment variables")
            except RuntimeError as e:
                if "No .env file found" in str(e):
                    print("   No .env file found - using system environment only")
                    env_vars = dict(os.environ)  # Use system environment
                    print(f"   Using {len(env_vars)} system environment variables")
                else:
                    raise
            results["steps"]["environment"] = {"status": "success"}

            # Step 6: Generate FastAPI App (localhost-specific)
            print("🏗️  Generating FastAPI application...")
            output_path = (
                Path(output_dir) if output_dir else agent_path_obj / ".any_agent"
            )
            app_file = self.fastapi_generator.generate_fastapi_app(
                agent_path_obj, metadata, output_path, add_ui, port
            )
            print(f"   Generated: {app_file}")
            results["steps"]["fastapi_generation"] = {
                "status": "success",
                "app_file": str(app_file),
            }

            # Step 6: Port Availability Check
            print(f"🔌 Checking port {port} availability...")
            port_checker = PortChecker()
            if not port_checker.is_port_available(port):
                return {
                    "success": False,
                    "message": f"Port {port} is already in use",
                    "steps": dict(
                        results["steps"],
                        port_check={
                            "status": "failed",
                            "port": port,
                            "error": "Port unavailable",
                        },
                    ),
                    "recommendation": "Try a different port with --port flag or stop the service using the port",
                }

            results["steps"]["port_check"] = {"status": "success", "port": port}
            print(f"   ✅ Port {port} is available")

            # Step 7: Start Localhost Server with Hot Reload (localhost-specific)
            print(f"🚀 Starting localhost server on port {port}...")

            # Create restart callback for hot reload
            def regenerate_app():
                """Regenerate FastAPI app when files change."""
                try:
                    print("🏗️  Regenerating FastAPI app due to file changes...")
                    new_app_file = self.fastapi_generator.generate_fastapi_app(
                        self.current_agent_path,
                        self.current_metadata,
                        self.current_output_path,
                        self.current_add_ui,
                        port,  # Pass the current port
                    )
                    print(f"   ✅ Regenerated: {new_app_file}")
                except Exception as e:
                    print(f"   ❌ Regeneration failed: {e}")
                    logger.error(f"App regeneration failed: {e}")
                    raise

            server_started = self.localhost_server.start_server(
                app_file,
                port,
                restart_callback=regenerate_app if enable_hot_reload else None,
            )

            if not server_started:
                return {
                    "success": False,
                    "message": "Failed to start localhost server",
                    "steps": dict(results["steps"], server={"status": "failed"}),
                }

            results["steps"]["server"] = {"status": "success", "port": port}

            # Step 8: Wait and check server status
            print("⏳ Waiting for server to start...")
            time.sleep(2)  # Give server time to start

            if self.localhost_server.is_running():
                print("✅ Server is running!")
                print(f"   🌐 Agent URL: http://localhost:{port}/")
                print(f"   🏥 Health Check: {localhost_urls.health_url(port)}")
                print(f"   📋 Agent Card: {localhost_urls.agent_card_url(port)}")

                # Update context with localhost server information for safe removal
                try:
                    context_manager = AgentContextManager(agent_path_obj)
                    if self.localhost_server.process:
                        context_manager.update_localhost_server(
                            pid=self.localhost_server.process.pid,
                            port=port,
                            host="localhost",
                            app_file_path=str(app_file),
                            working_directory=str(app_file.parent),
                            command_line=f"uvicorn localhost_app:app --host localhost --port {port}"
                        )
                        print("   📝 Updated context with server information")
                except Exception as context_error:
                    logger.warning(f"Failed to update context with server info: {context_error}")

                # Step 9: Setup File Watching for Hot Reload
                if enable_hot_reload:
                    print("👀 Setting up file watching for hot reload...")
                    self.file_watcher = create_file_watcher(
                        agent_path_obj, lambda: self.localhost_server.restart_server()
                    )

                    if self.file_watcher.start_watching():
                        print("   ✅ File watching enabled")
                        results["steps"]["file_watcher"] = {"status": "success"}
                    else:
                        print("   ⚠️  File watching failed to start")
                        results["steps"]["file_watcher"] = {"status": "failed"}

                # Step 10: UI Integration (always use production build in single-port mode)
                if add_ui:
                    print("🏭 Setting up UI integration...")
                    # Check if UI is already built
                    if self.ui_build_manager.is_ui_built():
                        print("   ✅ Production UI build found")
                        build_info = self.ui_build_manager.get_build_info()
                        print(
                            f"   📦 Size: {build_info.get('size_mb', 0)} MB, {build_info.get('file_count', 0)} files"
                        )

                        # Copy UI files to agent output directory for serving
                        ui_copy_result = self.ui_build_manager.copy_dist_to_context(
                            self.current_output_path
                        )
                        if ui_copy_result["success"]:
                            print(
                                f"   📁 UI files copied to {ui_copy_result['static_dir']}"
                            )
                            results["steps"]["ui_production"] = {
                                "status": "success",
                                "static_dir": ui_copy_result["static_dir"],
                                "build_info": build_info,
                            }
                        else:
                            print(
                                f"   ⚠️  Failed to copy UI files: {ui_copy_result.get('error')}"
                            )
                            results["steps"]["ui_production"] = {
                                "status": "failed",
                                "error": ui_copy_result.get("error"),
                            }
                    else:
                        print("   ⚠️  Production UI not built - building now...")
                        build_result = self.ui_build_manager.build_ui()

                        if build_result["success"]:
                            print(
                                f"   ✅ UI built successfully ({build_result.get('build_size_mb', 0)} MB)"
                            )

                            # Copy to output directory
                            ui_copy_result = self.ui_build_manager.copy_dist_to_context(
                                self.current_output_path
                            )
                            if ui_copy_result["success"]:
                                print(
                                    f"   📁 UI files copied to {ui_copy_result['static_dir']}"
                                )
                                results["steps"]["ui_production"] = {
                                    "status": "success",
                                    "static_dir": ui_copy_result["static_dir"],
                                    "build_result": build_result,
                                }
                            else:
                                print(
                                    f"   ⚠️  Failed to copy UI files: {ui_copy_result.get('error')}"
                                )
                                results["steps"]["ui_production"] = {
                                    "status": "failed",
                                    "error": ui_copy_result.get("error"),
                                }
                        else:
                            print(
                                f"   ⚠️  UI build failed: {build_result.get('error', 'Unknown error')}"
                            )
                            results["steps"]["ui_production"] = {
                                "status": "failed",
                                "error": build_result.get("error"),
                            }

                results["success"] = True
                results["message"] = "Localhost development server started successfully"
                results["url"] = localhost_urls.ui_url(port, "/")
                if enable_hot_reload:
                    results["hot_reload"] = "enabled"

            else:
                # Get any error output
                error_output = self.localhost_server.get_server_output(timeout=0.5)
                error_msg = "Server process stopped unexpectedly"
                if error_output:
                    error_msg += f": {error_output}"

                return {
                    "success": False,
                    "message": error_msg,
                    "steps": dict(
                        results["steps"],
                        server={"status": "failed", "error": error_output},
                    ),
                }

        except Exception as e:
            logger.error(f"Localhost pipeline failed: {e}")
            return {
                "success": False,
                "message": f"Pipeline error: {str(e)}",
                "steps": results.get("steps", {}),
            }

        return results

    def cleanup(self):
        """Clean up resources (file watcher, server, etc.)."""
        if self.file_watcher:
            print("🧹 Cleaning up file watcher...")
            self.file_watcher.stop_watching()
            self.file_watcher = None

        if self.ui_dev_server and self.ui_dev_server.is_running:
            print("🧹 Stopping React dev server...")
            self.ui_dev_server.stop_dev_server()

        if self.localhost_server:
            print("🧹 Stopping localhost server...")
            self.localhost_server.stop_server()

    def __del__(self):
        """Ensure cleanup on object destruction."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore cleanup errors during destruction
