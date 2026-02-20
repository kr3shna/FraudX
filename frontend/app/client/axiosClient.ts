import axios from 'axios';

const apiUrl =
  typeof process !== 'undefined'
    ? (process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000')
    : 'http://localhost:8000';

const axiosClient = axios.create({
  baseURL: apiUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default axiosClient;
export { apiUrl };