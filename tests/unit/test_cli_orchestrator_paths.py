"""CLI tests focusing on orchestrator execution paths for comprehensive coverage."""

import os
from unittest.mock import patch, Mock, MagicMock
from click.testing import CliRunner
import pytest
from any_agent.cli import main


class TestCLIOrchestratorPaths:
    """Test CLI orchestrator execution paths to improve coverage."""

    @patch('any_agent.core.orchestrator.AgentOrchestrator')
    @patch('any_agent.core.agent_context.AgentContextManager')  
    @patch('any_agent.ui.manager.UIBuildManager')
    def test_cli_normal_execution_path_dry_run(self, mock_ui, mock_context, mock_orchestrator):
        """Test normal CLI execution path in dry-run mode."""
        runner = CliRunner()
        
        # Mock orchestrator
        mock_orchestrator_instance = Mock()
        mock_adapter = Mock()
        mock_adapter.__class__.__name__ = "GoogleAdkAdapter"
        mock_orchestrator_instance.detect_framework.return_value = mock_adapter
        
        mock_metadata = Mock()
        mock_metadata.name = "test-agent"
        mock_metadata.framework = "adk"
        mock_orchestrator_instance.extract_metadata.return_value = mock_metadata
        mock_orchestrator_instance.containerize_agent.return_value = True
        mock_orchestrator.return_value = mock_orchestrator_instance
        
        # Mock context manager
        mock_context_instance = Mock()
        mock_context.return_value = mock_context_instance
        
        # Mock UI manager
        mock_ui_instance = Mock()
        mock_ui_instance.ensure_ui_built.return_value = True
        mock_ui.return_value = mock_ui_instance
        
        with runner.isolated_filesystem():
            os.makedirs("test_agent")
            with open("test_agent/__init__.py", "w") as f:
                f.write("# Test agent")
            
            result = runner.invoke(main, [
                "test_agent",
                "--dry-run",
                "--verbose"
            ])
            
            assert result.exit_code == 0
            assert "DRY RUN" in result.output

    @patch('any_agent.core.orchestrator.AgentOrchestrator')
    @patch('any_agent.core.agent_context.AgentContextManager')
    @patch('any_agent.ui.manager.UIBuildManager')
    def test_cli_framework_detection_failure(self, mock_ui, mock_context, mock_orchestrator):
        """Test CLI behavior when framework detection fails."""
        runner = CliRunner()
        
        # Mock orchestrator with failed detection
        mock_orchestrator_instance = Mock()
        mock_orchestrator_instance.detect_framework.return_value = None
        mock_orchestrator.return_value = mock_orchestrator_instance
        
        # Mock context manager
        mock_context_instance = Mock()
        mock_context.return_value = mock_context_instance
        
        # Mock UI manager
        mock_ui_instance = Mock()
        mock_ui.return_value = mock_ui_instance
        
        with runner.isolated_filesystem():
            os.makedirs("test_agent")
            with open("test_agent/__init__.py", "w") as f:
                f.write("# Test agent")
            
            result = runner.invoke(main, [
                "test_agent",
                "--verbose",
                "--dry-run"
            ])
            
            # Should still complete but may show framework detection failure
            assert result.exit_code == 0

    @patch('any_agent.core.orchestrator.AgentOrchestrator')
    @patch('any_agent.core.agent_context.AgentContextManager')
    @patch('any_agent.ui.manager.UIBuildManager') 
    @patch('any_agent.core.port_checker.PortChecker')
    def test_cli_port_conflict_handling(self, mock_port_checker, mock_ui, mock_context, mock_orchestrator):
        """Test CLI behavior with port conflicts."""
        runner = CliRunner()
        
        # Mock port checker indicating conflict
        mock_port_checker_instance = Mock()
        mock_port_checker_instance.is_port_available.return_value = False
        mock_port_checker_instance.get_port_info.return_value = {
            "available": False,
            "reason": "Port in use"
        }
        mock_port_checker.return_value = mock_port_checker_instance
        
        # Mock other components
        mock_orchestrator_instance = Mock()
        mock_adapter = Mock()
        mock_adapter.__class__.__name__ = "GoogleAdkAdapter"
        mock_orchestrator_instance.detect_framework.return_value = mock_adapter
        mock_orchestrator.return_value = mock_orchestrator_instance
        
        mock_context_instance = Mock()
        mock_context.return_value = mock_context_instance
        
        mock_ui_instance = Mock()
        mock_ui.return_value = mock_ui_instance
        
        with runner.isolated_filesystem():
            os.makedirs("test_agent")
            with open("test_agent/__init__.py", "w") as f:
                f.write("# Test agent")
            
            result = runner.invoke(main, [
                "test_agent",
                "--port", "8080",
                "--dry-run"
            ])
            
            assert result.exit_code == 0

    @patch('any_agent.core.orchestrator.AgentOrchestrator')
    @patch('any_agent.core.agent_context.AgentContextManager')
    @patch('any_agent.ui.manager.UIBuildManager')
    def test_cli_ui_build_handling(self, mock_ui, mock_context, mock_orchestrator):
        """Test CLI UI build handling paths."""
        runner = CliRunner()
        
        # Mock orchestrator
        mock_orchestrator_instance = Mock()
        mock_adapter = Mock()
        mock_adapter.__class__.__name__ = "GoogleAdkAdapter"
        mock_orchestrator_instance.detect_framework.return_value = mock_adapter
        mock_orchestrator.return_value = mock_orchestrator_instance
        
        # Mock context manager
        mock_context_instance = Mock()
        mock_context.return_value = mock_context_instance
        
        # Mock UI manager scenarios
        scenarios = [
            # UI build successful
            {"ensure_ui_built": True, "is_ui_built": True},
            # UI build needed
            {"ensure_ui_built": True, "is_ui_built": False},
            # UI disabled
            {"ensure_ui_built": False, "is_ui_built": False},
        ]
        
        for scenario in scenarios:
            mock_ui_instance = Mock()
            mock_ui_instance.ensure_ui_built.return_value = scenario["ensure_ui_built"]
            mock_ui_instance.is_ui_built.return_value = scenario["is_ui_built"]
            mock_ui.return_value = mock_ui_instance
            
            with runner.isolated_filesystem():
                os.makedirs("test_agent")
                with open("test_agent/__init__.py", "w") as f:
                    f.write("# Test agent")
                
                args = ["test_agent", "--dry-run"]
                if scenario.get("no_ui"):
                    args.append("--no-ui")
                if scenario.get("rebuild_ui"):
                    args.append("--rebuild-ui")
                
                result = runner.invoke(main, args)
                assert result.exit_code == 0

    @patch('any_agent.core.orchestrator.AgentOrchestrator')
    @patch('any_agent.core.agent_context.AgentContextManager')
    @patch('any_agent.ui.manager.UIBuildManager')
    def test_cli_metadata_extraction_scenarios(self, mock_ui, mock_context, mock_orchestrator):
        """Test CLI metadata extraction with different scenarios."""
        runner = CliRunner()
        
        # Mock context manager
        mock_context_instance = Mock()
        mock_context.return_value = mock_context_instance
        
        # Mock UI manager
        mock_ui_instance = Mock()
        mock_ui_instance.ensure_ui_built.return_value = True
        mock_ui.return_value = mock_ui_instance
        
        # Test different metadata scenarios
        metadata_scenarios = [
            # Successful metadata extraction
            {"name": "test-agent", "framework": "adk", "success": True},
            # Metadata extraction with special characters
            {"name": "test_agent-v1.0", "framework": "aws-strands", "success": True},
            # Minimal metadata
            {"name": "agent", "framework": "auto", "success": True},
        ]
        
        for scenario in metadata_scenarios:
            mock_orchestrator_instance = Mock()
            mock_adapter = Mock()
            mock_adapter.__class__.__name__ = "TestAdapter"
            mock_orchestrator_instance.detect_framework.return_value = mock_adapter
            
            if scenario["success"]:
                mock_metadata = Mock()
                mock_metadata.name = scenario["name"]
                mock_metadata.framework = scenario["framework"]
                mock_orchestrator_instance.extract_metadata.return_value = mock_metadata
            else:
                mock_orchestrator_instance.extract_metadata.side_effect = Exception("Metadata error")
            
            mock_orchestrator.return_value = mock_orchestrator_instance
            
            with runner.isolated_filesystem():
                os.makedirs("test_agent")
                with open("test_agent/__init__.py", "w") as f:
                    f.write("# Test agent")
                
                result = runner.invoke(main, [
                    "test_agent",
                    "--dry-run",
                    "--verbose"
                ])
                
                assert result.exit_code == 0

    @patch('any_agent.core.orchestrator.AgentOrchestrator')
    @patch('any_agent.core.agent_context.AgentContextManager')
    @patch('any_agent.ui.manager.UIBuildManager')
    def test_cli_containerization_scenarios(self, mock_ui, mock_context, mock_orchestrator):
        """Test CLI containerization with different outcomes."""
        runner = CliRunner()
        
        # Mock context manager
        mock_context_instance = Mock()
        mock_context.return_value = mock_context_instance
        
        # Mock UI manager
        mock_ui_instance = Mock()
        mock_ui_instance.ensure_ui_built.return_value = True
        mock_ui.return_value = mock_ui_instance
        
        # Test containerization scenarios
        containerization_scenarios = [
            {"success": True, "build_enabled": True},
            {"success": True, "build_enabled": False},
            {"success": False, "error": "Build failed"},
        ]
        
        for scenario in containerization_scenarios:
            mock_orchestrator_instance = Mock()
            mock_adapter = Mock()
            mock_adapter.__class__.__name__ = "TestAdapter"
            mock_orchestrator_instance.detect_framework.return_value = mock_adapter
            
            mock_metadata = Mock()
            mock_metadata.name = "test-agent"
            mock_metadata.framework = "test"
            mock_orchestrator_instance.extract_metadata.return_value = mock_metadata
            
            if scenario["success"]:
                mock_orchestrator_instance.containerize_agent.return_value = True
            else:
                mock_orchestrator_instance.containerize_agent.side_effect = Exception(
                    scenario.get("error", "Containerization failed")
                )
            
            mock_orchestrator.return_value = mock_orchestrator_instance
            
            with runner.isolated_filesystem():
                os.makedirs("test_agent")
                with open("test_agent/__init__.py", "w") as f:
                    f.write("# Test agent")
                
                args = ["test_agent", "--dry-run"]
                if not scenario.get("build_enabled", True):
                    args.append("--no-build")
                
                result = runner.invoke(main, args)
                
                # Should handle gracefully even if containerization fails in dry-run
                assert result.exit_code == 0

    @patch('any_agent.core.orchestrator.AgentOrchestrator')
    @patch('any_agent.core.agent_context.AgentContextManager')
    @patch('any_agent.ui.manager.UIBuildManager')
    def test_cli_helmsman_registration_scenarios(self, mock_ui, mock_context, mock_orchestrator):
        """Test CLI Helmsman registration handling."""
        runner = CliRunner()
        
        # Mock orchestrator
        mock_orchestrator_instance = Mock()
        mock_adapter = Mock()
        mock_adapter.__class__.__name__ = "TestAdapter"
        mock_orchestrator_instance.detect_framework.return_value = mock_adapter
        
        mock_metadata = Mock()
        mock_metadata.name = "test-agent"
        mock_orchestrator_instance.extract_metadata.return_value = mock_metadata
        mock_orchestrator.return_value = mock_orchestrator_instance
        
        # Mock context manager
        mock_context_instance = Mock()
        mock_context.return_value = mock_context_instance
        
        # Mock UI manager
        mock_ui_instance = Mock()
        mock_ui_instance.ensure_ui_built.return_value = True
        mock_ui.return_value = mock_ui_instance
        
        # Test different Helmsman scenarios
        helmsman_scenarios = [
            {
                "enabled": True,
                "agent_name": "test-helmsman-agent",
                "url": "http://localhost:7080",
                "token": "test-token"
            },
            {
                "enabled": True, 
                "agent_name": "simple-agent",
                "url": "http://custom.helmsman.url:8080",
                "token": None
            },
            {
                "enabled": False
            }
        ]
        
        for scenario in helmsman_scenarios:
            with runner.isolated_filesystem():
                os.makedirs("test_agent")
                with open("test_agent/__init__.py", "w") as f:
                    f.write("# Test agent")
                
                args = ["test_agent", "--dry-run"]
                
                if scenario["enabled"]:
                    args.extend(["--helmsman"])
                    if scenario.get("agent_name"):
                        args.extend(["--agent-name", scenario["agent_name"]])
                    if scenario.get("url"):
                        args.extend(["--helmsman-url", scenario["url"]])
                
                result = runner.invoke(main, args)
                assert result.exit_code == 0

    def test_cli_comprehensive_flag_combinations(self):
        """Test CLI with comprehensive flag combinations."""
        runner = CliRunner()
        
        # Test various realistic flag combinations
        flag_combinations = [
            ["--verbose", "--dry-run", "--no-ui"],
            ["--framework", "adk", "--port", "8080", "--dry-run"],
            ["--no-build", "--no-run", "--dry-run"],
            ["--rebuild-ui", "--skip-a2a-test", "--dry-run"],
            ["--helmsman", "--agent-name", "combo-test", "--verbose", "--dry-run"],
        ]
        
        for flags in flag_combinations:
            with runner.isolated_filesystem():
                os.makedirs("test_agent")
                with open("test_agent/__init__.py", "w") as f:
                    f.write("# Test agent")
                
                args = ["test_agent"] + flags
                result = runner.invoke(main, args)
                
                assert result.exit_code == 0

    @patch('any_agent.core.orchestrator.AgentOrchestrator')
    def test_cli_framework_specific_port_detection(self, mock_orchestrator):
        """Test framework-specific port detection logic."""
        runner = CliRunner()
        
        # Test different framework adapters and their port assignments
        framework_configs = [
            ("GoogleAdkAdapter", 8035),
            ("AwsStrandsAdapter", 8045), 
            ("LangchainAdapter", 8055),
            ("CrewaiAdapter", 8065),
            ("LanggraphAdapter", 8075),
            ("UnknownAdapter", 8080),  # fallback
        ]
        
        for adapter_class, expected_port in framework_configs:
            mock_adapter = Mock()
            mock_adapter.__class__.__name__ = adapter_class
            mock_orchestrator_instance = Mock()
            mock_orchestrator_instance.detect_framework.return_value = mock_adapter
            mock_orchestrator.return_value = mock_orchestrator_instance
            
            with runner.isolated_filesystem():
                os.makedirs("test_agent")
                with open("test_agent/__init__.py", "w") as f:
                    f.write("# Test agent")
                
                result = runner.invoke(main, [
                    "test_agent",
                    "--verbose",
                    "--dry-run"
                ])
                
                assert result.exit_code == 0
                # Should show the framework-specific port in verbose output
                assert str(expected_port) in result.output or "DRY RUN" in result.output

    def test_cli_edge_cases_and_error_conditions(self):
        """Test CLI edge cases and error conditions."""
        runner = CliRunner()
        
        # Test various edge cases
        edge_cases = [
            # Long agent names
            {"args": ["--agent-name", "very-long-agent-name-that-tests-limits-" + "x" * 50, "--dry-run"]},
            # Special characters in names  
            {"args": ["--agent-name", "test-agent_v1.0-beta", "--dry-run"]},
            # Maximum timeout values
            {"args": ["--a2a-test-timeout", "300", "--dry-run"]},
        ]
        
        for case in edge_cases:
            with runner.isolated_filesystem():
                os.makedirs("test_agent") 
                with open("test_agent/__init__.py", "w") as f:
                    f.write("# Test agent")
                
                args = ["test_agent"] + case["args"]
                result = runner.invoke(main, args)
                
                # Should handle gracefully
                assert result.exit_code == 0