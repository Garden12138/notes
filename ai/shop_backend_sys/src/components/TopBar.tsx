import {
  AppBar,
  Avatar,
  Badge,
  Box,
  IconButton,
  InputAdornment,
  Stack,
  TextField,
  Typography,
  styled,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import NotificationsIcon from '@mui/icons-material/Notifications';

const StyledAppBar = styled(AppBar)(({ theme }) => ({
  backgroundColor: theme.palette.background.paper,
  boxShadow: 'none',
  borderBottom: `1px solid ${theme.palette.grey[200]}`,
  color: theme.palette.text.primary,
}));

const SearchField = styled(TextField)(({ theme }) => ({
  width: 300,
  '& .MuiOutlinedInput-root': {
    backgroundColor: theme.palette.background.default,
  },
}));

const NotificationBadge = styled(Badge)(({ theme }) => ({
  '& .MuiBadge-badge': {
    backgroundColor: theme.palette.success.main,
    color: theme.palette.common.white,
    boxShadow: `0 0 0 2px ${theme.palette.background.paper}`,
    '&::after': {
      position: 'absolute',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      borderRadius: '50%',
      border: '1px solid currentColor',
      content: '""',
    },
  },
}));

export const TopBar = () => {
  return (
    <StyledAppBar position="static">
      <Stack
        direction="row"
        alignItems="center"
        justifyContent="space-between"
        sx={{ px: 3, py: 2 }}
      >
        <SearchField
          placeholder="Search"
          variant="outlined"
          size="small"
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon color="action" />
              </InputAdornment>
            ),
          }}
        />
        
        <Stack direction="row" alignItems="center" spacing={3}>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Welcome back,
            </Typography>
            <Typography variant="h2">
              Diego Morata
            </Typography>
          </Box>

          <IconButton>
            <NotificationBadge badgeContent={2} overlap="circular">
              <NotificationsIcon />
            </NotificationBadge>
          </IconButton>

          <Avatar
            src="/avatar.jpg"
            alt="Diego Morata"
            sx={{
              width: 40,
              height: 40,
              border: (theme) => `2px solid ${theme.palette.grey[100]}`,
            }}
          />
        </Stack>
      </Stack>
    </StyledAppBar>
  );
}; 