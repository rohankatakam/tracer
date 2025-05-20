// Common enums for all bug types
export enum BugSchemaType {
  BASE = 'base',
  MOZILLA = 'mozilla',
  CHROMIUM = 'chromium',
  ORACLE = 'oracle',
  GITHUB_ISSUE = 'github', // Changed from 'github_issue' to match backend expectations
}

// Base type enums
export enum BaseSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

export enum BaseStatus {
  NEW = 'NEW',
  IN_PROGRESS = 'IN_PROGRESS',
  RESOLVED = 'RESOLVED',
  CLOSED = 'CLOSED',
}

// Mozilla/Bugzilla specific enums
export enum MozillaSeverity {
  BLOCKER = 'blocker',
  CRITICAL = 'critical',
  MAJOR = 'major',
  NORMAL = 'normal',
  MINOR = 'minor',
  TRIVIAL = 'trivial',
  ENHANCEMENT = 'enhancement',
}

export enum MozillaPriority {
  P1 = 'P1',
  P2 = 'P2',
  P3 = 'P3',
  P4 = 'P4',
  P5 = 'P5',
}

export enum MozillaStatus {
  UNCONFIRMED = 'UNCONFIRMED',
  NEW = 'NEW',
  ASSIGNED = 'ASSIGNED',
  RESOLVED = 'RESOLVED',
  VERIFIED = 'VERIFIED',
  REOPENED = 'REOPENED',
}

export enum MozillaResolution {
  FIXED = 'FIXED',
  INVALID = 'INVALID',
  WONTFIX = 'WONTFIX',
  DUPLICATE = 'DUPLICATE',
  WORKSFORME = 'WORKSFORME',
  INCOMPLETE = 'INCOMPLETE',
}

// Chromium specific enums
export enum ChromiumPriority {
  P0 = 'P0',
  P1 = 'P1',
  P2 = 'P2',
  P3 = 'P3',
  P4 = 'P4',
}

export enum ChromiumType {
  BUG = 'Bug',
  FEATURE = 'Feature',
  FEATURE_REQUEST = 'Feature Request',
  TASK = 'Task',
}

export enum ChromiumStatus {
  UNCONFIRMED = 'Unconfirmed',
  UNTRIAGED = 'Untriaged',
  ASSIGNED = 'Assigned',
  STARTED = 'Started',
  FIXED = 'Fixed',
  VERIFIED = 'Verified',
  DUPLICATE = 'Duplicate',
  WONTFIX = 'WontFix',
  ARCHIVED = 'Archived',
}

// Common bug interface with schema discrimination
export interface BaseBug {
  bug_id: string;
  title: string;
  description?: string;
  reporter?: string;
  created_at: string;
  updated_at: string;
  product?: string;
  component?: string;
  version?: string;
  platform?: string;
  operating_system?: string;
  schema_type: BugSchemaType;
  attachment_count?: number;
  attachments?: Attachment[];
  extra_data?: Record<string, any>;
}

// Base schema bug
export interface BaseTypeBug extends BaseBug {
  schema_type: BugSchemaType.BASE;
  severity?: BaseSeverity;
  status?: BaseStatus;
}

// Mozilla/Bugzilla schema bug
export interface MozillaBug extends BaseBug {
  schema_type: BugSchemaType.MOZILLA;
  mozilla_severity?: MozillaSeverity;
  mozilla_priority?: MozillaPriority;
  mozilla_status?: MozillaStatus;
  mozilla_resolution?: MozillaResolution;
  mozilla_version?: string;
  mozilla_component?: string;
  mozilla_keywords?: string;
}

// Chromium schema bug
export interface ChromiumBug extends BaseBug {
  schema_type: BugSchemaType.CHROMIUM;
  chromium_priority?: ChromiumPriority;
  chromium_type?: ChromiumType;
  chromium_status?: ChromiumStatus;
  chromium_component?: string;
  chromium_owner?: string;
  chromium_cc?: string;
  chromium_labels?: string;
}

// Oracle schema bug
export interface OracleBug extends BaseBug {
  schema_type: BugSchemaType.ORACLE;
  oracle_status_code?: number;
  oracle_status_description?: string;
  oracle_severity?: string;
  oracle_priority?: string;
  oracle_close_reason?: string;
  oracle_environment?: string;
}

// GitHub Issue schema bug
export interface GitHubIssueBug extends BaseBug {
  schema_type: BugSchemaType.GITHUB_ISSUE;
  github_issue_number?: number;
  github_issue_url?: string;
  github_repo?: string;
  github_owner?: string;
  github_state?: string;
  github_labels?: string[];
  github_assignees?: string[];
  github_created_at?: string;
  github_updated_at?: string;
}

// Bug union type for all schemas
export type Bug = BaseTypeBug | MozillaBug | ChromiumBug | OracleBug | GitHubIssueBug;

// Create bug request types
export interface BaseCreateBugRequest {
  title: string;
  description?: string;
  reporter?: string;
  product?: string;
  component?: string;
  version?: string;
  platform?: string;
  operating_system?: string;
  schema_type: BugSchemaType;
  extra_data?: Record<string, any>;
}

// Base type create request
export interface BaseTypeCreateRequest extends BaseCreateBugRequest {
  schema_type: BugSchemaType.BASE;
  severity?: BaseSeverity;
  status?: BaseStatus;
}

// Mozilla type create request
export interface MozillaCreateRequest extends BaseCreateBugRequest {
  schema_type: BugSchemaType.MOZILLA;
  mozilla_severity?: MozillaSeverity;
  mozilla_priority?: MozillaPriority;
  mozilla_status?: MozillaStatus;
  mozilla_resolution?: MozillaResolution;
  mozilla_version?: string;
  mozilla_component?: string;
  mozilla_keywords?: string;
}

// Chromium type create request
export interface ChromiumCreateRequest extends BaseCreateBugRequest {
  schema_type: BugSchemaType.CHROMIUM;
  chromium_priority?: ChromiumPriority;
  chromium_type?: ChromiumType;
  chromium_status?: ChromiumStatus;
  chromium_component?: string;
  chromium_owner?: string;
  chromium_cc?: string;
  chromium_labels?: string;
}

// Oracle type create request
export interface OracleCreateRequest extends BaseCreateBugRequest {
  schema_type: BugSchemaType.ORACLE;
  oracle_status_code?: number;
  oracle_status_description?: string;
  oracle_severity?: string;
  oracle_priority?: string;
  oracle_close_reason?: string;
  oracle_environment?: string;
}

// GitHub Issue type create request
export interface GitHubIssueCreateRequest extends BaseCreateBugRequest {
  schema_type: BugSchemaType.GITHUB_ISSUE;
  github_issue_number?: number;
  github_issue_url?: string;
  github_repo?: string;
  github_owner?: string;
  github_state?: string;
  github_labels?: string[];
  github_assignees?: string[];
  github_created_at?: string;
  github_updated_at?: string;
  github_closed_at?: string | null;
}

// Create request union type
export type CreateBugRequest = BaseTypeCreateRequest | MozillaCreateRequest | ChromiumCreateRequest | OracleCreateRequest | GitHubIssueCreateRequest;

// Update bug request types (similar to create but all fields optional)
export interface BaseUpdateBugRequest {
  title?: string;
  description?: string;
  reporter?: string;
  product?: string;
  component?: string;
  version?: string;
  platform?: string;
  operating_system?: string;
  schema_type?: BugSchemaType;
  extra_data?: Record<string, any>;
}

// Base type update request
export interface BaseTypeUpdateRequest extends BaseUpdateBugRequest {
  schema_type?: BugSchemaType.BASE;
  severity?: BaseSeverity;
  status?: BaseStatus;
}

// Mozilla type update request
export interface MozillaUpdateRequest extends BaseUpdateBugRequest {
  schema_type?: BugSchemaType.MOZILLA;
  mozilla_severity?: MozillaSeverity;
  mozilla_priority?: MozillaPriority;
  mozilla_status?: MozillaStatus;
  mozilla_resolution?: MozillaResolution;
  mozilla_version?: string;
  mozilla_component?: string;
  mozilla_keywords?: string;
}

// Chromium type update request
export interface ChromiumUpdateRequest extends BaseUpdateBugRequest {
  schema_type?: BugSchemaType.CHROMIUM;
  chromium_priority?: ChromiumPriority;
  chromium_type?: ChromiumType;
  chromium_status?: ChromiumStatus;
  chromium_component?: string;
  chromium_owner?: string;
  chromium_cc?: string;
  chromium_labels?: string;
}

// Oracle type update request
export interface OracleUpdateRequest extends BaseUpdateBugRequest {
  schema_type?: BugSchemaType.ORACLE;
  oracle_status_code?: number;
  oracle_status_description?: string;
  oracle_severity?: string;
  oracle_priority?: string;
  oracle_close_reason?: string;
  oracle_environment?: string;
}

// GitHub Issue type update request
export interface GitHubIssueUpdateRequest extends BaseUpdateBugRequest {
  schema_type?: BugSchemaType.GITHUB_ISSUE;
  github_issue_number?: number;
  github_issue_url?: string;
  github_repo?: string;
  github_owner?: string;
  github_state?: string;
  github_labels?: string[];
  github_assignees?: string[];
  github_created_at?: string;
  github_updated_at?: string;
}

// Update request union type
export type UpdateBugRequest = BaseTypeUpdateRequest | MozillaUpdateRequest | ChromiumUpdateRequest | OracleUpdateRequest | GitHubIssueUpdateRequest;

export interface Attachment {
  attachment_id: string;
  bug_id: string;
  filename: string;
  file_type?: string;
  file_extension?: string;
  file_size: number;
  content_type?: string;
  upload_timestamp: string;
  processing_status: string;
  processing_error?: string | null;
  description?: string | null;
  uploader?: string | null;
  content?: {
    text_content_ids: string[];
    image_content_ids: string[];
    pdf_content_id: string | null;
    video_content_id: string | null;
  };
  extra_data?: Record<string, any>;
}
