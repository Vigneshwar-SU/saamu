import React, { useState } from 'react';
import { Box, useTheme } from '@mui/material';
import { Outlet } from 'react-router-dom';
import { Header } from '../components/Header';
import { Sidebar } from '../components/Sidebar';
import { Footer } from '../components/Footer';
import { PageContainer } from '../components/ui/PageContainer';

const DRAWER_WIDTH = 272;

export const MainLayout: React.FC = () => {
  const theme = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleToggleSidebar = () => {
    setSidebarOpen((prev) => !prev);
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        backgroundColor: '#FAF6EC',
      }}
    >
      {/* Top Navigation Bar */}
      <Header onToggleSidebar={handleToggleSidebar} />

      <Box sx={{ display: 'flex', flexGrow: 1 }}>
        {/* Left Sidebar */}
        <Sidebar
          open={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          drawerWidth={DRAWER_WIDTH}
        />

        {/* Main Content Area */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            minWidth: 0,
            display: 'flex',
            flexDirection: 'column',
            width: {
              xs: '100%',
              md: sidebarOpen ? `calc(100% - ${DRAWER_WIDTH}px)` : '100%',
            },
            transition: theme.transitions.create(['width', 'margin'], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
          }}
        >
          <Box
            className="page-content"
            sx={{ p: { xs: 2, sm: 3, md: 4 }, flexGrow: 1, minWidth: 0 }}
          >
            <PageContainer>
              <Outlet />
            </PageContainer>
          </Box>

          {/* Footer */}
          <Footer />
        </Box>
      </Box>
    </Box>
  );
};

export default MainLayout;
