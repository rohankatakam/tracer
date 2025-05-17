/**
 * Comment Types
 * 
 * This file contains all TypeScript interfaces related to the comments feature.
 */

/**
 * Base interface for comment data
 */
export interface CommentBase {
  author: string;
  text: string;
  is_private?: boolean;
  attachment_ids?: string[];
}

/**
 * Interface for creating a new comment
 */
export interface CreateCommentRequest extends CommentBase {
  // Inherits all properties from CommentBase
}

/**
 * Interface for updating an existing comment
 */
export interface UpdateCommentRequest {
  text?: string;
  is_private?: boolean;
  attachment_ids?: string[];
}

/**
 * Complete comment interface with all fields
 */
export interface Comment extends CommentBase {
  comment_id: string;
  bug_id: string;
  timestamp: string;
}
