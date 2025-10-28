"""Tauri project structure generator."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict


class TauriProjectGenerator:
    """Generates Tauri project structure for packaging agents."""

    def __init__(self) -> None:
        """Initialize the TauriProjectGenerator."""
        self.ui_source_path = Path(__file__).parent.parent / "ui"

    def generate_project(
        self,
        tauri_path: Path,
        metadata: Dict[str, str],
        agent_path: Path,
    ) -> Dict[str, Any]:
        """
        Generate complete Tauri project structure.

        Args:
            tauri_path: Path where Tauri project will be created
            metadata: Application metadata
            agent_path: Path to the agent directory

        Returns:
            Dict with success status
        """
        try:
            # Create directory structure
            self._create_directory_structure(tauri_path)

            # Copy React UI source
            self._copy_ui_source(tauri_path)

            # Process icon if provided
            if metadata.get("icon_path") and metadata["icon_path"] != "default":
                self._process_icon(tauri_path, Path(metadata["icon_path"]))

            # Generate Tauri configuration
            self._generate_tauri_config(tauri_path, metadata)

            # Generate Tauri v2 capabilities
            self._generate_capabilities(tauri_path)

            # Generate Rust main.rs
            self._generate_rust_main(tauri_path, metadata)

            # Generate Cargo.toml
            self._generate_cargo_toml(tauri_path, metadata)

            # Generate package.json
            self._generate_package_json(tauri_path, metadata)

            # Generate build script
            self._generate_build_script(tauri_path)

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_directory_structure(self, tauri_path: Path) -> None:
        """Create the basic Tauri directory structure."""
        directories = [
            tauri_path / "src",
            tauri_path / "src-tauri",
            tauri_path / "src-tauri" / "src",
            tauri_path / "src-tauri" / "icons",
            tauri_path / "public",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _copy_ui_source(self, tauri_path: Path) -> None:
        """Copy React UI source files to Tauri project."""
        # Copy src directory
        src_dest = tauri_path / "src"
        ui_src = self.ui_source_path / "src"

        if ui_src.exists():
            shutil.copytree(ui_src, src_dest, dirs_exist_ok=True)

        # Copy Tauri API adapter
        adapter_source = Path(__file__).parent / "tauri_api_adapter.ts"
        if adapter_source.exists():
            adapter_dest = tauri_path / "src" / "utils" / "tauri_api_adapter.ts"
            adapter_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(adapter_source, adapter_dest)

            # Modify api.ts to use dynamic port
            self._modify_api_for_tauri(tauri_path)

        # Copy index.html
        index_html = self.ui_source_path / "index.html"
        if index_html.exists():
            shutil.copy(index_html, tauri_path / "index.html")

        # Copy vite config
        vite_config = self.ui_source_path / "vite.config.ts"
        if vite_config.exists():
            shutil.copy(vite_config, tauri_path / "vite.config.ts")

        # Copy tsconfig files
        for tsconfig_file in ["tsconfig.json", "tsconfig.node.json"]:
            tsconfig = self.ui_source_path / tsconfig_file
            if tsconfig.exists():
                shutil.copy(tsconfig, tauri_path / tsconfig_file)

        # Copy index.css
        index_css = self.ui_source_path / "src" / "index.css"
        if index_css.exists():
            shutil.copy(index_css, tauri_path / "src" / "index.css")

    def _modify_api_for_tauri(self, tauri_path: Path) -> None:
        """Modify api.ts to use Tauri backend port discovery."""
        api_file = tauri_path / "src" / "utils" / "api.ts"

        if not api_file.exists():
            return

        # Read original api.ts
        with open(api_file, "r") as f:
            content = f.read()

        # Replace API_BASE_URL with dynamic version
        modified_content = content.replace(
            "const API_BASE_URL = '';",
            """import { getBackendURL, isTauriEnvironment, initializeTauriBackend } from './tauri_api_adapter';

let API_BASE_URL = '';

// Initialize backend URL discovery for Tauri
if (isTauriEnvironment()) {
  initializeTauriBackend().then(port => {
    API_BASE_URL = `http://localhost:${port}`;
    console.log('Tauri backend port discovered:', port);
  }).catch(error => {
    console.error('Failed to discover backend port:', error);
  });
}""",
        )

        # Write modified content
        with open(api_file, "w") as f:
            f.write(modified_content)

    def _process_icon(self, tauri_path: Path, icon_path: Path) -> None:
        """
        Process icon file and generate all required sizes using Tauri CLI.

        Args:
            tauri_path: Path to the Tauri project
            icon_path: Path to the source icon file
        """
        if not icon_path.exists():
            return

        # Create icons directory
        icons_dir = tauri_path / "src-tauri" / "icons"
        icons_dir.mkdir(parents=True, exist_ok=True)

        # Use Tauri CLI to generate all icon sizes
        try:
            subprocess.run(
                ["cargo", "tauri", "icon", str(icon_path)],
                cwd=tauri_path,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            # Fallback: just copy the source icon
            shutil.copy(icon_path, icons_dir / "icon.png")

    def _generate_tauri_config(
        self, tauri_path: Path, metadata: Dict[str, str]
    ) -> None:
        """Generate tauri.conf.json."""
        # Build bundle configuration
        bundle_config = {
            "active": True,
            "targets": "all",
            "identifier": f"com.{metadata.get('author', 'anyagent').lower().replace(' ', '').replace('-', '')}.{metadata['app_name'].lower().replace(' ', '').replace('-', '')}",
            "resources": ["resources/*"],
            "externalBin": [],
            "copyright": f"Copyright © {metadata.get('author', 'Any Agent')}",
            "category": "DeveloperTool",
            "shortDescription": metadata["description"],
            "longDescription": metadata["description"],
            "macOS": {
                "frameworks": [],
                "minimumSystemVersion": "10.13",
                "exceptionDomain": "",
                "signingIdentity": None,
                "providerShortName": None,
                "entitlements": None,
            },
        }

        # Only add icon configuration if icons exist
        icons_dir = tauri_path / "src-tauri" / "icons"
        if icons_dir.exists() and list(icons_dir.glob("*.png")):
            bundle_config["icon"] = [
                "icons/32x32.png",
                "icons/128x128.png",
                "icons/128x128@2x.png",
                "icons/icon.icns",
                "icons/icon.ico",
            ]

        # Tauri v2 minimal configuration
        config = {
            "$schema": "../node_modules/@tauri-apps/cli/schema.json",
            "build": {
                "beforeDevCommand": "npm run dev",
                "beforeBuildCommand": "npm run build"
            },
            "package": {
                "productName": metadata["app_name"],
                "version": metadata["version"]
            },
            "tauri": {
                "bundle": {
                    "active": True,
                    "targets": "all",
                    "identifier": bundle_config["identifier"],
                    "icon": bundle_config.get("icon", []),
                    "resources": bundle_config.get("resources", []),
                    "externalBin": bundle_config.get("externalBin", []),
                    "copyright": bundle_config.get("copyright", ""),
                    "category": bundle_config.get("category", "DeveloperTool"),
                    "shortDescription": metadata["description"],
                    "longDescription": metadata["description"],
                    "macOS": bundle_config.get("macOS", {}),
                }
            }
        }

        config_path = tauri_path / "src-tauri" / "tauri.conf.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

    def _generate_capabilities(self, tauri_path: Path) -> None:
        """Generate Tauri v2 capabilities for permissions."""
        capabilities_dir = tauri_path / "src-tauri" / "capabilities"
        capabilities_dir.mkdir(parents=True, exist_ok=True)

        # Main capability file for the app
        main_capability = {
            "identifier": "main-capability",
            "description": "Capability for the main window",
            "windows": ["main"],
            "permissions": [
                "core:default",
                "shell:allow-open",
                "fs:allow-read-file",
                "fs:allow-write-file",
                "fs:allow-exists",
                "http:default",
            ],
        }

        capability_path = capabilities_dir / "main.json"
        with open(capability_path, "w") as f:
            json.dump(main_capability, f, indent=2)

    def _generate_rust_main(self, tauri_path: Path, metadata: Dict[str, str]) -> None:
        """Generate Rust main.rs file."""
        # Tauri v2 - main.rs just calls the library
        main_rs = """// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    app_lib::run()
}
"""

        main_rs_path = tauri_path / "src-tauri" / "src" / "main.rs"
        with open(main_rs_path, "w") as f:
            f.write(main_rs)

        # lib.rs with Python backend management
        lib_rs = """// Tauri v2 application library
use std::process::{Command, Stdio};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // Start Python backend as a separate process
            // The Python script will find its own port and communicate it
            let resource_dir = app.path()
                .resource_dir()
                .expect("failed to resolve resource dir");

            let python_script = resource_dir.join("python-runtime/run_agent.py");
            let venv_python = resource_dir.join("python-runtime/venv/bin/python");

            // Try to start Python backend
            let _child = Command::new(&venv_python)
                .arg(&python_script)
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .spawn();

            // Note: We don't wait for the Python process here.
            // The React UI will poll for the backend to be ready.

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
"""
        lib_rs_path = tauri_path / "src-tauri" / "src" / "lib.rs"
        with open(lib_rs_path, "w") as f:
            f.write(lib_rs)

    def _generate_cargo_toml(self, tauri_path: Path, metadata: Dict[str, str]) -> None:
        """Generate Cargo.toml for Rust project."""
        cargo_toml = f'''[package]
name = "{metadata["app_name"].lower().replace(" ", "-")}"
version = "{metadata["version"]}"
description = "{metadata["description"]}"
authors = ["{metadata.get("author", "Any Agent")}"]
license = ""
repository = ""
edition = "2021"

# See more keys and their definitions at https://doc.rust-lang.org/cargo/reference/manifest.html

[lib]
name = "app_lib"
crate-type = ["staticlib", "cdylib", "rlib"]

[build-dependencies]
tauri-build = {{ version = "2", features = [] }}

[dependencies]
tauri = {{ version = "2", features = [] }}
tauri-plugin-shell = "2"
serde = {{ version = "1", features = ["derive"] }}
serde_json = "1"
'''

        cargo_toml_path = tauri_path / "src-tauri" / "Cargo.toml"
        with open(cargo_toml_path, "w") as f:
            f.write(cargo_toml)

        # Also create build.rs
        build_rs = """fn main() {
    tauri_build::build()
}
"""
        build_rs_path = tauri_path / "src-tauri" / "build.rs"
        with open(build_rs_path, "w") as f:
            f.write(build_rs)

    def _generate_package_json(
        self, tauri_path: Path, metadata: Dict[str, str]
    ) -> None:
        """Generate package.json for Node/npm."""
        # Read the original UI package.json
        original_package_json_path = self.ui_source_path / "package.json"
        if original_package_json_path.exists():
            with open(original_package_json_path, "r") as f:
                original = json.load(f)
        else:
            original = {"dependencies": {}, "devDependencies": {}}

        package_json = {
            "name": metadata["app_name"].lower().replace(" ", "-"),
            "version": metadata["version"],
            "description": metadata["description"],
            "private": True,
            "scripts": {
                "dev": "vite",
                "build": "tsc && vite build",
                "preview": "vite preview",
                "tauri": "tauri",
                "tauri:dev": "tauri dev",
                "tauri:build": "tauri build",
            },
            "dependencies": original.get("dependencies", {}),
            "devDependencies": {
                **original.get("devDependencies", {}),
                "@tauri-apps/cli": "^1.5.0",
                "@tauri-apps/api": "^1.5.0",
            },
        }

        package_json_path = tauri_path / "package.json"
        with open(package_json_path, "w") as f:
            json.dump(package_json, f, indent=2)

    def _generate_build_script(self, tauri_path: Path) -> None:
        """Generate shell script for building the app."""
        build_script = """#!/bin/bash
set -e

echo "🔨 Building Tauri application..."

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build the application
echo "🏗️  Building..."
npm run tauri:build

echo "✅ Build complete!"
"""

        script_path = tauri_path / "build.sh"
        with open(script_path, "w") as f:
            f.write(build_script)

        # Make executable
        script_path.chmod(0o755)
