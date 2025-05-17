/**
 * API Client Service
 * 
 * Provides a central client for making API calls to the backend services.
 * Includes type-safe methods for all bug and attachment operations.
 */

import axios, { AxiosError } from 'axios';
import { Bug, CreateBugRequest, UpdateBugRequest } from '../types/bug';

// Define comment types here directly if there are import issues
interface Comment {
  comment_id: string;
  bug_id: string;
  author: string;
  text: string;
  timestamp: string;
  is_private?: boolean;
  attachment_ids?: string[];
}

interface CommentBase {
  author: string;
  text: string;
  is_private?: boolean;
  attachment_ids?: string[];
}

interface CreateCommentRequest extends CommentBase {}

interface UpdateCommentRequest {
  text?: string;
  is_private?: boolean;
  attachment_ids?: string[];
}

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
   * Fetches all bugs from the fixed API endpoint
   */
  async getAllFixed(): Promise<Bug[]> {
    try {
      const response = await apiClient.get('/bugs-fixed');
      return response.data;
    } catch (error) {
      handleApiError(error);
      return []; // This line won't be reached if handleApiError throws
    }
  },
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
  async getByIdFixed(id: string): Promise<Bug> {
    try {
      // Ensure the ID is properly encoded for use in a URL
      const encodedId = encodeURIComponent(id);
      const response = await apiClient.get(`/bugs-fixed/${encodedId}`);
      return response.data;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  },

  /**
   * Gets a specific bug by ID
   */
  async getById(id: string): Promise<Bug> {
    try {
      // Ensure the ID is properly encoded for use in a URL
      const encodedId = encodeURIComponent(id);
      const response = await apiClient.get(`/bugs/${encodedId}`);
      return response.data;
    } catch (error) {
      handleApiError(error);
      throw error;
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
      const encodedId = encodeURIComponent(id);
      const response = await apiClient.put(`/bugs/${encodedId}`, bug);
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
      const encodedId = encodeURIComponent(id);
      await apiClient.delete(`/bugs/${encodedId}`);
    } catch (error) {
      handleApiError(error);
    }
  },
};

// Attachment-related API calls
// Comment-related API calls
export const commentAPI = {
  /**
   * Get comments for a specific bug
   */
  async getBugComments(bugId: string): Promise<Comment[]> {
    try {
      // Ensure the bug ID is properly encoded for the URL
      const encodedId = encodeURIComponent(bugId);
      console.log(`Fetching comments for bug ID: ${bugId} (encoded as ${encodedId})`);
      const response = await apiClient.get(`/bugs/${encodedId}/comments`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching comments for bug ID: ${bugId}`, error);
      handleApiError(error);
      return []; // Never reached if handleApiError throws
    }
  },

  /**
   * Create a new comment for a bug
   */
  async createComment(bugId: string, comment: CreateCommentRequest): Promise<Comment> {
    try {
      const encodedId = encodeURIComponent(bugId);
      const response = await apiClient.post(`/bugs/${encodedId}/comments`, comment);
      return response.data;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  },

  /**
   * Update an existing comment
   */
  async updateComment(commentId: string, comment: UpdateCommentRequest): Promise<Comment> {
    try {
      const response = await apiClient.put(`/bugs/comments/${commentId}`, comment);
      return response.data;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  },

  /**
   * Delete a comment
   */
  async deleteComment(commentId: string): Promise<void> {
    try {
      await apiClient.delete(`/bugs/comments/${commentId}`);
    } catch (error) {
      handleApiError(error);
    }
  },
};

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
