import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  useTheme,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import Navigation from './Navigation';

const Header: React.FC = () => {
  const theme = useTheme();
  const [navigationOpen, setNavigationOpen] = useState(false);

  const handleToggleNavigation = () => {
    setNavigationOpen(!navigationOpen);
  };

  return (
    <>
      <AppBar 
        position="fixed" 
        sx={{ 
          zIndex: theme.zIndex.drawer + 1,
          backgroundColor: theme.palette.primary.dark,
        }}
      >
        <Toolbar 
          sx={{ 
            minHeight: { xs: '48px', sm: '56px' },
            px: { xs: 2, sm: 4 },
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Box sx={{ display: 'flex', flexDirection: 'column' }}>
            <Typography 
              variant="h6" 
              component="h1"
              sx={{
                fontSize: { xs: '0.875rem', sm: '1rem' },
                fontWeight: 500,
                margin: 0,
                lineHeight: 1.2,
                color: 'white',
              }}
            >
              Any Agent
            </Typography>
          </Box>
          
          <IconButton
            edge="end"
            color="inherit"
            aria-label="menu"
            onClick={handleToggleNavigation}
            sx={{
              width: { xs: 32, sm: 40 },
              height: { xs: 32, sm: 40 },
              '& .MuiSvgIcon-root': {
                fontSize: { xs: '1.25rem', sm: '1.5rem' },
              },
            }}
          >
            <MenuIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Navigation 
        open={navigationOpen} 
        onClose={() => setNavigationOpen(false)} 
      />
    </>
  );
};

export default Header;