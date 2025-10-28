/**
 * Settings Page - Credential management UI
 *
 * Allows users to view and update their API credentials.
 * This implements Layer 2 of the three-layer credential system.
 */

import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Alert,
  CircularProgress,
  InputAdornment,
  IconButton,
  Divider,
} from '@mui/material';
import { Visibility, VisibilityOff, Save, FolderOpen } from '@mui/icons-material';
import { ConfigManager, AgentConfig } from '../utils/configManager';

export const SettingsPage: React.FC = () => {
  const [config, setConfig] = useState<AgentConfig | null>(null);
  const [configPath, setConfigPath] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isTauriMode, setIsTauriMode] = useState(false);

  const [showKeys, setShowKeys] = useState({
    google: false,
    anthropic: false,
    openai: false,
  });

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    setLoading(true);
    setError(null);

    // Check if running in Tauri (improved detection)
    const tauri = typeof window !== 'undefined' && ('__TAURI__' in window || '__TAURI_INTERNALS__' in window);

    console.log('SettingsPage Tauri detection:', {
      tauri,
      hasTauriGlobal: typeof window !== 'undefined' && '__TAURI__' in window,
      hasTauriInternals: typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window,
      windowKeys: typeof window !== 'undefined' ? Object.keys(window).filter(k => k.includes('TAURI')) : []
    });

    setIsTauriMode(tauri);

    if (!tauri) {
      setError('Settings are only available in the desktop app. In Docker/localhost mode, use .env files for configuration.');
      setLoading(false);
      return;
    }

    try {
      const [loadedConfig, path] = await Promise.all([
        ConfigManager.readConfig(),
        ConfigManager.getConfigPath(),
      ]);

      setConfig(loadedConfig);
      setConfigPath(path);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: keyof AgentConfig) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    if (config) {
      setConfig({ ...config, [field]: event.target.value });
      setError(null);
      setSuccess(null);
    }
  };

  const handleSave = async () => {
    if (!config) return;

    if (!ConfigManager.hasValidCredentials(config)) {
      setError('Please provide at least one valid API key');
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      await ConfigManager.writeConfig(config);
      setSuccess('Configuration saved successfully! Restart the app for changes to take effect.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const toggleShowKey = (key: 'google' | 'anthropic' | 'openai') => {
    setShowKeys({ ...showKeys, [key]: !showKeys[key] });
  };

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ py: 4, textAlign: 'center' }}>
        <CircularProgress />
        <Typography sx={{ mt: 2 }}>Loading settings...</Typography>
      </Container>
    );
  }

  if (!isTauriMode) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h5" gutterBottom>
            Settings
          </Typography>
          <Alert severity="info">
            Settings are only available in the desktop app.
            <br />
            <br />
            For Docker/localhost deployments, configure credentials using <code>.env</code> files in your agent directory.
          </Alert>
        </Paper>
      </Container>
    );
  }

  if (!config) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Paper sx={{ p: 3 }}>
          <Alert severity="error">{error || 'Failed to load configuration'}</Alert>
          <Button onClick={loadConfig} sx={{ mt: 2 }}>
            Retry
          </Button>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
          Settings
        </Typography>

        <Typography variant="body2" color="text.secondary" gutterBottom>
          Manage your API credentials and configuration
        </Typography>

        <Divider sx={{ my: 3 }} />

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {success}
          </Alert>
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {/* Google API Key */}
          <TextField
            label="Google API Key"
            value={config.GOOGLE_API_KEY || ''}
            onChange={handleChange('GOOGLE_API_KEY')}
            type={showKeys.google ? 'text' : 'password'}
            fullWidth
            helperText="For Google ADK agents (Gemini models)"
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => toggleShowKey('google')}
                    edge="end"
                    size="small"
                  >
                    {showKeys.google ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          {/* Google Model */}
          <TextField
            label="Google Model"
            value={config.GOOGLE_MODEL || ''}
            onChange={handleChange('GOOGLE_MODEL')}
            fullWidth
            helperText="Default: gemini-pro"
          />

          {/* Anthropic API Key */}
          <TextField
            label="Anthropic API Key"
            value={config.ANTHROPIC_API_KEY || ''}
            onChange={handleChange('ANTHROPIC_API_KEY')}
            type={showKeys.anthropic ? 'text' : 'password'}
            fullWidth
            helperText="For AWS Strands agents (Claude models)"
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => toggleShowKey('anthropic')}
                    edge="end"
                    size="small"
                  >
                    {showKeys.anthropic ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          {/* OpenAI API Key */}
          <TextField
            label="OpenAI API Key"
            value={config.OPENAI_API_KEY || ''}
            onChange={handleChange('OPENAI_API_KEY')}
            type={showKeys.openai ? 'text' : 'password'}
            fullWidth
            helperText="For LangChain/CrewAI agents (GPT models)"
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => toggleShowKey('openai')}
                    edge="end"
                    size="small"
                  >
                    {showKeys.openai ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          {/* AWS Region */}
          <TextField
            label="AWS Region"
            value={config.AWS_REGION || ''}
            onChange={handleChange('AWS_REGION')}
            fullWidth
            helperText="For AWS Strands agents"
          />

          {/* MCP Server URL */}
          <TextField
            label="MCP Server URL (Optional)"
            value={config.MCP_SERVER_URL || ''}
            onChange={handleChange('MCP_SERVER_URL')}
            fullWidth
            helperText="Model Context Protocol server endpoint"
            placeholder="http://localhost:8080/mcp"
          />
        </Box>

        <Divider sx={{ my: 3 }} />

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FolderOpen fontSize="small" color="action" />
            <Typography variant="caption" color="text.secondary">
              {configPath}
            </Typography>
          </Box>

          <Button
            variant="contained"
            startIcon={saving ? <CircularProgress size={20} /> : <Save />}
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </Box>

        <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
          Changes require an app restart to take effect.
        </Typography>
      </Paper>
    </Container>
  );
};
