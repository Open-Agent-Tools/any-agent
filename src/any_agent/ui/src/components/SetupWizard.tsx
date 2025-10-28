/**
 * Setup Wizard - First-run credential configuration
 *
 * Modal dialog that appears on first launch to collect API credentials.
 * This implements Layer 3 of the three-layer credential system.
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Box,
  Alert,
  CircularProgress,
  InputAdornment,
  IconButton,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { ConfigManager, AgentConfig } from '../utils/configManager';

interface SetupWizardProps {
  open: boolean;
  onComplete: () => void;
}

export const SetupWizard: React.FC<SetupWizardProps> = ({ open, onComplete }) => {
  const [config, setConfig] = useState<AgentConfig>({
    GOOGLE_API_KEY: '',
    GOOGLE_MODEL: 'gemini-pro',
    ANTHROPIC_API_KEY: '',
    OPENAI_API_KEY: '',
    AWS_REGION: 'us-west-2',
    MCP_SERVER_URL: '',
  });

  const [showKeys, setShowKeys] = useState({
    google: false,
    anthropic: false,
    openai: false,
  });

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (field: keyof AgentConfig) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setConfig({ ...config, [field]: event.target.value });
    setError(null);
  };

  const handleSave = async () => {
    // Validate that at least one API key is provided
    if (!ConfigManager.hasValidCredentials(config)) {
      setError('Please provide at least one API key to continue');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      await ConfigManager.writeConfig(config);
      onComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save configuration');
      setSaving(false);
    }
  };

  const toggleShowKey = (key: 'google' | 'anthropic' | 'openai') => {
    setShowKeys({ ...showKeys, [key]: !showKeys[key] });
  };

  return (
    <Dialog
      open={open}
      maxWidth="sm"
      fullWidth
      disableEscapeKeyDown
      aria-labelledby="setup-wizard-title"
    >
      <DialogTitle id="setup-wizard-title">
        Welcome to Any Agent
      </DialogTitle>

      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          To get started, please provide your API credentials. You'll need at least one
          API key depending on which agent framework you're using.
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
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
            helperText="For AWS Strands agents (default: us-west-2)"
          />

          {/* MCP Server URL (Optional) */}
          <TextField
            label="MCP Server URL (Optional)"
            value={config.MCP_SERVER_URL || ''}
            onChange={handleChange('MCP_SERVER_URL')}
            fullWidth
            helperText="Model Context Protocol server endpoint"
            placeholder="http://localhost:8080/mcp"
          />
        </Box>

        <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
          Your credentials are stored locally and never sent to any external servers.
        </Typography>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={saving}
          startIcon={saving ? <CircularProgress size={20} /> : null}
        >
          {saving ? 'Saving...' : 'Save and Continue'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
