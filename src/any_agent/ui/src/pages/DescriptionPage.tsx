import React from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Link,
  Grid,
  useTheme,
} from '@mui/material';
import { CheckCircle as CheckCircleIcon } from '@mui/icons-material';
import { AgentMetadata, ApiEndpoint } from '@/types';

interface DescriptionPageProps {
  agentMetadata: AgentMetadata | null;
}

const apiEndpoints: ApiEndpoint[] = [
  {
    method: 'GET',
    path: '/health',
    description: 'Health check endpoint',
  },
  {
    method: 'GET',
    path: '/describe',
    description: 'Agent description page',
  },
  {
    method: 'GET',
    path: '/.well-known/agent-card.json',
    description: 'Agent discovery card',
  },
  {
    method: 'POST',
    path: '/',
    description: 'A2A JSON-RPC message endpoint',
  },
];

const DescriptionPage: React.FC<DescriptionPageProps> = ({ agentMetadata }) => {
  const theme = useTheme();

  const getMethodChipColor = (method: string): 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning' => {
    switch (method) {
      case 'GET':
        return 'primary';
      case 'POST':
        return 'success';
      case 'PUT':
        return 'warning';
      case 'DELETE':
        return 'error';
      default:
        return 'info';
    }
  };

  const formatCurlCommand = (endpoint: ApiEndpoint, port: number = 8080) => {
    return `curl http://localhost:${port}${endpoint.path}`;
  };

  return (
    <Container 
      maxWidth="lg" 
      sx={{ 
        mt: { xs: 8, sm: 9 },
        mb: { xs: 8, sm: 9 },
        px: { xs: 2, sm: 3 },
      }}
    >
      {/* Agent Information Section */}
      <Box sx={{ mb: 4 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card elevation={1}>
              <CardContent>
                <Typography variant="h5" component="h3" gutterBottom>
                  Agent Information
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" component="dt" sx={{ fontWeight: 500 }}>
                    Framework:
                  </Typography>
                  <Typography variant="body1" component="dd" sx={{ ml: 0, mb: 1 }}>
                    {agentMetadata?.framework || 'Unknown'}
                  </Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" component="dt" sx={{ fontWeight: 500 }}>
                    Model:
                  </Typography>
                  <Typography variant="body1" component="dd" sx={{ ml: 0, mb: 1 }}>
                    {agentMetadata?.model || 'Not specified'}
                  </Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" component="dt" sx={{ fontWeight: 500 }}>
                    Port:
                  </Typography>
                  <Typography variant="body1" component="dd" sx={{ ml: 0, mb: 1 }}>
                    {agentMetadata?.port || 8080}
                  </Typography>
                </Box>
                <Box sx={{ mb: 0 }}>
                  <Typography variant="body2" color="text.secondary" component="dt" sx={{ fontWeight: 500 }}>
                    Status:
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                    <CheckCircleIcon sx={{ fontSize: 16, color: 'success.main' }} />
                    <Typography variant="body1" sx={{ color: 'success.main', fontWeight: 500 }}>
                      Active
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card elevation={1}>
              <CardContent>
                <Typography variant="h5" component="h3" gutterBottom>
                  Description
                </Typography>
                <Typography variant="body1" paragraph>
                  AI agent containerized using Any Agent Framework and accessible via the A2A protocol.
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  This agent provides standardized APIs for integration with various AI frameworks.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* API Endpoints Section */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h2" gutterBottom sx={{ mb: 3 }}>
          API Endpoints
        </Typography>
        
        <TableContainer component={Paper} elevation={1}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 500 }}>Method</TableCell>
                <TableCell sx={{ fontWeight: 500 }}>Endpoint</TableCell>
                <TableCell sx={{ fontWeight: 500 }}>Description</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {apiEndpoints.map((endpoint, index) => (
                <TableRow 
                  key={index}
                  sx={{ 
                    '&:hover': { 
                      backgroundColor: theme.palette.action.hover,
                    },
                  }}
                >
                  <TableCell>
                    <Chip
                      label={endpoint.method}
                      color={getMethodChipColor(endpoint.method)}
                      size="small"
                      sx={{
                        fontFamily: '"Roboto Mono", monospace',
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        minWidth: 60,
                      }}
                    />
                  </TableCell>
                  <TableCell>
                    <Box
                      component="code"
                      sx={{
                        backgroundColor: theme.palette.grey[100],
                        px: 1,
                        py: 0.5,
                        borderRadius: 1,
                        fontFamily: '"Roboto Mono", monospace',
                        fontSize: '0.875rem',
                      }}
                    >
                      {endpoint.path === '/health' || endpoint.path === '/describe' || endpoint.path === '/.well-known/agent-card.json' ? (
                        <Link 
                          href={endpoint.path} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          color="primary"
                          underline="hover"
                        >
                          {endpoint.path}
                        </Link>
                      ) : (
                        endpoint.path
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {endpoint.description}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>

      {/* Usage Examples Section */}
      <Box>
        <Typography variant="h4" component="h2" gutterBottom sx={{ mb: 3 }}>
          Usage Examples
        </Typography>
        
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" component="h3" gutterBottom>
            Health Check
          </Typography>
          <Paper
            sx={{
              backgroundColor: theme.palette.grey[900],
              color: theme.palette.common.white,
              p: 2,
              borderRadius: 2,
              fontFamily: '"Roboto Mono", monospace',
              fontSize: '0.875rem',
              overflow: 'auto',
            }}
          >
            <code>{formatCurlCommand(apiEndpoints[0], agentMetadata?.port)}</code>
          </Paper>
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" component="h3" gutterBottom>
            Agent Description
          </Typography>
          <Paper
            sx={{
              backgroundColor: theme.palette.grey[900],
              color: theme.palette.common.white,
              p: 2,
              borderRadius: 2,
              fontFamily: '"Roboto Mono", monospace',
              fontSize: '0.875rem',
              overflow: 'auto',
            }}
          >
            <code>{formatCurlCommand(apiEndpoints[1], agentMetadata?.port)}</code>
          </Paper>
        </Box>

        <Box>
          <Typography variant="h6" component="h3" gutterBottom>
            Agent Discovery
          </Typography>
          <Paper
            sx={{
              backgroundColor: theme.palette.grey[900],
              color: theme.palette.common.white,
              p: 2,
              borderRadius: 2,
              fontFamily: '"Roboto Mono", monospace',
              fontSize: '0.875rem',
              overflow: 'auto',
            }}
          >
            <code>{formatCurlCommand(apiEndpoints[2], agentMetadata?.port)}</code>
          </Paper>
        </Box>
      </Box>
    </Container>
  );
};

export default DescriptionPage;