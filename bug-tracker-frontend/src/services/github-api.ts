/**
 * Service for interacting with the GitHub API
 */

// Function to parse GitHub issue URL into owner, repo, and issue number
export const parseGitHubIssueUrl = (url: string): { owner: string; repo: string; issueNumber: string } | null => {
  try {
    // Match GitHub issue URL pattern: https://github.com/{owner}/{repo}/issues/{number}
    const pattern = /https:\/\/github\.com\/([^\/]+)\/([^\/]+)\/issues\/(\d+)/;
    const match = url.match(pattern);
    
    if (!match) return null;
    
    return {
      owner: match[1],
      repo: match[2],
      issueNumber: match[3]
    };
  } catch (error) {
    console.error('Error parsing GitHub issue URL:', error);
    return null;
  }
};

// Function to fetch GitHub issue data from our API
export const fetchGitHubIssue = async (url: string) => {
  try {
    // First parse the GitHub URL
    const parsed = parseGitHubIssueUrl(url);
    if (!parsed) {
      throw new Error('Invalid GitHub issue URL format');
    }
    
    const { owner, repo, issueNumber } = parsed;
    
    // Try to call our backend API to fetch the GitHub issue data
    try {
      const response = await fetch(`/api/github/issues?owner=${owner}&repo=${repo}&issue=${issueNumber}`, {
        signal: AbortSignal.timeout(5000) // 5 second timeout
      });
      
      if (response.ok) {
        return await response.json();
      }
      
      // Don't try to parse JSON for non-OK responses as it might fail
      if (response.status === 404) {
        console.warn(`Backend API endpoint not found, falling back to mock implementation`);
        // Fall through to mock implementation below
      } else {
        try {
          const errorData = await response.json();
          throw new Error(errorData.message || `Failed to fetch GitHub issue: ${response.status}`);
        } catch (jsonError) {
          throw new Error(`Failed to fetch GitHub issue: ${response.status}`);
        }
      }
    } catch (fetchError) {
      console.warn('Backend API unavailable, falling back to mock implementation', fetchError);
      // Fall through to mock implementation below
    }
    
    // Fallback: Mock GitHub issue data for development purposes when backend is unavailable
    // This prevents the UI from breaking when the backend API is not implemented yet
    console.info(`Using mock GitHub issue data for ${owner}/${repo}#${issueNumber}`);
    return {
      title: `[Mock] Issue #${issueNumber} from ${owner}/${repo}`,
      body: `This is mock data for GitHub issue #${issueNumber} from repository ${owner}/${repo}. This is displayed because the backend API endpoint is not available.\n\nPlease implement the backend API endpoint at /api/github/issues to fetch real GitHub issue data.`,
      number: parseInt(issueNumber),
      html_url: url,
      repository: {
        name: repo,
        owner: {
          login: owner
        }
      },
      state: 'open',
      labels: [{ name: 'mock-data' }],
      assignees: [{ login: 'mock-user' }],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
  } catch (error) {
    console.error('Error fetching GitHub issue:', error);
    throw error;
  }
};
