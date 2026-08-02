import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Box,
  Typography,
  Divider,
} from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';
import { SIDEBAR_ITEMS } from '../constants/navigation';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  drawerWidth?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ open, onClose, drawerWidth = 260 }) => {
  const location = useLocation();
  const navigate = useNavigate();

  const handleNavigate = (path: string) => {
    navigate(path);
  };

  const drawerContent = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', py: 2 }}>
      <Box sx={{ px: 3, pb: 2 }}>
        <Typography
          variant="caption"
          sx={{
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            color: '#94A3B8',
            fontSize: '0.7rem',
          }}
        >
          Navigation Menu
        </Typography>
      </Box>

      <List sx={{ flexGrow: 1, px: 1.5, py: 0 }}>
        {SIDEBAR_ITEMS.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <ListItem key={item.id} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                onClick={() => handleNavigate(item.path)}
                selected={isActive}
                sx={{
                  borderRadius: '10px',
                  py: 1.2,
                  px: 2,
                  color: isActive ? '#1E3A8A' : '#475569',
                  backgroundColor: isActive ? '#EFF6FF' : 'transparent',
                  fontWeight: isActive ? 600 : 400,
                  '&.Mui-selected': {
                    backgroundColor: '#EFF6FF',
                    color: '#1E3A8A',
                    '&:hover': {
                      backgroundColor: '#DBEAFE',
                    },
                  },
                  '&:hover': {
                    backgroundColor: '#F1F5F9',
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 40,
                    color: isActive ? '#1E3A8A' : '#64748B',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.title}
                  primaryTypographyProps={{
                    fontSize: '0.9rem',
                    fontWeight: isActive ? 600 : 500,
                  }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      <Divider sx={{ my: 2, mx: 2 }} />

      <Box sx={{ px: 3, py: 1 }}>
        <Typography variant="caption" sx={{ color: '#94A3B8', display: 'block' }}>
          Saamu Tailors v1.0
        </Typography>
        <Typography variant="caption" sx={{ color: '#CBD5E1', display: 'block' }}>
          ERP Foundation Sprint
        </Typography>
      </Box>
    </Box>
  );

  return (
    <>
      {/* Mobile Drawer */}
      <Drawer
        variant="temporary"
        open={open}
        onClose={onClose}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
            backgroundColor: '#FFFFFF',
            borderRight: '1px solid #E2E8F0',
          },
        }}
      >
        {drawerContent}
      </Drawer>

      {/* Desktop Permanent Drawer */}
      <Drawer
        variant="persistent"
        open={open}
        sx={{
          display: { xs: 'none', md: 'block' },
          width: open ? drawerWidth : 0,
          flexShrink: 0,
          transition: (theme) =>
            theme.transitions.create('width', {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
            top: '64px',
            height: 'calc(100% - 64px)',
            backgroundColor: '#FFFFFF',
            borderRight: '1px solid #E2E8F0',
          },
        }}
      >
        {drawerContent}
      </Drawer>
    </>
  );
};
