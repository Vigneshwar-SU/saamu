import React from 'react';
import {
  Box,
  Divider,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  useMediaQuery,
} from '@mui/material';
import type { Theme } from '@mui/material/styles';
import { useLocation, useNavigate } from 'react-router-dom';
import { NAV_GROUPS, SIDEBAR_ITEMS } from '../constants/navigation';
import { useAuth } from '../context/useAuth';
import { BrandMark } from './ui/BrandMark';
import type { NavItem } from '../types/navigation';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  drawerWidth?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ open, onClose, drawerWidth = 272 }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { role, user } = useAuth();
  const isMobile = useMediaQuery((theme: Theme) => theme.breakpoints.down('md'));

  const visibleItems = SIDEBAR_ITEMS.filter(
    (item) => !item.roles || (role != null && item.roles.includes(role))
  );

  const isActive = (item: NavItem) =>
    location.pathname === item.path || location.pathname.startsWith(`${item.path}/`);

  const handleNavigate = (path: string) => {
    navigate(path);
    if (isMobile) onClose();
  };

  const drawerContent = (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: '#FFFFFF',
      }}
    >
      {/* Brand */}
      <Box sx={{ px: 2.5, py: 2.25, display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <BrandMark size={42} />
        <Box sx={{ minWidth: 0 }}>
          <Typography
            sx={{
              fontWeight: 800,
              fontSize: '1.05rem',
              lineHeight: 1.2,
              color: '#242424',
              letterSpacing: '-0.01em',
            }}
          >
            Saamu Tailors
          </Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary', lineHeight: 1 }}>
            Management System
          </Typography>
        </Box>
      </Box>

      <Divider sx={{ mx: 2.5 }} />

      {/* Navigation */}
      <Box sx={{ flexGrow: 1, overflowY: 'auto', py: 1.5 }}>
        {NAV_GROUPS.map((group) => {
          const groupItems = visibleItems.filter((item) => item.group?.id === group.id);
          if (groupItems.length === 0) return null;
          return (
            <Box key={group.id} sx={{ px: 1.5, mb: 0.5 }}>
              <Typography
                variant="caption"
                sx={{
                  px: 1.5,
                  pt: 1,
                  pb: 0.5,
                  display: 'block',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  color: '#A29B8E',
                  fontSize: '0.68rem',
                }}
              >
                {group.label}
              </Typography>
              <List sx={{ py: 0 }}>
                {groupItems.map((item) => {
                  const active = isActive(item);
                  return (
                    <ListItem key={item.id} disablePadding sx={{ mb: 0.25 }}>
                      <ListItemButton
                        onClick={() => handleNavigate(item.path)}
                        selected={active}
                        sx={{
                          borderRadius: '10px',
                          py: 1.05,
                          px: 1.75,
                          color: active ? '#7A5E0C' : '#5A5448',
                          fontWeight: active ? 600 : 500,
                          position: 'relative',
                          '&::before': {
                            content: '""',
                            position: 'absolute',
                            left: 0,
                            top: '22%',
                            bottom: '22%',
                            width: 3,
                            borderRadius: 2,
                            backgroundColor: active ? '#A98216' : 'transparent',
                          },
                          '&.Mui-selected': {
                            backgroundColor: '#F5EBD2',
                            '&:hover': {
                              backgroundColor: '#E8D79A',
                            },
                          },
                          '&:hover': {
                            backgroundColor: '#FBF6EA',
                          },
                        }}
                      >
                        <ListItemIcon
                          sx={{
                            minWidth: 38,
                            color: active ? '#A98216' : '#8A7E66',
                          }}
                        >
                          {item.icon}
                        </ListItemIcon>
                        <ListItemText
                          primary={item.title}
                          primaryTypographyProps={{
                            fontSize: '0.9rem',
                            fontWeight: active ? 600 : 500,
                          }}
                        />
                        {item.badge && (
                          <Box
                            component="span"
                            sx={{
                              minWidth: 22,
                              height: 22,
                              px: 0.75,
                              borderRadius: '8px',
                              backgroundColor: '#C9A227',
                              color: '#FFFFFF',
                              fontSize: '0.72rem',
                              fontWeight: 700,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                            }}
                          >
                            {item.badge}
                          </Box>
                        )}
                      </ListItemButton>
                    </ListItem>
                  );
                })}
              </List>
            </Box>
          );
        })}
      </Box>

      {/* Footer / user summary */}
      <Divider sx={{ mx: 2.5 }} />
      <Box sx={{ px: 2.5, py: 2 }}>
        <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block' }}>
          Signed in as <strong>{user?.username ?? '—'}</strong>
        </Typography>
        <Typography variant="caption" sx={{ color: 'text.disabled', display: 'block', mt: 0.25 }}>
          Saamu Tailors v1.0
        </Typography>
      </Box>
    </Box>
  );

  return (
    <>
      {/* Mobile Drawer */}
      <Drawer
        variant="temporary"
        open={isMobile && open}
        onClose={onClose}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
            borderRight: '1px solid #E7E0D0',
          },
        }}
      >
        {drawerContent}
      </Drawer>

      {/* Desktop Persistent Drawer */}
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
            borderRight: '1px solid #E7E0D0',
            boxShadow: 'none',
          },
        }}
      >
        {drawerContent}
      </Drawer>
    </>
  );
};

export default Sidebar;
