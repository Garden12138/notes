import { Typography, Box } from '@mui/material';

export const Logo = () => {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 3,
      }}
    >
      <Typography
        variant="h2"
        sx={{
          background: (theme) =>
            `-webkit-linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          fontWeight: 700,
        }}
      >
        ADMIN PANEL
      </Typography>
    </Box>
  );
}; 