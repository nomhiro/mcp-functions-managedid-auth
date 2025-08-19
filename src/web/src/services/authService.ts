import { DefaultAzureCredential } from '@azure/identity';

export class AuthService {
  private credential: DefaultAzureCredential | null = null;
  private functionAppUrl: string;

  constructor(functionAppUrl: string) {
    this.functionAppUrl = functionAppUrl;
    
    // Only initialize credential in production/Azure environment
    if (this.isAzureEnvironment()) {
      try {
        this.credential = new DefaultAzureCredential();
      } catch (error) {
        console.warn('Could not initialize Azure credential, using mock for development:', error);
      }
    }
  }

  private isAzureEnvironment(): boolean {
    // Check if running in Azure environment
    return !!(
      process.env.WEBSITE_SITE_NAME || // App Service
      process.env.AZURE_CLIENT_ID ||   // Managed Identity
      process.env.MSI_ENDPOINT        // Managed Identity endpoint
    );
  }

  async getAccessToken(): Promise<string> {
    try {
      if (this.credential && this.isAzureEnvironment()) {
        const tokenResponse = await this.credential.getToken([
          'https://management.azure.com/.default'
        ]);
        
        if (!tokenResponse) {
          throw new Error('Failed to get access token');
        }
        
        return tokenResponse.token;
      } else {
        // Return mock token for local development
        console.warn('Using mock token for local development');
        return 'mock-development-token';
      }
    } catch (error) {
      console.error('Error getting access token:', error);
      // Fallback to mock token for development
      return 'mock-development-token';
    }
  }

  async callMCPFunction(message: string): Promise<any> {
    try {
      const token = await this.getAccessToken();
      
      const response = await fetch(`${this.functionAppUrl}/api/test-chat`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error calling MCP function:', error);
      
      // For development, return a mock response
      if (!this.isAzureEnvironment()) {
        return {
          content: `Mock response for: "${message}". This is a development-only response. MCP tools would normally handle: current time, weather information, etc.`,
          timestamp: new Date().toISOString(),
          authenticated_user: 'dev-user'
        };
      }
      
      throw error;
    }
  }

  async testAuthentication(): Promise<any> {
    try {
      const token = await this.getAccessToken();
      
      const response = await fetch(`${this.functionAppUrl}/api/test-auth`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      });

      return await response.json();
    } catch (error) {
      console.error('Error testing authentication:', error);
      return {
        authenticated: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        note: 'This is expected in local development environment'
      };
    }
  }

  async callHealthCheck(): Promise<any> {
    try {
      const response = await fetch(`${this.functionAppUrl}/api/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error calling health check:', error);
      throw error;
    }
  }
}