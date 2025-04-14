import {
  Box,
  Button,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Chip,
  IconButton,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import FilterListIcon from '@mui/icons-material/FilterList';
import VisibilityIcon from '@mui/icons-material/Visibility';
import NotificationsIcon from '@mui/icons-material/Notifications';
import ReceiptIcon from '@mui/icons-material/Receipt';

const clients = [
  {
    id: 1,
    name: 'Martijn Dragonjer',
    city: 'Jackson',
    date: '2020/06/01',
    term: 'Renewable',
    status: 'Active',
  },
  {
    id: 2,
    name: 'Nombeko Mabandla',
    city: 'São Paulo',
    date: '2020/06/01',
    term: 'Convertible',
    status: 'Soon to expire',
  },
  // Add more clients as needed
];

export const Clients = () => {
  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h1">Clients</Typography>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<FileDownloadIcon />}
            color="primary"
          >
            Export List
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            color="primary"
          >
            Add new client
          </Button>
        </Stack>
      </Stack>

      <Stack direction="row" spacing={2} mb={3}>
        <TextField
          placeholder="Type"
          size="small"
          InputProps={{
            endAdornment: <FilterListIcon color="action" />,
          }}
        />
        <TextField
          placeholder="Date"
          size="small"
          InputProps={{
            endAdornment: <CalendarTodayIcon color="action" />,
          }}
        />
        <TextField
          placeholder="Status"
          size="small"
          InputProps={{
            endAdornment: <FilterListIcon color="action" />,
          }}
        />
      </Stack>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>NAME</TableCell>
              <TableCell>CITY</TableCell>
              <TableCell>CLIENT SINCE</TableCell>
              <TableCell>INSURANCE</TableCell>
              <TableCell align="center">STATUS</TableCell>
              <TableCell align="center">ACTIONS</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {clients.map((client) => (
              <TableRow key={client.id}>
                <TableCell>{client.name}</TableCell>
                <TableCell>{client.city}</TableCell>
                <TableCell>{client.date}</TableCell>
                <TableCell>{client.term}</TableCell>
                <TableCell align="center">
                  <Chip
                    label={client.status}
                    color={client.status === 'Active' ? 'success' : 'warning'}
                    variant="outlined"
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Stack direction="row" spacing={1} justifyContent="center">
                    <IconButton size="small">
                      <ReceiptIcon />
                    </IconButton>
                    <IconButton size="small">
                      <NotificationsIcon />
                    </IconButton>
                    <IconButton size="small">
                      <VisibilityIcon />
                    </IconButton>
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}; 