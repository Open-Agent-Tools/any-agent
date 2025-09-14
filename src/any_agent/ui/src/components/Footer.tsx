import React from 'react';
import { Box, Typography, useTheme } from '@mui/material';
import { AgentMetadata } from '@/types';

interface FooterProps {
  agentMetadata: AgentMetadata | null;
}

const Footer: React.FC<FooterProps> = ({ agentMetadata }) => {
  const theme = useTheme();

  const getFrameworkDisplayName = (framework: string): string => {
    switch (framework?.toLowerCase()) {
      case 'adk':
        return 'Google ADK';
      case 'aws-strands':
        return 'AWS Strands';
      case 'langchain':
        return 'LangChain';
      case 'crewai':
        return 'CrewAI';
      case 'langgraph':
        return 'LangGraph';
      default:
        return framework ? framework.charAt(0).toUpperCase() + framework.slice(1) : 'Unknown';
    }
  };

  return (
    <Box
      component="footer"
      sx={{
        backgroundColor: theme.palette.grey[100],
        color: theme.palette.text.secondary,
        textAlign: 'center',
        py: 1,
        px: { xs: 2, sm: 4 },
        borderTop: `1px solid ${theme.palette.divider}`,
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: theme.zIndex.appBar,
      }}
    >
      <Typography
        variant="caption"
        component="p"
        sx={{
          margin: 0,
          fontSize: '0.75rem',
          lineHeight: 1.4,
        }}
      >
{getFrameworkDisplayName(agentMetadata?.framework || 'unknown')} Agent • 
        Powered by Any Agent Framework • 
        A2A Protocol Compatible
      </Typography>
    </Box>
  );
};

export default Footer;