import React from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';

interface LoadingIndicatorProps {
  message?: string;
  size?: number;
}

const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({ 
  message = 'Loading...', 
  size = 16 
}) => {
  return (
    <Box
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 1,
        fontSize: '0.875rem',
        color: 'text.secondary',
      }}
    >
      <Typography variant="body2" component="span">
        {message}
      </Typography>
      <CircularProgress
        size={size}
        thickness={4}
        sx={{
          color: 'primary.main',
        }}
      />
    </Box>
  );
};

export default LoadingIndicator;