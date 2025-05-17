/**
 * API Client Service
 * 
 * Provides a central client for making API calls to the backend services.
 * Includes type-safe methods for all bug and attachment operations.
 */

import axios, { AxiosError } from 'axios';
import { Bug, CreateBugRequest, UpdateBugRequest } from '../types/bug';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080';

/**
 * Global error handler for API requests
 */
const handleApiError = (error: any) => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError;
    console.error('API Error:', {
      status: axiosError.response?.status,
      statusText: axiosError.response?.statusText,
      data: axiosError.response?.data,
      url: axiosError.config?.url
    });
    
    // You can customize error handling based on status codes
    if (axiosError.response?.status === 404) {
      throw new Error(`Resource not found: ${axiosError.config?.url}`);
    } else if (axiosError.response?.status === 500) {
      throw new Error('Server error. Please try again later.');
    }
  }
  
  // Re-throw the error for the calling function to handle
  throw error;
};

/**
 * Base API client configuration
 */
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Bug-related API calls
export const bugAPI = {
  /**
   * Fetches all bugs from the API
   */
  async getAll(): Promise<Bug[]> {
    try {
      const response = await apiClient.get('/bugs');
      return response.data;
    } catch (error) {
      handleApiError(error);
      return []; // This line won't be reached if handleApiError throws
    }
  },

  /**
   * Gets a specific bug by ID
   */
  async getById(id: string): Promise<Bug> {
    try {
      const response = await apiClient.get(`/bugs/${id}`);
      return response.data;
    } catch (error) {
      handleApiError(error);
      throw error; // This line won't be reached if handleApiError throws
    }
  },

  /**
   * Creates a new bug
   */
  async create(bug: CreateBugRequest): Promise<Bug> {
    try {
      const response = await apiClient.post('/bugs', bug);
      return response.data;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  },

  /**
   * Updates an existing bug
   */
  async update(id: string, bug: UpdateBugRequest): Promise<Bug> {
    try {
      const response = await apiClient.put(`/bugs/${id}`, bug);
      return response.data;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  },

  /**
   * Deletes a bug
   */
  async delete(id: string): Promise<void> {
    try {
      await apiClient.delete(`/bugs/${id}`);
    } catch (error) {
      handleApiError(error);
    }
  },
};

// Attachment-related API calls
export const attachmentAPI = {
  /**
   * Get attachments for a specific bug
   */
  getBugAttachments: async (bugId: string): Promise<any[]> => {
    try {
      const response = await apiClient.get(`/bugs/${bugId}/attachments`);
      return response.data;
    } catch (error) {
      handleApiError(error);
      return []; // Never reached if handleApiError throws
    }
  },

  /**
   * Upload an attachment for a bug
   */
  uploadAttachment: async (bugId: string, file: File): Promise<any> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await apiClient.post(`/bugs/${bugId}/attachments`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return response.data;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  },

  /**
   * Get a specific attachment's metadata
   */
  getAttachment: async (attachmentId: string): Promise<any> => {
    try {
      const response = await apiClient.get(`/attachments/${attachmentId}`);
      return response.data;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  },

  /**
   * Get attachment content for preview
   */
  getAttachmentContent: async (attachmentId: string): Promise<any> => {
    try {
      const response = await apiClient.get(`/attachments/${attachmentId}/content`);
      return response.data;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  },
};
