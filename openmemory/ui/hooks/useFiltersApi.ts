import { useState, useCallback } from 'react';
import apiClient from '../lib/apiClient';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '@/store/store';
import {
  Category,
  setCategoriesLoading,
  setCategoriesSuccess,
  setCategoriesError,
  setSortingState,
  setSelectedApps,
  setSelectedCategories
} from '@/store/filtersSlice';

interface CategoriesResponse {
  categories: Category[];
  total: number;
}

export interface UseFiltersApiReturn {
  fetchCategories: () => Promise<void>;
  isLoading: boolean;
  error: string | null;
  updateApps: (apps: string[]) => void;
  updateCategories: (categories: string[]) => void;
  updateSort: (column: string, direction: 'asc' | 'desc') => void;
}

export const useFiltersApi = (): UseFiltersApiReturn => {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const dispatch = useDispatch<AppDispatch>();
  const user_id = useSelector((state: RootState) => state.profile.userId);

  const fetchCategories = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    dispatch(setCategoriesLoading());
    setError(null); // Clear previous errors
    try {
      // The backend /api/v1/memories/categories seems to want user_id from your logs.
      // However, all routers are protected by get_current_supa_user, so backend already knows the user.
      // Ideally, the backend endpoint should use the JWT user. Sending user_id is okay if backend handles it.
      console.log(`useFiltersApi: Fetching categories for user_id (from redux): ${user_id}`); // DEBUG
      const response = await apiClient.get<CategoriesResponse>(
        `/api/v1/memories/categories`, { params: { user_id: user_id } } 
      );

      dispatch(setCategoriesSuccess({
        categories: response.data.categories,
        total: response.data.total
      }));
      setIsLoading(false);
    } catch (err: any) {
      console.error("useFiltersApi: Failed to fetch categories", err); // DEBUG
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to fetch categories';
      setError(errorMessage);
      dispatch(setCategoriesError(errorMessage));
      setIsLoading(false);
      // It's often better not to re-throw here unless the component specifically needs to catch it.
      // throw new Error(errorMessage); 
    }
  }, [dispatch, user_id]);

  const updateApps = useCallback((apps: string[]) => {
    dispatch(setSelectedApps(apps));
  }, [dispatch]);

  const updateCategories = useCallback((categories: string[]) => {
    dispatch(setSelectedCategories(categories));
  }, [dispatch]);

  const updateSort = useCallback((column: string, direction: 'asc' | 'desc') => {
    dispatch(setSortingState({ column, direction }));
  }, [dispatch]);

  return {
    fetchCategories,
    isLoading,
    error,
    updateApps,
    updateCategories,
    updateSort
  };
}; 