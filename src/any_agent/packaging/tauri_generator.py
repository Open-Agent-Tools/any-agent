"""Tauri project structure generator."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from any_agent.packaging.agent_bundler import AgentBundler


class TauriProjectGenerator:
    """Generates Tauri project structure for packaging agents."""

    def __init__(self) -> None:
        """Initialize the TauriProjectGenerator."""
        self.ui_source_path = Path(__file__).parent.parent / "ui"

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """
        Sanitize a name for use in filenames.

        Args:
            name: The name to sanitize

        Returns:
            Sanitized name safe for filesystem use
        """
        # Replace spaces and problematic characters with hyphens
        sanitized = name.replace(" ", "-").replace("_", "-")
        # Remove any other potentially problematic characters
        sanitized = "".join(c for c in sanitized if c.isalnum() or c in ("-", "."))
        return sanitized

    def generate_project(
        self,
        tauri_path: Path,
        metadata: Dict[str, str],
        agent_path: Path,
        bundle_agent: bool = False,
        framework: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate complete Tauri project structure.

        Args:
            tauri_path: Path where Tauri project will be created
            metadata: Application metadata
            agent_path: Path to the agent directory
            bundle_agent: If True, bundle the agent as a sidecar executable
            framework: Framework type (auto-detected if None)

        Returns:
            Dict with success status and optional sidecar_path
        """
        try:
            # Create directory structure
            self._create_directory_structure(tauri_path)

            # Create placeholder in resources directory
            # This ensures the resources/* glob pattern matches during build
            resources_dir = tauri_path / "src-tauri" / "resources"
            placeholder = resources_dir / ".gitkeep"
            placeholder.touch()

            # Bundle agent if requested
            sidecar_path = None
            if bundle_agent:
                sidecar_result = self._bundle_agent_sidecar(
                    tauri_path, agent_path, metadata["app_name"], framework
                )
                if sidecar_result["success"]:
                    sidecar_path = sidecar_result["sidecar_path"]
                    metadata["sidecar_path"] = sidecar_path
                    metadata["sidecar_name"] = sidecar_result["sidecar_name"]
                else:
                    return sidecar_result

            # Create default icon if none provided
            if not metadata.get("icon_path") or metadata["icon_path"] == "default":
                self._create_default_icon(tauri_path)

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

            result = {"success": True}
            if sidecar_path:
                result["sidecar_path"] = sidecar_path

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_directory_structure(self, tauri_path: Path) -> None:
        """Create the basic Tauri directory structure."""
        directories = [
            tauri_path / "src",
            tauri_path / "src-tauri",
            tauri_path / "src-tauri" / "src",
            tauri_path / "src-tauri" / "icons",
            tauri_path / "src-tauri" / "resources",
            tauri_path / "public",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _bundle_agent_sidecar(
        self,
        tauri_path: Path,
        agent_path: Path,
        app_name: str,
        framework: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Bundle the agent as a Tauri sidecar executable.

        Args:
            tauri_path: Path to the Tauri project
            agent_path: Path to the agent directory
            app_name: Name for the application
            framework: Framework type (auto-detected if None)

        Returns:
            Dict with success status and sidecar_path
        """
        try:
            # Create bundler
            bundler = AgentBundler(agent_path)

            # Bundle the agent
            bundle_output_dir = tauri_path / "src-tauri" / "binaries"
            bundle_output_dir.mkdir(parents=True, exist_ok=True)

            # Sanitize app name for filesystem use
            safe_app_name = self._sanitize_filename(app_name)

            result = bundler.bundle_agent(
                output_dir=bundle_output_dir,
                app_name=f"{safe_app_name}-agent",
                framework=framework,
            )

            if not result["success"]:
                return result

            # Move executable to resources directory for packaging
            executable_path = Path(result["executable_path"])
            sidecar_name = f"{safe_app_name}-agent"

            # Tauri expects sidecars in the resources directory
            # with platform-specific suffixes
            import platform

            system = platform.system().lower()
            machine = platform.machine().lower()

            # Determine platform-specific sidecar filename
            if system == "darwin":
                if machine in ("arm64", "aarch64"):
                    sidecar_filename = f"{sidecar_name}-aarch64-apple-darwin"
                else:  # x86_64
                    sidecar_filename = f"{sidecar_name}-x86_64-apple-darwin"
            elif system == "windows":
                sidecar_filename = f"{sidecar_name}-x86_64-pc-windows-msvc.exe"
            else:  # Linux
                if machine in ("aarch64", "arm64"):
                    sidecar_filename = f"{sidecar_name}-aarch64-unknown-linux-gnu"
                else:
                    sidecar_filename = f"{sidecar_name}-x86_64-unknown-linux-gnu"

            # Copy to binaries directory for Tauri sidecar
            binaries_dir = tauri_path / "src-tauri" / "binaries"
            binaries_dir.mkdir(parents=True, exist_ok=True)
            sidecar_path = binaries_dir / sidecar_filename
            shutil.copy(executable_path, sidecar_path)

            # Make executable on Unix systems
            if system != "windows":
                sidecar_path.chmod(0o755)

            return {
                "success": True,
                "sidecar_path": str(sidecar_path),
                "sidecar_name": sidecar_name,
            }

        except Exception as bundle_error:
            return {
                "success": False,
                "error": f"Failed to bundle agent sidecar: {str(bundle_error)}",
            }

    def _create_default_icon(self, tauri_path: Path) -> None:
        """Create a minimal default icon for Tauri."""
        import zlib
        import struct

        icons_dir = tauri_path / "src-tauri" / "icons"
        icon_path = icons_dir / "icon.png"

        # Create a 32x32 RGBA image with a simple gradient
        width, height = 32, 32

        # Generate pixel data (RGBA format with a teal/blue gradient)
        pixels = bytearray()
        for y in range(height):
            pixels.append(0)  # Filter type (0 = none)
            for x in range(width):
                # Create a simple teal to blue gradient
                r = 0x20 + (x * 2)
                g = 0x80 + (y * 2)
                b = 0xE0 - (x * 2)
                a = 0xFF  # Fully opaque
                pixels.extend([r, g, b, a])

        # Compress the pixel data
        compressed = zlib.compress(bytes(pixels), 9)

        # Build PNG file
        png_data = bytearray()

        # PNG signature
        png_data.extend(b'\x89PNG\r\n\x1a\n')

        # IHDR chunk
        ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
        png_data.extend(struct.pack('>I', len(ihdr_data)))
        png_data.extend(b'IHDR')
        png_data.extend(ihdr_data)
        png_data.extend(struct.pack('>I', zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff))

        # IDAT chunk
        png_data.extend(struct.pack('>I', len(compressed)))
        png_data.extend(b'IDAT')
        png_data.extend(compressed)
        png_data.extend(struct.pack('>I', zlib.crc32(b'IDAT' + compressed) & 0xffffffff))

        # IEND chunk
        png_data.extend(struct.pack('>I', 0))
        png_data.extend(b'IEND')
        png_data.extend(struct.pack('>I', zlib.crc32(b'IEND') & 0xffffffff))

        with open(icon_path, "wb") as f:
            f.write(png_data)

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

        # Replace API_BASE_URL with dynamic version that properly awaits port discovery
        modified_content = content.replace(
            "const API_BASE_URL = '';",
            """import { isTauriEnvironment, getBackendURL } from './tauri_api_adapter';

// Helper to get the API base URL (handles async Tauri port discovery)
async function getApiBaseUrl(): Promise<string> {
  if (isTauriEnvironment()) {
    return await getBackendURL();
  }
  return ''; // Empty string for relative URLs in web context
}""",
        )

        # Update all API methods to await the base URL
        # Replace pattern: `fetch(`${API_BASE_URL}` with `const API_BASE_URL = await getApiBaseUrl(); fetch(`${API_BASE_URL}`
        api_methods = [
            'async getAgentCard(): Promise<AgentMetadata> {',
            'async healthCheck(): Promise<ApiResponse> {',
            'async createChatSession(sessionId: string): Promise<ChatCreateSessionResponse> {',
            'async sendMessage(sessionId: string, message: string): Promise<ChatSendMessageResponse> {',
            'async cleanupSession(sessionId: string): Promise<void> {',
            'async cancelTask(sessionId: string): Promise<ChatCancelTaskResponse> {',
        ]

        for method in api_methods:
            # Find the method and inject API_BASE_URL = await getApiBaseUrl()
            if method in modified_content:
                # Add the await call right after the method signature
                modified_content = modified_content.replace(
                    method,
                    method + '\n    const API_BASE_URL = await getApiBaseUrl();'
                )

        # Fix cleanupSessionBeacon signature to be async
        modified_content = modified_content.replace(
            'cleanupSessionBeacon(sessionId: string): void {',
            'async cleanupSessionBeacon(sessionId: string): Promise<void> {\n    const API_BASE_URL = await getApiBaseUrl();'
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
        # Build sidecar configuration if agent was bundled
        external_bin = []
        if metadata.get("sidecar_name"):
            # Tauri sidecar naming convention
            external_bin.append(f"binaries/{metadata['sidecar_name']}")

        # Build bundle configuration
        bundle_config = {
            "active": True,
            "targets": "all",
            "identifier": f"com.{metadata.get('author', 'anyagent').lower().replace(' ', '').replace('-', '')}.{metadata['app_name'].lower().replace(' ', '').replace('-', '')}",
            "resources": ["resources/*"],
            "externalBin": external_bin,
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

        # Don't add icon configuration - will use default
        # Icons can be added later with: cargo tauri icon path/to/icon.png

        # Tauri v2 configuration
        # Note: In Tauri v2, productName and version come from Cargo.toml
        # Windows are created programmatically in lib.rs, not in config
        config = {
            "$schema": "../node_modules/@tauri-apps/cli/schema.json",
            "identifier": bundle_config["identifier"],
            "build": {
                "beforeDevCommand": "npm run dev",
                "devUrl": "http://localhost:5173",
                "beforeBuildCommand": "npm run build",
                "frontendDist": "../dist"
            },
            "app": {
                "windows": [
                    {
                        "title": metadata["app_name"],
                        "width": 1200,
                        "height": 800,
                        "resizable": True,
                        "fullscreen": False,
                        "devtools": True  # Enable devtools in release builds
                    }
                ],
                "withGlobalTauri": True
            },
            "bundle": {
                "active": True,
                "targets": "all",
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

        config_path = tauri_path / "src-tauri" / "tauri.conf.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

    def _generate_capabilities(self, tauri_path: Path) -> None:
        """Generate Tauri v2 capabilities for permissions."""
        capabilities_dir = tauri_path / "src-tauri" / "capabilities"
        capabilities_dir.mkdir(parents=True, exist_ok=True)

        # Main capability file for the app
        # Tauri v2 uses core:* permissions
        main_capability = {
            "identifier": "main-capability",
            "description": "Capability for the main window",
            "windows": ["main"],
            "permissions": [
                "core:default",
                "core:window:default",
                "core:webview:default",
                "shell:default",
                "shell:allow-open",
                "shell:allow-spawn",
                "shell:allow-execute",
                "shell:allow-kill",
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

        # lib.rs with agent backend management, window creation, and config management
        app_name = metadata["app_name"]
        sidecar_name = metadata.get("sidecar_name")

        # Determine backend port based on framework
        backend_port = metadata.get("port", 8080)  # Default to 8080 if not in metadata

        # Generate different backend startup code based on sidecar availability
        if sidecar_name:
            backend_setup = f"""
            // Start agent sidecar and manage its lifecycle with explicit cleanup
            use tauri_plugin_shell::ShellExt;
            let shell = app.shell();

            eprintln!("Starting agent sidecar: {sidecar_name}");

            let sidecar_command = shell
                .sidecar("{sidecar_name}")
                .map_err(|e| {{
                    eprintln!("Failed to create sidecar command: {{}}", e);
                    e
                }})?;

            let (_rx, child) = sidecar_command.spawn()
                .map_err(|e| {{
                    eprintln!("Failed to spawn sidecar: {{}}", e);
                    e
                }})?;

            // Get the process ID for logging
            let pid = child.pid();
            eprintln!("Agent sidecar started successfully with PID: {{}}", pid);

            // Create process manager that will cleanup on drop
            let process_manager = SidecarProcessManager::new(child, pid);
            app.manage(process_manager);

            eprintln!("Sidecar process manager initialized - cleanup will occur automatically on app exit");
"""
        else:
            backend_setup = """
            // No bundled agent - UI only mode
            eprintln!("Running in UI-only mode (no bundled agent)");
            eprintln!("Connect to an external agent or run the agent separately");
"""

        lib_rs = f"""// Tauri v2 application library
use std::fs;
use std::path::PathBuf;
use tauri::{{Manager, WebviewWindowBuilder, WebviewUrl}};
use tauri::menu::{{Menu, MenuItem, PredefinedMenuItem, Submenu}};
use serde_json::{{Value, json}};

// Process manager for sidecar with automatic cleanup on drop
struct SidecarProcessManager {{
    child: std::sync::Mutex<Option<tauri_plugin_shell::process::CommandChild>>,
    pid: u32,
}}

impl SidecarProcessManager {{
    fn new(child: tauri_plugin_shell::process::CommandChild, pid: u32) -> Self {{
        Self {{
            child: std::sync::Mutex::new(Some(child)),
            pid,
        }}
    }}
}}

impl Drop for SidecarProcessManager {{
    fn drop(&mut self) {{
        eprintln!("SidecarProcessManager dropping - cleaning up process PID: {{}}", self.pid);

        if let Ok(mut child_guard) = self.child.lock() {{
            if let Some(mut child_proc) = child_guard.take() {{
                eprintln!("Attempting to kill sidecar process (PID: {{}})...", self.pid);

                // Try graceful kill first
                match child_proc.kill() {{
                    Ok(_) => {{
                        eprintln!("Successfully sent kill signal to sidecar");
                        // Give it a moment to terminate
                        std::thread::sleep(std::time::Duration::from_millis(500));
                    }},
                    Err(e) => {{
                        eprintln!("Failed to kill sidecar gracefully: {{}}", e);
                    }}
                }}

                // Force kill with SIGKILL on Unix platforms as fallback
                #[cfg(unix)]
                {{
                    use std::process::Command;
                    eprintln!("Sending SIGKILL to PID {{}} as fallback...", self.pid);
                    let _ = Command::new("kill")
                        .args(["-9", &self.pid.to_string()])
                        .output();
                }}
            }}
        }} else {{
            eprintln!("Failed to acquire lock on child process during cleanup");
        }}

        eprintln!("Sidecar cleanup complete");
    }}
}}

// Config management commands
#[tauri::command]
fn get_config_path() -> Result<String, String> {{
    let config_dir = if cfg!(target_os = "macos") {{
        dirs::home_dir()
            .ok_or("Failed to get home directory")?
            .join("Library")
            .join("Application Support")
            .join("AnyAgent")
    }} else if cfg!(target_os = "windows") {{
        dirs::config_dir()
            .ok_or("Failed to get config directory")?
            .join("AnyAgent")
    }} else {{
        dirs::home_dir()
            .ok_or("Failed to get home directory")?
            .join(".config")
            .join("anyagent")
    }};

    let config_file = config_dir.join("config.json");
    Ok(config_file.to_string_lossy().to_string())
}}

#[tauri::command]
fn config_exists() -> bool {{
    if let Ok(path) = get_config_path() {{
        PathBuf::from(path).exists()
    }} else {{
        false
    }}
}}

#[tauri::command]
fn read_config() -> Result<Value, String> {{
    let path = get_config_path()?;
    let path_buf = PathBuf::from(&path);

    if !path_buf.exists() {{
        // Return default template config
        return Ok(json!({{
            "GOOGLE_API_KEY": "",
            "ANTHROPIC_API_KEY": "",
            "OPENAI_API_KEY": "",
            "AWS_REGION": "us-west-2",
            "GOOGLE_MODEL": "gemini-pro",
        }}));
    }}

    let contents = fs::read_to_string(&path_buf)
        .map_err(|e| format!("Failed to read config: {{}}", e))?;

    let config: Value = serde_json::from_str(&contents)
        .map_err(|e| format!("Failed to parse config: {{}}", e))?;

    Ok(config)
}}

#[tauri::command]
fn write_config(config: Value) -> Result<(), String> {{
    let path = get_config_path()?;
    let path_buf = PathBuf::from(&path);

    // Create parent directory if it doesn't exist
    if let Some(parent) = path_buf.parent() {{
        fs::create_dir_all(parent)
            .map_err(|e| format!("Failed to create config directory: {{}}", e))?;
    }}

    // Write config file
    let contents = serde_json::to_string_pretty(&config)
        .map_err(|e| format!("Failed to serialize config: {{}}", e))?;

    fs::write(&path_buf, contents)
        .map_err(|e| format!("Failed to write config: {{}}", e))?;

    Ok(())
}}

// Backend port discovery for frontend A2A client
#[tauri::command]
fn get_backend_port() -> u16 {{
    // Return the agent backend port (framework-specific)
    {backend_port}
}}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {{
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            get_config_path,
            config_exists,
            read_config,
            write_config,
            get_backend_port
        ])
        .setup(|app| {{
            // Create menu with Developer Tools option
            let view_menu = Submenu::with_items(
                app,
                "View",
                true,
                &[
                    &MenuItem::with_id(app, "dev_tools", "Developer Tools", true, Some("CmdOrCtrl+Shift+I"))?
                ]
            )?;

            let menu = Menu::with_items(
                app,
                &[
                    &PredefinedMenuItem::about(app, None, None)?,
                    &view_menu
                ]
            )?;

            // Set the application-level menu (for macOS menu bar)
            app.set_menu(menu)?;

            // Handle menu events
            app.on_menu_event(move |_app_handle, _event| {{
                // DevTools are enabled via configuration and keyboard shortcut (Cmd+Shift+I)
                // The menu item serves as a visual reminder of the shortcut
            }});

            {backend_setup}

            Ok(())
        }})
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}}
"""
        lib_rs_path = tauri_path / "src-tauri" / "src" / "lib.rs"
        with open(lib_rs_path, "w") as f:
            f.write(lib_rs)

    def _generate_cargo_toml(self, tauri_path: Path, metadata: Dict[str, str]) -> None:
        """Generate Cargo.toml for Rust project."""
        app_name = metadata["app_name"].lower().replace(" ", "-")
        cargo_toml = f'''[package]
name = "{app_name}"
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

[[bin]]
name = "{app_name}"
path = "src/main.rs"

[build-dependencies]
tauri-build = {{ version = "2", features = [] }}

[dependencies]
tauri = {{ version = "2", features = [] }}
tauri-plugin-shell = "2"
serde = {{ version = "1", features = ["derive"] }}
serde_json = "1"
dirs = "5"

[features]
default = ["custom-protocol"]
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
                "@tauri-apps/cli": "^2.0.0",
                "@tauri-apps/api": "^2.0.0",
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
