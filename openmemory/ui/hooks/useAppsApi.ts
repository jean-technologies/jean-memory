import { useState, useCallback } from 'react';
import apiClient from '../lib/apiClient';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '@/store/store';
import {
  App,
  AppDetails,
  AppMemory,
  AccessedMemory,
  setAppsSuccess,
  setAppsError,
  setAppsLoading,
  setSelectedAppLoading,
  setSelectedAppDetails,
  setCreatedMemoriesLoading,
  setCreatedMemoriesSuccess,
  setCreatedMemoriesError,
  setAccessedMemoriesLoading,
  setAccessedMemoriesSuccess,
  setAccessedMemoriesError,
  setSelectedAppError,
} from '@/store/appsSlice';

interface ApiResponse {
  total: number;
  page: number;
  page_size: number;
  apps: App[];
}

interface MemoriesResponse {
  total: number;
  page: number;
  page_size: number;
  memories: AppMemory[];
}

interface AccessedMemoriesResponse {
  total: number;
  page: number;
  page_size: number;
  memories: AccessedMemory[];
}

interface FetchAppsParams {
  name?: string;
  is_active?: boolean;
  sort_by?: 'name' | 'memories' | 'memories_accessed';
  sort_direction?: 'asc' | 'desc';
  page?: number;
  page_size?: number;
}

interface UseAppsApiReturn {
  fetchApps: (params?: FetchAppsParams) => Promise<{ apps: App[], total: number } | undefined>;
  fetchAppDetails: (appId: string) => Promise<void>;
  fetchAppMemories: (appId: string, page?: number, pageSize?: number) => Promise<void>;
  fetchAppAccessedMemories: (appId: string, page?: number, pageSize?: number) => Promise<void>;
  updateAppDetails: (appId: string, details: { is_active: boolean }) => Promise<any | undefined>;
  isLoading: boolean;
  error: string | null;
}

export const useAppsApi = (): UseAppsApiReturn => {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const dispatch = useDispatch<AppDispatch>();

  const fetchApps = useCallback(async (params: FetchAppsParams = {}): Promise<{ apps: App[], total: number } | undefined> => {
    const {
      name,
      is_active,
      sort_by = 'name',
      sort_direction = 'asc',
      page = 1,
      page_size = 10
    } = params;

    setIsLoading(true);
    dispatch(setAppsLoading());
    setError(null);
    try {
      const queryParams: Record<string, any> = {
        page: page,
        page_size: page_size,
        sort_by: sort_by,
        sort_direction: sort_direction
      };
      if (name) queryParams.name = name;
      if (is_active !== undefined) queryParams.is_active = String(is_active);

      console.log("useAppsApi: Fetching apps with params:", queryParams);
      const response = await apiClient.get<ApiResponse>(
        `/api/v1/apps/`, { params: queryParams }
      );

      setIsLoading(false);
      dispatch(setAppsSuccess(response.data.apps));
      return {
        apps: response.data.apps,
        total: response.data.total
      };
    } catch (err: any) {
      console.error("useAppsApi: Failed to fetch apps", err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to fetch apps';
      setError(errorMessage);
      dispatch(setAppsError(errorMessage));
      setIsLoading(false);
      return undefined;
    }
  }, [dispatch]);

  const fetchAppDetails = useCallback(async (appId: string): Promise<void> => {
    setIsLoading(true);
    dispatch(setSelectedAppLoading());
    setError(null);
    try {
      console.log(`useAppsApi: Fetching details for app ${appId}`);
      const response = await apiClient.get<AppDetails>(
        `/api/v1/apps/${appId}`
      );
      dispatch(setSelectedAppDetails(response.data));
      setIsLoading(false);
    } catch (err: any) {
      console.error("useAppsApi: Failed to fetch app details", err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to fetch app details';
      dispatch(setSelectedAppError(errorMessage));
      setError(errorMessage);
      setIsLoading(false);
    }
  }, [dispatch]);

  const fetchAppMemories = useCallback(async (appId: string, page: number = 1, pageSize: number = 10): Promise<void> => {
    setIsLoading(true);
    dispatch(setCreatedMemoriesLoading());
    setError(null);
    try {
      console.log(`useAppsApi: Fetching memories for app ${appId}`);
      const response = await apiClient.get<MemoriesResponse>(
        `/api/v1/apps/${appId}/memories`, { params: { page, page_size: pageSize } }
      );
      dispatch(setCreatedMemoriesSuccess({
        items: response.data.memories,
        total: response.data.total,
        page: response.data.page,
      }));
      setIsLoading(false);
    } catch (err: any) {
      console.error("useAppsApi: Failed to fetch app memories", err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to fetch app memories';
      dispatch(setCreatedMemoriesError(errorMessage));
      setError(errorMessage);
      setIsLoading(false);
    }
  }, [dispatch]);

  const fetchAppAccessedMemories = useCallback(async (appId: string, page: number = 1, pageSize: number = 10): Promise<void> => {
    setIsLoading(true);
    dispatch(setAccessedMemoriesLoading());
    setError(null);
    try {
      console.log(`useAppsApi: Fetching accessed memories for app ${appId}`);
      const response = await apiClient.get<AccessedMemoriesResponse>(
        `/api/v1/apps/${appId}/accessed`, { params: { page, page_size: pageSize } }
      );
      dispatch(setAccessedMemoriesSuccess({
        items: response.data.memories,
        total: response.data.total,
        page: response.data.page,
      }));
      setIsLoading(false);
    } catch (err: any) {
      console.error("useAppsApi: Failed to fetch accessed memories", err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to fetch accessed memories';
      dispatch(setAccessedMemoriesError(errorMessage));
      setError(errorMessage);
      setIsLoading(false);
    }
  }, [dispatch]);

  const updateAppDetails = async (appId: string, details: { is_active: boolean }): Promise<any | undefined> => {
    setIsLoading(true);
    setError(null);
    try {
      console.log(`useAppsApi: Updating app ${appId} details:`, details);
      const response = await apiClient.put(
        `/api/v1/apps/${appId}`, details
      );
      setIsLoading(false);
      return response.data;
    } catch (error: any) {
      console.error("useAppsApi: Failed to update app details:", error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to update app details';
      setError(errorMessage);
      dispatch(setSelectedAppError(errorMessage));
      setIsLoading(false);
      return undefined;
    }
  };

  return {
    fetchApps,
    fetchAppDetails,
    fetchAppMemories,
    fetchAppAccessedMemories,
    updateAppDetails,
    isLoading,
    error
  };
};
