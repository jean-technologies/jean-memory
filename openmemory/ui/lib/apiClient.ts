import axios, { InternalAxiosRequestConfig, AxiosError } from 'axios';
import { getGlobalAccessToken } from '../contexts/AuthContext'; // Import the accessor

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
});

// Function to get the access token - this would typically be from your AuthContext
// For now, we assume you will pass it or have a way to access it globally.
// In a real app, you'd integrate this with useAuth() from AuthContext.

// Interceptor to add the auth token to requests
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getGlobalAccessToken(); 
    
    // EXTENSIVE DEBUG LOGGING FOR NOTION STATUS AUTH ISSUE
    if (config.url?.includes('/notion/status')) {
      console.error('🚨 FRONTEND API CLIENT - NOTION STATUS REQUEST');
      console.error('   URL:', config.url);
      console.error('   Method:', config.method);
      console.error('   Token available:', token ? 'YES' : 'NO');
      console.error('   Token value:', token ? token.substring(0, 20) + '...' : 'NONE');
      console.error('   Headers before adding auth:', config.headers);
    }
    
    console.log('API Client Interceptor: Token being used:', token ? 'Token present' : 'No token'); // DEBUG LINE
    console.log('API Client Interceptor: Request URL:', config.url); // DEBUG LINE
    
    if (token) {
      // Always use the real Supabase token (local or production)
      config.headers.Authorization = `Bearer ${token}`;
      
      if (config.url?.includes('/notion/status')) {
        console.error('   ✅ Authorization header added:', config.headers.Authorization ? 'YES' : 'NO');
        console.error('   ✅ Auth header value:', config.headers.Authorization ? config.headers.Authorization.substring(0, 20) + '...' : 'NONE');
        console.error('   ✅ Final headers:', config.headers);
      }
    } else {
      console.warn('API Client: No authentication token available');
      if (config.url?.includes('/notion/status')) {
        console.error('   ❌ NO TOKEN - Headers will not include Authorization');
      }
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

export default apiClient; 