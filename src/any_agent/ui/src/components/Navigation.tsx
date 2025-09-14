import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Typography,
  Box,
  Backdrop,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import { Link, useLocation } from 'react-router-dom';

interface NavigationProps {
  open: boolean;
  onClose: () => void;
}

const navigationItems = [
  { text: 'Chat Interface', path: '/' },
  { text: 'Agent Description', path: '/describe' },
  { text: 'Health Check', path: '/health', external: true },
  { text: 'Agent Card', path: '/.well-known/agent-card.json', external: true },
];

const Navigation: React.FC<NavigationProps> = ({ open, onClose }) => {
  const theme = useTheme();
  const location = useLocation();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const drawerWidth = isMobile ? 250 : 300;

  const handleLinkClick = () => {
    onClose();
  };

  const drawerContent = (
    <Box
      sx={{
        width: drawerWidth,
        height: '100%',
        p: { xs: 2, sm: 3 },
        backgroundColor: theme.palette.background.paper,
      }}
    >
      <Typography
        variant="h6"
        component="h3"
        sx={{
          color: theme.palette.primary.main,
          mb: 2,
          fontSize: '1.25rem',
          fontWeight: 500,
        }}
      >
        API Documentation
      </Typography>
      
      <List sx={{ p: 0 }}>
        {navigationItems.map((item) => (
          <ListItem key={item.text} sx={{ p: 0 }}>
            <ListItemButton
              component={item.external ? 'a' : Link}
              to={item.external ? undefined : item.path}
              href={item.external ? item.path : undefined}
              target={item.external ? '_blank' : undefined}
              rel={item.external ? 'noopener noreferrer' : undefined}
              onClick={handleLinkClick}
              sx={{
                py: 1,
                px: 0,
                borderBottom: `1px solid ${theme.palette.divider}`,
                '&:hover': {
                  backgroundColor: 'transparent',
                  '& .MuiListItemText-primary': {
                    color: theme.palette.primary.main,
                  },
                },
                ...(location.pathname === item.path && !item.external && {
                  '& .MuiListItemText-primary': {
                    color: theme.palette.primary.main,
                    fontWeight: 500,
                  },
                }),
              }}
            >
              <ListItemText
                primary={item.text}
                sx={{
                  '& .MuiListItemText-primary': {
                    fontSize: '0.95rem',
                    color: theme.palette.text.secondary,
                    transition: 'color 0.2s ease',
                  },
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <>
      {/* Backdrop for mobile */}
      <Backdrop
        open={open}
        onClick={onClose}
        sx={{
          zIndex: theme.zIndex.drawer - 1,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
        }}
      />
      
      {/* Drawer */}
      <Drawer
        anchor="right"
        open={open}
        onClose={onClose}
        variant="temporary"
        ModalProps={{
          keepMounted: true, // Better open performance on mobile
        }}
        sx={{
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxShadow: '0 10px 15px rgba(0, 0, 0, 0.1)',
          },
        }}
      >
        {drawerContent}
      </Drawer>
    </>
  );
};

export default Navigation;