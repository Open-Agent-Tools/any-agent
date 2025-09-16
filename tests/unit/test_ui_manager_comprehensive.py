"""Comprehensive UI Manager test suite for build system coverage."""

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

from any_agent.ui.manager import UIBuildManager


class TestUIBuildManagerComprehensive:
    """Comprehensive tests for UI Build Manager."""

    def test_init_paths(self):
        """Test UIBuildManager initialization with correct paths."""
        manager = UIBuildManager()

        # Check paths are set correctly
        assert (
            manager.ui_source_dir
            == Path(__file__).parent.parent.parent / "src" / "any_agent" / "ui"
        )
        assert manager.dist_dir == manager.ui_source_dir / "dist"
        assert manager.package_json == manager.ui_source_dir / "package.json"

    def test_is_ui_built_false_no_dist(self, tmp_path):
        """Test is_ui_built returns False when dist directory doesn't exist."""
        manager = UIBuildManager()
        manager.dist_dir = tmp_path / "nonexistent_dist"

        assert not manager.is_ui_built()

    def test_is_ui_built_false_missing_essential_files(self, tmp_path):
        """Test is_ui_built returns False when essential files are missing."""
        manager = UIBuildManager()
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        manager.dist_dir = dist_dir

        # Only create index.html, missing assets
        (dist_dir / "index.html").write_text("<html></html>")

        assert not manager.is_ui_built()

    def test_is_ui_built_true_complete(self, tmp_path):
        """Test is_ui_built returns True when all essential files exist."""
        manager = UIBuildManager()
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        manager.dist_dir = dist_dir

        # Create essential files
        (dist_dir / "index.html").write_text("<html></html>")
        assets_dir = dist_dir / "assets"
        assets_dir.mkdir()
        (assets_dir / "main.js").write_text("// JS content")

        assert manager.is_ui_built()

    def test_should_rebuild_ui_force_rebuild(self, tmp_path):
        """Test should_rebuild_ui with force_rebuild=True."""
        manager = UIBuildManager()
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        manager.dist_dir = dist_dir

        # Create complete UI
        (dist_dir / "index.html").write_text("<html></html>")
        (dist_dir / "assets").mkdir()

        assert manager.should_rebuild_ui(force_rebuild=True)

    def test_should_rebuild_ui_not_built(self, tmp_path):
        """Test should_rebuild_ui when UI is not built."""
        manager = UIBuildManager()
        manager.dist_dir = tmp_path / "nonexistent_dist"

        assert manager.should_rebuild_ui()

    def test_should_rebuild_ui_already_built(self, tmp_path):
        """Test should_rebuild_ui when UI is already built."""
        manager = UIBuildManager()
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        manager.dist_dir = dist_dir

        # Create complete UI
        (dist_dir / "index.html").write_text("<html></html>")
        (dist_dir / "assets").mkdir()

        assert not manager.should_rebuild_ui()

    def test_build_ui_no_package_json(self, tmp_path):
        """Test build_ui when package.json doesn't exist."""
        manager = UIBuildManager()
        manager.package_json = tmp_path / "nonexistent_package.json"
        manager.dist_dir = tmp_path / "nonexistent_dist"

        result = manager.build_ui()

        assert not result["success"]
        assert "No pre-built UI assets available" in result["error"]
        assert "recommendation" in result

    @patch("subprocess.run")
    def test_build_ui_npm_install_needed(self, mock_run, tmp_path):
        """Test build_ui when npm install is needed."""
        manager = UIBuildManager()
        manager.ui_source_dir = tmp_path
        manager.dist_dir = tmp_path / "dist"
        manager.package_json = tmp_path / "package.json"

        # Create package.json
        manager.package_json.write_text('{"name": "test"}')

        # Mock successful npm install and build
        mock_run.side_effect = [
            Mock(returncode=0, stdout="install success", stderr=""),  # npm install
            Mock(returncode=0, stdout="build success", stderr=""),  # npm run build
        ]

        # Create expected dist structure
        manager.dist_dir.mkdir()
        (manager.dist_dir / "index.html").write_text("<html></html>")
        (manager.dist_dir / "assets").mkdir()

        result = manager.build_ui()

        assert result["success"]
        assert "message" in result
        assert mock_run.call_count == 2

    @patch("subprocess.run")
    def test_build_ui_npm_install_failure(self, mock_run, tmp_path):
        """Test build_ui when npm install fails."""
        manager = UIBuildManager()
        manager.ui_source_dir = tmp_path
        manager.package_json = tmp_path / "package.json"

        # Create package.json
        manager.package_json.write_text('{"name": "test"}')

        # Mock failed npm install
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="install failed")

        result = manager.build_ui()

        assert not result["success"]
        assert "npm install failed" in result["error"]
        assert "recommendation" in result

    @patch("subprocess.run")
    def test_build_ui_build_failure(self, mock_run, tmp_path):
        """Test build_ui when npm run build fails."""
        manager = UIBuildManager()
        manager.ui_source_dir = tmp_path
        manager.dist_dir = tmp_path / "dist"
        manager.package_json = tmp_path / "package.json"

        # Create package.json and node_modules (skip install)
        manager.package_json.write_text('{"name": "test"}')
        (tmp_path / "node_modules").mkdir()

        # Mock failed build
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="build failed")

        result = manager.build_ui()

        assert not result["success"]
        assert "npm run build failed" in result["error"]

    @patch("subprocess.run")
    def test_build_ui_timeout_error(self, mock_run, tmp_path):
        """Test build_ui when subprocess times out."""
        manager = UIBuildManager()
        manager.ui_source_dir = tmp_path
        manager.package_json = tmp_path / "package.json"

        # Create package.json
        manager.package_json.write_text('{"name": "test"}')

        # Mock timeout
        mock_run.side_effect = subprocess.TimeoutExpired("npm", 300)

        result = manager.build_ui()

        assert not result["success"]
        assert "timed out" in result["error"]

    @patch("subprocess.run")
    def test_build_ui_npm_not_found(self, mock_run, tmp_path):
        """Test build_ui when npm is not found."""
        manager = UIBuildManager()
        manager.ui_source_dir = tmp_path
        manager.package_json = tmp_path / "package.json"

        # Create package.json
        manager.package_json.write_text('{"name": "test"}')

        # Mock npm not found
        mock_run.side_effect = FileNotFoundError("npm not found")

        result = manager.build_ui()

        assert not result["success"]
        assert "npm not found" in result["error"]

    @patch("subprocess.run")
    def test_build_ui_success_with_node_modules(self, mock_run, tmp_path):
        """Test build_ui success when node_modules already exists."""
        manager = UIBuildManager()
        manager.ui_source_dir = tmp_path
        manager.dist_dir = tmp_path / "dist"
        manager.package_json = tmp_path / "package.json"

        # Create package.json and node_modules
        manager.package_json.write_text('{"name": "test"}')
        (tmp_path / "node_modules").mkdir()

        # Mock successful build (only one call since install is skipped)
        mock_run.return_value = Mock(returncode=0, stdout="build success", stderr="")

        # Create expected dist structure
        manager.dist_dir.mkdir()
        (manager.dist_dir / "index.html").write_text("<html></html>")
        (manager.dist_dir / "assets").mkdir()

        result = manager.build_ui()

        assert result["success"]
        assert mock_run.call_count == 1  # Only build, no install

    def test_clean_build_success(self, tmp_path):
        """Test clean_build removes dist and node_modules."""
        manager = UIBuildManager()
        manager.ui_source_dir = tmp_path
        manager.dist_dir = tmp_path / "dist"

        # Create directories to clean
        manager.dist_dir.mkdir()
        (manager.dist_dir / "index.html").write_text("<html></html>")
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "package").mkdir()

        result = manager.clean_build()

        assert result["success"]
        assert not manager.dist_dir.exists()
        assert not node_modules.exists()

    def test_clean_build_no_directories(self, tmp_path):
        """Test clean_build when directories don't exist."""
        manager = UIBuildManager()
        manager.ui_source_dir = tmp_path
        manager.dist_dir = tmp_path / "nonexistent_dist"

        result = manager.clean_build()

        assert result["success"]
        assert "cleaned successfully" in result["message"]

    @patch("shutil.rmtree")
    def test_clean_build_error(self, mock_rmtree, tmp_path):
        """Test clean_build when removal fails."""
        manager = UIBuildManager()
        manager.ui_source_dir = tmp_path
        manager.dist_dir = tmp_path / "dist"

        # Create directory
        manager.dist_dir.mkdir()

        # Mock removal failure
        mock_rmtree.side_effect = PermissionError("Permission denied")

        result = manager.clean_build()

        assert not result["success"]
        assert "Failed to clean build" in result["error"]

    def test_copy_dist_to_context_ui_not_built(self, tmp_path):
        """Test copy_dist_to_context when UI is not built."""
        manager = UIBuildManager()
        manager.dist_dir = tmp_path / "nonexistent_dist"

        build_context = tmp_path / "build_context"
        build_context.mkdir()

        result = manager.copy_dist_to_context(build_context)

        assert not result["success"]
        assert "UI not built" in result["error"]

    def test_copy_dist_to_context_success(self, tmp_path):
        """Test copy_dist_to_context successful operation."""
        manager = UIBuildManager()

        # Create dist directory with files
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        manager.dist_dir = dist_dir

        (dist_dir / "index.html").write_text("<html></html>")
        assets_dir = dist_dir / "assets"
        assets_dir.mkdir()
        (assets_dir / "main.js").write_text("// JS content")

        # Create build context
        build_context = tmp_path / "build_context"
        build_context.mkdir()

        result = manager.copy_dist_to_context(build_context)

        assert result["success"]
        assert "static_dir" in result
        assert result["files_copied"] == 2  # index.html and assets dir

        # Verify files were copied
        static_dir = build_context / "static"
        assert static_dir.exists()
        assert (static_dir / "index.html").exists()
        assert (static_dir / "assets" / "main.js").exists()

    @patch("shutil.copy2")
    def test_copy_dist_to_context_copy_error(self, mock_copy2, tmp_path):
        """Test copy_dist_to_context when copying fails."""
        manager = UIBuildManager()

        # Create minimal dist directory
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        manager.dist_dir = dist_dir
        (dist_dir / "index.html").write_text("<html></html>")
        (dist_dir / "assets").mkdir()

        # Mock copy failure
        mock_copy2.side_effect = PermissionError("Permission denied")

        build_context = tmp_path / "build_context"
        build_context.mkdir()

        result = manager.copy_dist_to_context(build_context)

        assert not result["success"]
        assert "Failed to copy UI files" in result["error"]

    def test_get_build_info_not_built(self, tmp_path):
        """Test get_build_info when UI is not built."""
        manager = UIBuildManager()
        manager.dist_dir = tmp_path / "nonexistent_dist"

        result = manager.get_build_info()

        assert not result["built"]
        assert "not built" in result["message"]

    def test_get_build_info_built_with_package_json(self, tmp_path):
        """Test get_build_info when UI is built with package.json."""
        manager = UIBuildManager()

        # Create dist directory
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        manager.dist_dir = dist_dir

        (dist_dir / "index.html").write_text("<html></html>")
        (dist_dir / "assets").mkdir()
        (dist_dir / "assets" / "main.js").write_text("// content")

        # Create package.json
        package_json = tmp_path / "package.json"
        manager.package_json = package_json
        package_data = {
            "name": "test-ui",
            "version": "1.0.0",
            "dependencies": {"react": "^18.0.0", "vite": "^4.0.0"},
        }
        package_json.write_text(json.dumps(package_data))

        result = manager.get_build_info()

        assert result["built"]
        assert "dist_dir" in result
        assert "size_mb" in result
        assert "file_count" in result
        assert result["package_info"]["name"] == "test-ui"
        assert result["package_info"]["version"] == "1.0.0"
        assert result["package_info"]["dependencies"] == 2

    def test_get_build_info_built_no_package_json(self, tmp_path):
        """Test get_build_info when UI is built but no package.json."""
        manager = UIBuildManager()

        # Create dist directory
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        manager.dist_dir = dist_dir
        manager.package_json = tmp_path / "nonexistent_package.json"

        (dist_dir / "index.html").write_text("<html></html>")
        (dist_dir / "assets").mkdir()

        result = manager.get_build_info()

        assert result["built"]
        assert result["package_info"] == {}

    @patch("builtins.open")
    def test_get_build_info_package_json_read_error(self, mock_open, tmp_path):
        """Test get_build_info when package.json reading fails."""
        manager = UIBuildManager()

        # Create dist directory
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        manager.dist_dir = dist_dir

        (dist_dir / "index.html").write_text("<html></html>")
        (dist_dir / "assets").mkdir()

        # Create package.json that exists but mock reading failure
        package_json = tmp_path / "package.json"
        package_json.write_text('{"name": "test"}')
        manager.package_json = package_json

        # Mock file read failure
        mock_open.side_effect = Exception("Read error")

        result = manager.get_build_info()

        assert not result["built"]
        assert "Failed to get build info" in result["error"]

    def test_get_directory_size(self, tmp_path):
        """Test _get_directory_size calculation."""
        manager = UIBuildManager()

        # Create files with known sizes
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        (test_dir / "file1.txt").write_text("a" * 100)  # 100 bytes
        (test_dir / "file2.txt").write_text("b" * 200)  # 200 bytes

        # Create subdirectory with file
        subdir = test_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("c" * 50)  # 50 bytes

        size = manager._get_directory_size(test_dir)

        assert size == 350  # 100 + 200 + 50

    def test_get_directory_size_empty(self, tmp_path):
        """Test _get_directory_size with empty directory."""
        manager = UIBuildManager()

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        size = manager._get_directory_size(empty_dir)

        assert size == 0

    @patch("any_agent.ui.manager.Path.rglob")
    def test_get_directory_size_stat_error(self, mock_rglob, tmp_path):
        """Test _get_directory_size when stat fails."""
        manager = UIBuildManager()

        # Mock file that raises exception on stat
        mock_file = Mock()
        mock_file.is_file.return_value = True
        mock_file.stat.side_effect = OSError("Stat failed")
        mock_rglob.return_value = [mock_file]

        size = manager._get_directory_size(tmp_path)

        assert size == 0  # Should handle errors gracefully

    @patch("subprocess.run")
    def test_check_prerequisites_success(self, mock_run):
        """Test check_prerequisites when Node.js and npm are available."""
        # Mock successful version checks
        mock_run.side_effect = [
            Mock(returncode=0, stdout="v18.17.0\n", stderr=""),  # node --version
            Mock(returncode=0, stdout="9.6.7\n", stderr=""),  # npm --version
        ]

        result = UIBuildManager.check_prerequisites()

        assert result["success"]
        assert result["node_version"] == "v18.17.0"
        assert result["npm_version"] == "9.6.7"
        assert "Prerequisites satisfied" in result["message"]

    @patch("subprocess.run")
    def test_check_prerequisites_node_failure(self, mock_run):
        """Test check_prerequisites when Node.js check fails."""
        # Mock failed node check
        mock_run.return_value = Mock(
            returncode=1, stdout="", stderr="command not found"
        )

        result = UIBuildManager.check_prerequisites()

        assert not result["success"]
        assert "Node.js not working properly" in result["error"]
        assert "recommendation" in result

    @patch("subprocess.run")
    def test_check_prerequisites_npm_failure(self, mock_run):
        """Test check_prerequisites when npm check fails."""
        # Mock successful node, failed npm
        mock_run.side_effect = [
            Mock(returncode=0, stdout="v18.17.0\n", stderr=""),  # node --version
            Mock(returncode=1, stdout="", stderr="npm error"),  # npm --version
        ]

        result = UIBuildManager.check_prerequisites()

        assert not result["success"]
        assert "npm not working properly" in result["error"]

    @patch("subprocess.run")
    def test_check_prerequisites_not_found(self, mock_run):
        """Test check_prerequisites when Node.js/npm not found."""
        # Mock FileNotFoundError
        mock_run.side_effect = FileNotFoundError("node not found")

        result = UIBuildManager.check_prerequisites()

        assert not result["success"]
        assert "Node.js/npm not found" in result["error"]

    @patch("subprocess.run")
    def test_check_prerequisites_timeout(self, mock_run):
        """Test check_prerequisites when version check times out."""
        # Mock timeout
        mock_run.side_effect = subprocess.TimeoutExpired("node", 10)

        result = UIBuildManager.check_prerequisites()

        assert not result["success"]
        assert "timed out" in result["error"]

    @patch("subprocess.run")
    def test_check_prerequisites_unexpected_error(self, mock_run):
        """Test check_prerequisites with unexpected error."""
        # Mock unexpected exception
        mock_run.side_effect = Exception("Unexpected error")

        result = UIBuildManager.check_prerequisites()

        assert not result["success"]
        assert "Prerequisite check failed" in result["error"]
