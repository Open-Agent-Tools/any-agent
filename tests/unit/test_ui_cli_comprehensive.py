"""Comprehensive UI CLI test suite for command-line interface coverage."""

import json
from pathlib import Path
from unittest.mock import Mock, patch
from click.testing import CliRunner

from any_agent.ui.cli import ui_cli, build, status, clean, copy, info


class TestUICLIComprehensive:
    """Comprehensive tests for UI CLI commands."""

    def test_ui_cli_main_group(self):
        """Test main UI CLI group command."""
        runner = CliRunner()
        result = runner.invoke(ui_cli, ["--help"])

        assert result.exit_code == 0
        assert "Any Agent UI Management" in result.output

    @patch("any_agent.ui.cli.UIBuildManager")
    def test_build_command_prerequisites_failure(self, mock_manager_class):
        """Test build command when prerequisites check fails."""
        runner = CliRunner()

        # Mock manager with failed prerequisites
        mock_manager = Mock()
        mock_manager.check_prerequisites.return_value = {
            "success": False,
            "error": "Node.js not found",
            "recommendation": "Install Node.js 18+",
        }
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(build)

        assert result.exit_code == 0
        assert "Prerequisites check failed" in result.output
        assert "Node.js not found" in result.output

    @patch("any_agent.ui.cli.UIBuildManager")
    def test_build_command_success_verbose(self, mock_manager_class):
        """Test build command successful execution with verbose output."""
        runner = CliRunner()

        # Mock manager with successful operations
        mock_manager = Mock()
        mock_manager.check_prerequisites.return_value = {
            "success": True,
            "node_version": "v18.17.0",
            "npm_version": "9.6.7",
        }
        mock_manager.build_ui.return_value = {
            "success": True,
            "dist_dir": "/path/to/dist",
            "build_size_mb": 2.5,
            "stdout": "Build completed successfully",
        }
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(build, ["--verbose"])

        assert result.exit_code == 0
        assert "UI build completed successfully" in result.output
        assert "Build completed successfully" in result.output  # verbose output

    @patch("any_agent.ui.cli.UIBuildManager")
    def test_build_command_with_clean(self, mock_manager_class):
        """Test build command with clean flag."""
        runner = CliRunner()

        # Mock manager
        mock_manager = Mock()
        mock_manager.check_prerequisites.return_value = {
            "success": True,
            "node_version": "v18.17.0",
            "npm_version": "9.6.7",
        }
        mock_manager.clean_build.return_value = {
            "success": True,
            "message": "Cleaned successfully",
        }
        mock_manager.build_ui.return_value = {
            "success": True,
            "dist_dir": "/path/to/dist",
            "build_size_mb": 1.8,
        }
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(build, ["--clean"])

        assert result.exit_code == 0
        assert "Build artifacts cleaned" in result.output
        mock_manager.clean_build.assert_called_once()

    @patch("any_agent.ui.cli.UIBuildManager")
    def test_build_command_clean_failure(self, mock_manager_class):
        """Test build command when clean fails."""
        runner = CliRunner()

        # Mock manager
        mock_manager = Mock()
        mock_manager.check_prerequisites.return_value = {
            "success": True,
            "node_version": "v18.17.0",
            "npm_version": "9.6.7",
        }
        mock_manager.clean_build.return_value = {
            "success": False,
            "error": "Permission denied",
        }
        mock_manager.build_ui.return_value = {
            "success": True,
            "dist_dir": "/path/to/dist",
            "build_size_mb": 1.8,
        }
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(build, ["--clean"])

        assert result.exit_code == 0
        assert "Clean failed" in result.output
        assert "Permission denied" in result.output

    @patch("any_agent.ui.cli.UIBuildManager")
    def test_build_command_build_failure_verbose(self, mock_manager_class):
        """Test build command when build fails with verbose output."""
        runner = CliRunner()

        # Mock manager
        mock_manager = Mock()
        mock_manager.check_prerequisites.return_value = {
            "success": True,
            "node_version": "v18.17.0",
            "npm_version": "9.6.7",
        }
        mock_manager.build_ui.return_value = {
            "success": False,
            "error": "Build failed",
            "recommendation": "Check TypeScript errors",
            "stdout": "Compilation errors found",
        }
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(build, ["--verbose"])

        assert result.exit_code == 0
        assert "UI build failed" in result.output
        assert "Build failed" in result.output
        assert "Check TypeScript errors" in result.output
        assert "Compilation errors found" in result.output

    @patch("any_agent.ui.cli.UIBuildManager")
    def test_status_command_prerequisites_failure(self, mock_manager_class):
        """Test status command when prerequisites check fails."""
        runner = CliRunner()

        # Mock manager
        mock_manager = Mock()
        mock_manager.check_prerequisites.return_value = {
            "success": False,
            "error": "npm not found",
            "recommendation": "Install Node.js with npm",
        }
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(status)

        assert result.exit_code == 0
        assert "npm not found" in result.output
        assert "Install Node.js with npm" in result.output

    @patch("any_agent.ui.cli.UIBuildManager")
    def test_status_command_ui_built(self, mock_manager_class):
        """Test status command when UI is built."""
        runner = CliRunner()

        # Mock manager
        mock_manager = Mock()
        mock_manager.check_prerequisites.return_value = {
            "success": True,
            "node_version": "v18.17.0",
            "npm_version": "9.6.7",
        }
        mock_manager.get_build_info.return_value = {
            "built": True,
            "dist_dir": "/path/to/dist",
            "size_mb": 2.1,
            "file_count": 15,
            "package_info": {
                "name": "any-agent-ui",
                "version": "1.0.0",
                "dependencies": 25,
            },
        }
        mock_manager.ui_source_dir = Path("/src/ui")
        mock_package_json = Mock()
        mock_package_json.exists.return_value = True
        mock_manager.package_json = mock_package_json
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(status)

        assert result.exit_code == 0
        assert "UI is built and ready" in result.output
        assert "2.1 MB" in result.output
        assert "any-agent-ui v1.0.0" in result.output
        assert "package.json found" in result.output

    @patch("any_agent.ui.cli.UIBuildManager")
    def test_status_command_ui_not_built(self, mock_manager_class):
        """Test status command when UI is not built."""
        runner = CliRunner()

        # Mock manager
        mock_manager = Mock()
        mock_manager.check_prerequisites.return_value = {
            "success": True,
            "node_version": "v18.17.0",
            "npm_version": "9.6.7",
        }
        mock_manager.get_build_info.return_value = {
            "built": False,
            "error": "Dist directory not found",
        }
        mock_manager.ui_source_dir = Path("/src/ui")
        mock_package_json = Mock()
        mock_package_json.exists.return_value = False
        mock_manager.package_json = mock_package_json
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(status)

        assert result.exit_code == 0
        assert "UI not built" in result.output
        assert "Dist directory not found" in result.output
        assert "package.json not found" in result.output

    @patch("any_agent.ui.cli.UIBuildManager")
    def test_clean_command_no_artifacts(self, mock_manager_class):
        """Test clean command when no artifacts exist."""
        runner = CliRunner()

        # Mock manager
        mock_manager = Mock()
        mock_manager.get_build_info.return_value = {"built": False}
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(clean)

        assert result.exit_code == 0
        assert "No build artifacts found" in result.output

    @patch("any_agent.ui.cli.UIBuildManager")
    def test_clean_command_with_force(self, mock_manager_class):
        """Test clean command with force flag."""
        runner = CliRunner()

        # Mock manager
        mock_manager = Mock()
        mock_manager.get_build_info.return_value = {
            "built": True,
            "dist_dir": "/path/to/dist",
            "size_mb": 2.5,
        }
        mock_manager.ui_source_dir = Mock()
        mock_node_modules = Mock()
        mock_node_modules.exists.return_value = True
        mock_manager.ui_source_dir.__truediv__ = Mock(return_value=mock_node_modules)

        mock_manager.clean_build.return_value = {
            "success": True,
            "message": "Cleaned successfully",
        }
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(clean, ["--force"])

        assert result.exit_code == 0
        assert "Build artifacts cleaned successfully" in result.output
        mock_manager.clean_build.assert_called_once()

    @patch("any_agent.ui.cli.UIBuildManager")
    def test_clean_command_user_cancels(self, mock_manager_class):
        """Test clean command when user cancels confirmation."""
        runner = CliRunner()

        # Mock manager
        mock_manager = Mock()
        mock_manager.get_build_info.return_value = {
            "built": True,
            "dist_dir": "/path/to/dist",
            "size_mb": 2.5,
        }
        mock_manager.ui_source_dir = Mock()
        mock_node_modules = Mock()
        mock_node_modules.exists.return_value = False
        mock_manager.ui_source_dir.__truediv__ = Mock(return_value=mock_node_modules)
        mock_manager_class.return_value = mock_manager

        # Simulate user saying 'n' to confirmation
        result = runner.invoke(clean, input="n\n")

        assert result.exit_code == 0
        assert "Cleaning cancelled" in result.output

    @patch("any_agent.ui.cli.UIBuildManager")
    def test_clean_command_with_confirmation(self, mock_manager_class):
        """Test clean command with user confirmation."""
        runner = CliRunner()

        # Mock manager
        mock_manager = Mock()
        mock_manager.get_build_info.return_value = {
            "built": True,
            "dist_dir": "/path/to/dist",
            "size_mb": 2.5,
        }
        mock_manager.ui_source_dir = Mock()
        mock_node_modules = Mock()
        mock_node_modules.exists.return_value = True
        mock_manager.ui_source_dir.__truediv__ = Mock(return_value=mock_node_modules)

        mock_manager.clean_build.return_value = {
            "success": True,
            "message": "Cleaned successfully",
        }
        mock_manager_class.return_value = mock_manager

        # Simulate user saying 'y' to confirmation
        result = runner.invoke(clean, input="y\n")

        assert result.exit_code == 0
        assert "Build artifacts cleaned successfully" in result.output

    @patch("any_agent.ui.cli.UIBuildManager")
    def test_clean_command_failure(self, mock_manager_class):
        """Test clean command when cleaning fails."""
        runner = CliRunner()

        # Mock manager
        mock_manager = Mock()
        mock_manager.get_build_info.return_value = {
            "built": True,
            "dist_dir": "/path/to/dist",
            "size_mb": 2.5,
        }
        mock_manager.ui_source_dir = Mock()
        mock_node_modules = Mock()
        mock_node_modules.exists.return_value = False
        mock_manager.ui_source_dir.__truediv__ = Mock(return_value=mock_node_modules)

        mock_manager.clean_build.return_value = {
            "success": False,
            "error": "Permission denied",
        }
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(clean, ["--force"])

        assert result.exit_code == 0
        assert "Cleaning failed" in result.output
        assert "Permission denied" in result.output

    @patch("any_agent.ui.cli.UIBuildManager")
    def test_copy_command_ui_not_built(self, mock_manager_class, tmp_path):
        """Test copy command when UI is not built."""
        runner = CliRunner()

        # Mock manager
        mock_manager = Mock()
        mock_manager.is_ui_built.return_value = False
        mock_manager_class.return_value = mock_manager

        build_context = tmp_path / "build_context"
        build_context.mkdir()

        result = runner.invoke(copy, [str(build_context)])

        assert result.exit_code == 0
        assert "UI not built" in result.output

    @patch("any_agent.ui.cli.UIBuildManager")
    def test_copy_command_success(self, mock_manager_class, tmp_path):
        """Test copy command successful operation."""
        runner = CliRunner()

        # Mock manager
        mock_manager = Mock()
        mock_manager.is_ui_built.return_value = True
        mock_manager.copy_dist_to_context.return_value = {
            "success": True,
            "static_dir": "/build/static",
            "files_copied": 10,
        }
        mock_manager_class.return_value = mock_manager

        build_context = tmp_path / "build_context"
        build_context.mkdir()

        result = runner.invoke(copy, [str(build_context)])

        assert result.exit_code == 0
        assert "UI files copied successfully" in result.output
        assert "Files copied: 10" in result.output

    @patch("any_agent.ui.cli.UIBuildManager")
    def test_copy_command_failure(self, mock_manager_class, tmp_path):
        """Test copy command when copying fails."""
        runner = CliRunner()

        # Mock manager
        mock_manager = Mock()
        mock_manager.is_ui_built.return_value = True
        mock_manager.copy_dist_to_context.return_value = {
            "success": False,
            "error": "Permission denied",
        }
        mock_manager_class.return_value = mock_manager

        build_context = tmp_path / "build_context"
        build_context.mkdir()

        result = runner.invoke(copy, [str(build_context)])

        assert result.exit_code == 0
        assert "Copy failed" in result.output
        assert "Permission denied" in result.output

    @patch("any_agent.ui.cli.UIBuildManager")
    def test_info_command_text_format(self, mock_manager_class):
        """Test info command with text output format."""
        runner = CliRunner()

        # Mock manager
        mock_manager = Mock()
        mock_manager.check_prerequisites.return_value = {
            "success": True,
            "node_version": "v18.17.0",
            "npm_version": "9.6.7",
        }
        mock_manager.get_build_info.return_value = {
            "built": True,
            "size_mb": 2.1,
            "file_count": 15,
            "package_info": {"name": "any-agent-ui", "version": "1.0.0"},
        }
        mock_manager.ui_source_dir = Path("/src/ui")
        mock_manager.dist_dir = Path("/src/ui/dist")
        mock_package_json = Mock()
        mock_package_json.exists.return_value = True
        mock_manager.package_json = mock_package_json
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(info)

        assert result.exit_code == 0
        assert "Detailed Information" in result.output
        assert "Prerequisites: ✅ OK" in result.output
        assert "Build Status: ✅ BUILT" in result.output
        assert "package.json: ✅ EXISTS" in result.output

    @patch("any_agent.ui.cli.UIBuildManager")
    def test_info_command_json_format(self, mock_manager_class):
        """Test info command with JSON output format."""
        runner = CliRunner()

        # Mock manager
        mock_manager = Mock()
        mock_manager.check_prerequisites.return_value = {
            "success": True,
            "node_version": "v18.17.0",
            "npm_version": "9.6.7",
        }
        mock_manager.get_build_info.return_value = {
            "built": True,
            "size_mb": 2.1,
            "file_count": 15,
        }
        mock_manager.ui_source_dir = Path("/src/ui")
        mock_manager.dist_dir = Path("/src/ui/dist")
        mock_package_json = Mock()
        mock_package_json.exists.return_value = True
        mock_manager.package_json = mock_package_json
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(info, ["--format", "json"])

        assert result.exit_code == 0

        # Parse JSON output
        output_data = json.loads(result.output)
        assert "prerequisites" in output_data
        assert "build_info" in output_data
        assert output_data["prerequisites"]["success"]
        assert output_data["build_info"]["built"]

    @patch("any_agent.ui.cli.UIBuildManager")
    def test_info_command_prerequisites_failed(self, mock_manager_class):
        """Test info command when prerequisites fail."""
        runner = CliRunner()

        # Mock manager
        mock_manager = Mock()
        mock_manager.check_prerequisites.return_value = {
            "success": False,
            "error": "Node.js not found",
        }
        mock_manager.get_build_info.return_value = {"built": False}
        mock_manager.ui_source_dir = Path("/src/ui")
        mock_manager.dist_dir = Path("/src/ui/dist")
        mock_package_json = Mock()
        mock_package_json.exists.return_value = False
        mock_manager.package_json = mock_package_json
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(info)

        assert result.exit_code == 0
        assert "Prerequisites: ❌ FAILED" in result.output
        assert "Build Status: ❌ NOT BUILT" in result.output
        assert "package.json: ❌ MISSING" in result.output

    def test_main_function(self):
        """Test main entry point function."""
        # This mainly tests that the function exists and can be called
        # The actual CLI testing is done through other tests
        runner = CliRunner()

        with patch("any_agent.ui.cli.ui_cli") as mock_cli:
            from any_agent.ui.cli import main

            # Call main function
            try:
                main()
            except SystemExit:
                pass  # Click CLI may exit

            mock_cli.assert_called_once()

    def test_version_option(self):
        """Test --version option on main command."""
        runner = CliRunner()
        result = runner.invoke(ui_cli, ["--version"])

        # Should exit with code 0 and show version
        assert result.exit_code == 0

    def test_individual_command_help(self):
        """Test help for individual commands."""
        runner = CliRunner()

        commands = ["build", "status", "clean", "copy", "info"]

        for cmd in commands:
            result = runner.invoke(ui_cli, [cmd, "--help"])
            assert result.exit_code == 0
            assert cmd in result.output.lower()

    @patch("any_agent.ui.cli.UIBuildManager")
    def test_build_command_no_options(self, mock_manager_class):
        """Test build command with no additional options."""
        runner = CliRunner()

        # Mock manager
        mock_manager = Mock()
        mock_manager.check_prerequisites.return_value = {
            "success": True,
            "node_version": "v18.17.0",
            "npm_version": "9.6.7",
        }
        mock_manager.build_ui.return_value = {
            "success": True,
            "dist_dir": "/path/to/dist",
            "build_size_mb": 2.5,
        }
        mock_manager_class.return_value = mock_manager

        result = runner.invoke(build)

        assert result.exit_code == 0
        assert "UI build completed successfully" in result.output
        # Should not call clean_build without --clean flag
        mock_manager.clean_build.assert_not_called()

    def test_copy_command_nonexistent_path(self):
        """Test copy command with non-existent build context path."""
        runner = CliRunner()

        result = runner.invoke(copy, ["/nonexistent/path"])

        # Should fail due to path validation
        assert result.exit_code != 0
