import React from 'react';
import {
  AppBar,
  Avatar,
  Box,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Toolbar,
  Tooltip,
  Typography,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import NotificationsNoneIcon from '@mui/icons-material/NotificationsNone';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/useAuth';
import { useHealth } from '../hooks/useHealth';
import { BrandMark } from './ui/BrandMark';

interface HeaderProps {
  onToggleSidebar: () => void;
}

function getInitials(username: string | undefined): string {
  if (!username) return 'ST';
  const name = username.trim();
  if (name.length === 0) return 'ST';
  return name.slice(0, 2).toUpperCase();
}

export const Header: React.FC<HeaderProps> = ({ onToggleSidebar }) => {
  const navigate = useNavigate();
  const { user, role, logout } = useAuth();
  const { data: health } = useHealth();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    handleMenuClose();
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <AppBar
      position="sticky"
      elevation={0}
      sx={{
        backgroundColor: '#FFFFFF',
        color: '#242424',
        borderBottom: '1px solid #E7E0D0',
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between', px: { xs: 2, sm: 3 }, minHeight: 64 }}>
        {/* Left Side: Toggle & Brand */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <IconButton
            edge="start"
            color="inherit"
            aria-label="open drawer"
            onClick={onToggleSidebar}
          >
            <MenuIcon />
          </IconButton>

          <Box sx={{ display: { xs: 'flex', md: 'none' }, alignItems: 'center', gap: 1.5 }}>
            <BrandMark size={36} />
            <Typography
              sx={{
                fontWeight: 800,
                fontSize: '1rem',
                lineHeight: 1.2,
                color: '#242424',
                letterSpacing: '-0.01em',
              }}
            >
              Saamu Tailors
            </Typography>
          </Box>
        </Box>

        {/* Right Side: Role chip, Server status, User profile */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          {role && (
            <Chip
              label={role}
              size="small"
              sx={{
                fontWeight: 700,
                fontSize: '0.72rem',
                backgroundColor: '#F5EBD2',
                color: '#7A5E0C',
                border: '1px solid #E8D79A',
                display: { xs: 'none', sm: 'inline-flex' },
              }}
            />
          )}

          <Chip
            label={health?.status === 'ok' ? 'Backend: Online' : 'Backend: Offline'}
            size="small"
            icon={
              <CheckCircleIcon
                sx={{ fontSize: 14, color: health?.status === 'ok' ? '#2E7D52' : '#B3402F' }}
              />
            }
            sx={{
              fontWeight: 600,
              fontSize: '0.72rem',
              backgroundColor: health?.status === 'ok' ? '#E7F1EA' : '#FBE9E6',
              color: health?.status === 'ok' ? '#1F5C3C' : '#8F2F22',
              display: { xs: 'none', md: 'inline-flex' },
            }}
          />

          <Tooltip title="Notifications">
            <IconButton aria-label="notifications">
              <NotificationsNoneIcon />
            </IconButton>
          </Tooltip>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
            <Tooltip title="Account settings">
              <IconButton onClick={handleMenuOpen} size="small" sx={{ ml: 0.5 }}>
                <Avatar
                  sx={{
                    width: 38,
                    height: 38,
                    fontSize: '0.9rem',
                    fontWeight: 700,
                    backgroundColor: '#A98216',
                  }}
                >
                  {getInitials(user?.username)}
                </Avatar>
              </IconButton>
            </Tooltip>
            <Box sx={{ display: { xs: 'none', md: 'block' } }}>
              <Typography variant="body2" sx={{ fontWeight: 600, lineHeight: 1.2 }}>
                {user?.username ?? 'Not signed in'}
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                {role ? `${role} account` : 'Unauthenticated'}
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
                minWidth: 200,
                mt: 1.5,
                borderRadius: '12px',
                border: '1px solid #E7E0D0',
                boxShadow: '0 12px 28px -8px rgba(58, 48, 20, 0.18)',
              },
            }}
          >
            <Box sx={{ px: 2, py: 1 }}>
              <Typography sx={{ fontWeight: 700 }}>{user?.username ?? 'Not signed in'}</Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                {role ? `${role} account` : ''}
              </Typography>
            </Box>
            <MenuItem
              onClick={() => {
                handleMenuClose();
                navigate('/settings');
              }}
            >
              <AccountCircleIcon sx={{ mr: 1.5, color: 'text.secondary', fontSize: 20 }} />
              Profile Settings
            </MenuItem>
            <MenuItem onClick={handleLogout} sx={{ color: '#B3402F' }}>
              Sign Out
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
