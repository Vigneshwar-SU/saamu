import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  Avatar,
  Menu,
  MenuItem,
  Tooltip,
  Chip,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import NotificationsNoneIcon from '@mui/icons-material/NotificationsNone';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import ContentCutIcon from '@mui/icons-material/ContentCut';
import { useNavigate } from 'react-router-dom';

interface HeaderProps {
  onToggleSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onToggleSidebar }) => {
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    handleMenuClose();
    navigate('/login');
  };

  return (
    <AppBar
      position="sticky"
      elevation={0}
      sx={{
        backgroundColor: '#FFFFFF',
        color: '#0F172A',
        borderBottom: '1px solid #E2E8F0',
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between', px: { xs: 2, sm: 3 } }}>
        {/* Left Side: Toggle & Brand */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton
            edge="start"
            color="inherit"
            aria-label="open drawer"
            onClick={onToggleSidebar}
            sx={{ color: '#475569' }}
          >
            <MenuIcon />
          </IconButton>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Box
              sx={{
                width: 38,
                height: 38,
                borderRadius: '10px',
                backgroundColor: '#1E3A8A',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#FFFFFF',
              }}
            >
              <ContentCutIcon fontSize="small" />
            </Box>
            <Box>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 700,
                  fontSize: '1.1rem',
                  lineHeight: 1.2,
                  color: '#1E3A8A',
                  letterSpacing: '-0.01em',
                }}
              >
                SAAMU TAILORS
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748B', display: 'block', lineHeight: 1 }}>
                Management System
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* Right Side: Status Badge, Notifications, User Profile */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Chip
            label="Local Server"
            size="small"
            color="success"
            variant="outlined"
            sx={{
              fontWeight: 600,
              fontSize: '0.75rem',
              borderColor: '#22C55E',
              color: '#15803D',
              display: { xs: 'none', sm: 'inline-flex' },
            }}
          />

          <Tooltip title="Notifications">
            <IconButton sx={{ color: '#475569' }}>
              <NotificationsNoneIcon />
            </IconButton>
          </Tooltip>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip title="Account settings">
              <IconButton onClick={handleMenuOpen} size="small" sx={{ ml: 0.5 }}>
                <Avatar
                  sx={{
                    width: 36,
                    height: 36,
                    backgroundColor: '#2563EB',
                    fontSize: '0.9rem',
                    fontWeight: 600,
                  }}
                >
                  ST
                </Avatar>
              </IconButton>
            </Tooltip>
            <Box sx={{ display: { xs: 'none', md: 'block' } }}>
              <Typography variant="body2" sx={{ fontWeight: 600, lineHeight: 1.2 }}>
                Admin User
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748B' }}>
                System Administrator
              </Typography>
            </Box>
          </Box>

          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
            PaperProps={{
              elevation: 2,
              sx: {
                minWidth: 180,
                mt: 1.5,
                borderRadius: '12px',
                border: '1px solid #E2E8F0',
              },
            }}
          >
            <MenuItem onClick={() => { handleMenuClose(); navigate('/settings'); }}>
              <AccountCircleIcon sx={{ mr: 1.5, color: '#64748B', fontSize: 20 }} />
              Profile Settings
            </MenuItem>
            <MenuItem onClick={handleLogout} sx={{ color: '#EF4444' }}>
              Sign Out
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};
