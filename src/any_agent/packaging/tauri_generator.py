"""Tauri project structure generator."""

import json
import shutil
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

            # Generate Tauri configuration
            self._generate_tauri_config(tauri_path, metadata)

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

    def _generate_tauri_config(
        self, tauri_path: Path, metadata: Dict[str, str]
    ) -> None:
        """Generate tauri.conf.json."""
        config = {
            "build": {
                "beforeDevCommand": "npm run dev",
                "beforeBuildCommand": "npm run build",
                "devPath": "http://localhost:1420",
                "distDir": "../dist",
            },
            "package": {
                "productName": metadata["app_name"],
                "version": metadata["version"],
            },
            "tauri": {
                "allowlist": {
                    "all": False,
                    "shell": {"all": False, "open": True},
                    "dialog": {"all": False, "open": False},
                    "fs": {
                        "all": False,
                        "readFile": True,
                        "writeFile": True,
                        "exists": True,
                        "scope": ["$APPDATA/*", "$HOME/Library/Application Support/*"],
                    },
                    "http": {
                        "all": False,
                        "request": True,
                        "scope": ["http://localhost:*"],
                    },
                },
                "bundle": {
                    "active": True,
                    "targets": "all",
                    "identifier": f"com.{metadata['author'].lower().replace(' ', '')}.{metadata['app_name'].lower().replace(' ', '')}",
                    "icon": [
                        "icons/32x32.png",
                        "icons/128x128.png",
                        "icons/128x128@2x.png",
                        "icons/icon.icns",
                        "icons/icon.ico",
                    ],
                    "resources": ["resources/*"],
                    "externalBin": ["binaries/python-runtime"],
                    "copyright": f"Copyright © {metadata['author']}",
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
                },
                "security": {"csp": None},
                "windows": [
                    {
                        "fullscreen": False,
                        "resizable": True,
                        "title": metadata["app_name"],
                        "width": 1200,
                        "height": 800,
                        "minWidth": 800,
                        "minHeight": 600,
                    }
                ],
            },
        }

        config_path = tauri_path / "src-tauri" / "tauri.conf.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

    def _generate_rust_main(self, tauri_path: Path, metadata: Dict[str, str]) -> None:
        """Generate Rust main.rs file."""
        main_rs = """// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Command, Stdio};
use std::sync::Mutex;
use tauri::State;

struct AppState {
    python_child: Mutex<Option<std::process::Child>>,
}

#[tauri::command]
fn get_backend_port(state: State<AppState>) -> Result<u16, String> {
    // Port will be set by Python backend via environment variable
    std::env::var("AGENT_PORT")
        .ok()
        .and_then(|p| p.parse().ok())
        .ok_or_else(|| "Backend port not available yet".to_string())
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            // Get the resource directory
            let resource_dir = app.path_resolver()
                .resource_dir()
                .expect("failed to resolve resource dir");

            // Start Python backend as subprocess
            let python_runtime = resource_dir.join("python-runtime/run_agent.py");

            let child = Command::new("python3")
                .arg(python_runtime)
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .spawn()
                .expect("Failed to start Python backend");

            // Store the child process handle
            app.manage(AppState {
                python_child: Mutex::new(Some(child)),
            });

            Ok(())
        })
        .on_window_event(|event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event.event() {
                // Cleanup Python process on window close
                // This is automatically handled when the app exits
            }
        })
        .invoke_handler(tauri::generate_handler![get_backend_port])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
"""

        main_rs_path = tauri_path / "src-tauri" / "src" / "main.rs"
        with open(main_rs_path, "w") as f:
            f.write(main_rs)

    def _generate_cargo_toml(self, tauri_path: Path, metadata: Dict[str, str]) -> None:
        """Generate Cargo.toml for Rust project."""
        cargo_toml = f'''[package]
name = "{metadata["app_name"].lower().replace(" ", "-")}"
version = "{metadata["version"]}"
description = "{metadata["description"]}"
authors = ["{metadata["author"]}"]
license = ""
repository = ""
edition = "2021"

# See more keys and their definitions at https://doc.rust-lang.org/cargo/reference/manifest.html

[build-dependencies]
tauri-build = {{ version = "1.5", features = [] }}

[dependencies]
tauri = {{ version = "1.5", features = ["shell-open"] }}
serde = {{ version = "1.0", features = ["derive"] }}
serde_json = "1.0"

[features]
# This feature is used for production builds or when `devPath` points to the filesystem
custom-protocol = ["tauri/custom-protocol"]
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
