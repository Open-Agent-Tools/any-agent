/**
 * Config Manager - Wrapper for Tauri config management commands
 *
 * Provides a clean TypeScript interface for reading and writing
 * agent credentials to platform-specific config files.
 */

// Check if we're running in Tauri environment
const isTauri = () => {
  if (typeof window === 'undefined') return false;

  // Tauri v2 detection - check multiple possible locations
  // @ts-ignore
  const hasTauri = '__TAURI__' in window || '__TAURI_INTERNALS__' in window;

  console.log('Tauri detection:', {
    hasTauri,
    hasTauriGlobal: '__TAURI__' in window,
    hasTauriInternals: '__TAURI_INTERNALS__' in window,
    windowKeys: Object.keys(window).filter(k => k.includes('TAURI'))
  });

  return hasTauri;
};

// Type-safe Tauri API access
const getTauriAPI = () => {
  if (!isTauri()) {
    console.warn('Tauri API not available - running in browser mode');
    return null;
  }
  // @ts-ignore - Tauri is injected at runtime
  return window.__TAURI__ || window.__TAURI_INTERNALS__;
};

export interface AgentConfig {
  GOOGLE_API_KEY?: string;
  ANTHROPIC_API_KEY?: string;
  OPENAI_API_KEY?: string;
  AWS_REGION?: string;
  GOOGLE_MODEL?: string;
  MCP_SERVER_URL?: string;
  [key: string]: string | undefined;
}

export class ConfigManager {
  /**
   * Check if config file exists
   */
  static async configExists(): Promise<boolean> {
    const tauri = getTauriAPI();
    if (!tauri) return false;

    try {
      const result = await tauri.invoke('config_exists');
      return result as boolean;
    } catch (error) {
      console.error('Failed to check config existence:', error);
      return false;
    }
  }

  /**
   * Get the path to the config file
   */
  static async getConfigPath(): Promise<string> {
    const tauri = getTauriAPI();
    if (!tauri) return 'Config path not available (browser mode)';

    try {
      const result = await tauri.invoke('get_config_path');
      return result as string;
    } catch (error) {
      console.error('Failed to get config path:', error);
      throw new Error('Failed to get config path');
    }
  }

  /**
   * Read the current configuration
   * Returns default template if config doesn't exist
   */
  static async readConfig(): Promise<AgentConfig> {
    if (!isTauri()) {
      console.log('Not in Tauri mode, returning default config');
      // Return default config for browser mode
      return {
        GOOGLE_API_KEY: '',
        ANTHROPIC_API_KEY: '',
        OPENAI_API_KEY: '',
        AWS_REGION: 'us-west-2',
        GOOGLE_MODEL: 'gemini-pro',
        MCP_SERVER_URL: '',
      };
    }

    const tauri = getTauriAPI();
    if (!tauri) {
      console.error('Tauri detected but API not available');
      throw new Error('Tauri API not available');
    }

    try {
      const result = await tauri.invoke('read_config');
      return result as AgentConfig;
    } catch (error) {
      console.error('Failed to read config:', error);
      throw new Error('Failed to read configuration');
    }
  }

  /**
   * Write configuration to file
   * Creates config directory if it doesn't exist
   */
  static async writeConfig(config: AgentConfig): Promise<void> {
    const tauri = getTauriAPI();
    if (!tauri) {
      console.warn('Cannot write config in browser mode');
      return;
    }

    try {
      await tauri.invoke('write_config', { config });
    } catch (error) {
      console.error('Failed to write config:', error);
      throw new Error('Failed to save configuration');
    }
  }

  /**
   * Check if a config has valid credentials
   * (at least one API key is set)
   */
  static hasValidCredentials(config: AgentConfig): boolean {
    const apiKeys = [
      config.GOOGLE_API_KEY,
      config.ANTHROPIC_API_KEY,
      config.OPENAI_API_KEY,
    ];

    return apiKeys.some(key => key && key.trim() !== '' && !key.startsWith('your-'));
  }

  /**
   * Mask sensitive values for display
   */
  static maskValue(value: string | undefined): string {
    if (!value || value === '' || value.startsWith('your-')) {
      return '';
    }
    if (value.length < 8) {
      return '••••••';
    }
    return value.substring(0, 4) + '••••••••' + value.substring(value.length - 4);
  }
}
