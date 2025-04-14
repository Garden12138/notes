import { Box, List, ListItem, ListItemIcon, ListItemText, styled } from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PeopleIcon from '@mui/icons-material/People';
import ReceiptIcon from '@mui/icons-material/Receipt';
import SecurityIcon from '@mui/icons-material/Security';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import SettingsIcon from '@mui/icons-material/Settings';
import LogoutIcon from '@mui/icons-material/Logout';
import { useLocation, useNavigate } from 'react-router-dom';
import { Logo } from './Logo';

const StyledListItem = styled(ListItem)<{ active?: boolean }>(({ theme, active }) => ({
  marginBottom: theme.spacing(0.5),
  borderRadius: theme.spacing(0.5),
  backgroundColor: active ? theme.palette.primary.light : 'transparent',
  color: active ? theme.palette.primary.main : theme.palette.secondary.main,
  cursor: 'pointer',
  '&:hover': {
    backgroundColor: theme.palette.primary.light,
    color: theme.palette.primary.main,
  },
  '& .MuiListItemIcon-root': {
    color: 'inherit',
  },
}));

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Clients', icon: <PeopleIcon />, path: '/clients' },
  { text: 'Invoices', icon: <ReceiptIcon />, path: '/invoices' },
  { text: 'Insurances', icon: <SecurityIcon />, path: '/insurances' },
  { text: 'Financial', icon: <AccountBalanceIcon />, path: '/financial' },
  { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
  { text: 'Log Out', icon: <LogoutIcon />, path: '/logout' },
];

export const SideNav = () => {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        width: 240,
        height: '100vh',
        backgroundColor: 'background.paper',
        borderRight: '1px solid',
        borderColor: 'grey.200',
      }}
    >
      <Logo />
      <List sx={{ px: 2 }}>
        {menuItems.map((item) => (
          <StyledListItem
            key={item.text}
            active={location.pathname === item.path}
            onClick={() => navigate(item.path)}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </StyledListItem>
        ))}
      </List>
    </Box>
  );
}; 