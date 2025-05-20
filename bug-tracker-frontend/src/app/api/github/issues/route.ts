/**
 * API route handler for fetching GitHub issues
 * This endpoint proxies requests to the GitHub API and returns issue data
 */
import { NextResponse } from 'next/server';

// GitHub API base URL
const GITHUB_API_BASE = 'https://api.github.com';

/**
 * GET handler for /api/github/issues endpoint
 * Query parameters:
 * - owner: GitHub repository owner
 * - repo: GitHub repository name
 * - issue: GitHub issue number
 */
export async function GET(request: Request) {
  try {
    // Get the URL object to extract query parameters
    const { searchParams } = new URL(request.url);
    
    // Extract required parameters
    const owner = searchParams.get('owner');
    const repo = searchParams.get('repo');
    const issueNumber = searchParams.get('issue');
    
    // Validate parameters
    if (!owner || !repo || !issueNumber) {
      return NextResponse.json(
        { message: 'Missing required parameters: owner, repo, and issue are required' },
        { status: 400 }
      );
    }
    
    // Construct GitHub API URL
    const githubApiUrl = `${GITHUB_API_BASE}/repos/${owner}/${repo}/issues/${issueNumber}`;
    
    // Set up headers for GitHub API request
    const headers = new Headers();
    headers.set('Accept', 'application/vnd.github.v3+json');
    headers.set('User-Agent', 'Bug-Tracker-App');
    
    // Add GitHub token if available
    const githubToken = process.env.GITHUB_TOKEN;
    if (githubToken) {
      headers.set('Authorization', `token ${githubToken}`);
    }
    
    // Fetch data from GitHub API
    const response = await fetch(githubApiUrl, { headers });
    
    // Handle HTTP errors
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`GitHub API error (${response.status}):`, errorText);
      
      if (response.status === 404) {
        return NextResponse.json(
          { message: `GitHub issue not found: ${owner}/${repo}#${issueNumber}` },
          { status: 404 }
        );
      }
      
      return NextResponse.json(
        { message: `Error fetching GitHub issue: ${response.statusText}` },
        { status: response.status }
      );
    }
    
    // Parse and return the GitHub issue data
    const issueData = await response.json();
    
    // Add repository info to response (not included in GitHub's issue endpoint response)
    issueData.repository = {
      name: repo,
      owner: {
        login: owner
      }
    };
    
    // Create a response with the issue data
    const apiResponse = NextResponse.json(issueData);
    
    // Add CORS headers for better compatibility with the FastAPI backend
    apiResponse.headers.set('Access-Control-Allow-Origin', '*');
    apiResponse.headers.set('Access-Control-Allow-Methods', 'GET, OPTIONS');
    apiResponse.headers.set('Access-Control-Allow-Headers', 'Content-Type');
    
    return apiResponse;
  } catch (error) {
    console.error('Error in GitHub issues API route:', error);
    return NextResponse.json(
      { message: 'Internal server error' },
      { status: 500 }
    );
  }
}
