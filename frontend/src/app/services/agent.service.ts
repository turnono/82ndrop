import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError } from 'rxjs';
import { catchError, switchMap } from 'rxjs/operators';
import { AuthService } from './auth.service';
import { SessionHistoryService } from './session-history.service';
import { environment } from '../../environments/environment';
import { tap } from 'rxjs/operators';
import { from } from 'rxjs';

export interface ChatMessage {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  user_id: string;
  timestamp: string;
}

// ADK-specific interfaces
export interface AgentRunRequest {
  appName: string;
  userId: string;
  sessionId: string;
  newMessage: {
    role: string;
    parts: { text: string }[];
  };
}

export interface AgentEvent {
  id: string;
  author: string;
  content: any;
  timestamp: string;
  type: string;
}

export interface Session {
  id: string;
  app_name: string;
  user_id: string;
  state?: any;
  events?: AgentEvent[];
}

export interface UserProfile {
  uid: string;
  email?: string;
  display_name?: string;
  agent_access: boolean;
  access_level: string;
  permissions: { [key: string]: any };
}

export interface VideoGenerationResponse {
  status: string;
  video_uri?: string;
  operation_name: string;
  user_id: string;
  session_id: string;
  created_at: string;
  videoUrl?: string; // For the transformed HTTPS URL
  error?: string; // For error messages when status is 'error'
}

interface MockResponse {
  mock_mode: boolean;
  message: string;
}

@Injectable({
  providedIn: 'root',
})
export class AgentService {
  private apiUrl = environment.apiUrl || 'http://127.0.0.1:8000';
  private currentSessionId: string | null = null;
  private appName = 'drop_agent';

  // Observable for chat messages
  private messagesSubject = new BehaviorSubject<any[]>([]);
  public messages$ = this.messagesSubject.asObservable();

  // Mock mode state
  private mockModeSubject = new BehaviorSubject<boolean>(true);
  mockMode$ = this.mockModeSubject.asObservable();

  constructor(
    private http: HttpClient,
    private authService: AuthService,
    private sessionHistoryService: SessionHistoryService
  ) {}

  /**
   * Get authenticated HTTP headers with Firebase ID token
   */
  private async getAuthHeaders(): Promise<HttpHeaders> {
    const user = this.authService.getCurrentUser();
    if (!user) {
      throw new Error('User not authenticated');
    }

    // Get the Firebase user for token operations
    const firebaseUser = this.authService.getFirebaseUser();
    if (!firebaseUser) {
      throw new Error('Firebase user not available');
    }

    const token = await firebaseUser.getIdToken();
    return new HttpHeaders({
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    });
  }

  /**
   * Get user profile and permissions
   */
  async getUserProfile(): Promise<UserProfile> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await this.http
        .get<UserProfile>(`${this.apiUrl}/user/profile`, { headers })
        .toPromise();
      if (!response) {
        throw new Error('No response received from server');
      }
      return response;
    } catch (error) {
      console.error('Error fetching user profile:', error);
      throw error;
    }
  }

  /**
   * Create a new session using ADK endpoints
   */
  private async createSession(): Promise<Session> {
    try {
      const headers = await this.getAuthHeaders();
      const user = this.authService.getCurrentUser();
      if (!user) {
        throw new Error('User not authenticated');
      }

      const userId = user.uid;
      const response = await this.http
        .post<Session>(
          `${this.apiUrl}/apps/${this.appName}/users/${userId}/sessions`,
          {},
          { headers }
        )
        .toPromise();

      if (!response) {
        throw new Error('Failed to create session');
      }

      return response;
    } catch (error) {
      console.error('Error creating session:', error);
      throw error;
    }
  }

  /**
   * Send a message to the 82ndrop agent using ADK endpoints
   */
  async sendMessage(message: string): Promise<ChatResponse> {
    try {
      const headers = await this.getAuthHeaders();
      const user = this.authService.getCurrentUser();
      if (!user) {
        throw new Error('User not authenticated');
      }

      // Create session if we don't have one
      if (!this.currentSessionId) {
        const session = await this.createSession();
        this.currentSessionId = session.id;

        // Sync session to Firebase for persistence
        try {
          await this.sessionHistoryService.createSession(
            `Video Session - ${new Date().toLocaleDateString()}`,
            session.id
          );
        } catch (firebaseError) {
          console.warn(
            'Firebase session sync failed (non-critical):',
            firebaseError
          );
        }
      }

      const runRequest = {
        appName: this.appName,
        userId: user.uid,
        sessionId: this.currentSessionId,
        newMessage: {
          role: 'user',
          parts: [{ text: message }],
        },
      };

      // Use the /run endpoint for better compatibility
      const response = await this.http
        .post<any>(`${this.apiUrl}/run`, runRequest, { headers })
        .toPromise();

      let agentContent = '';
      let responseTimestamp = new Date().toISOString();

      // Handle different response formats
      if (Array.isArray(response)) {
        // Look for the LAST agent response with actual text content (not function calls)
        let finalTextResponse = null;
        let workingAgents: string[] = [];

        // Process all events to build workflow steps and find final response
        for (const event of response) {
          if (event.author !== 'user' && event.content) {
            if (event.content.parts && event.content.parts[0]) {
              const part = event.content.parts[0];

              // Track function calls (workflow steps)
              if (part.functionCall) {
                const funcCall = part.functionCall;
                const agentName = this.getAgentDisplayName(
                  funcCall.args?.agent_name || funcCall.name
                );
                workingAgents.push(`🤖 ${agentName}`);
              }
              // Capture actual text responses
              else if (part.text && part.text.trim()) {
                finalTextResponse = {
                  content: part.text,
                  author: event.author,
                  timestamp: event.timestamp,
                };
              }
            }
          }
        }

        // Use the final text response if we found one
        if (finalTextResponse) {
          agentContent = finalTextResponse.content;
          responseTimestamp = finalTextResponse.timestamp || responseTimestamp;

          // Add workflow context if we tracked working agents
          if (workingAgents.length > 0) {
            const workflowInfo = `🔄 **Workflow:** ${workingAgents.join(
              ' → '
            )}\n\n`;
            agentContent = workflowInfo + agentContent;
          }
        } else if (workingAgents.length > 0) {
          // If we only have function calls, show workflow status
          agentContent = `🔄 **Multi-Agent Workflow Active**\n\n${workingAgents.join(
            ' → '
          )}\n\n⏳ Processing your request...`;
        } else {
          // Fallback to original logic
          const agentResponse = response.find(
            (event: any) => event.author !== 'user' && event.content
          );
          if (
            agentResponse &&
            agentResponse.content &&
            agentResponse.content.parts &&
            agentResponse.content.parts[0]
          ) {
            const part = agentResponse.content.parts[0];
            agentContent = part.text || JSON.stringify(part, null, 2);
            responseTimestamp = agentResponse.timestamp || responseTimestamp;
          }
        }
      } else if (response && typeof response === 'object') {
        agentContent =
          response.response ||
          response.content ||
          response.message ||
          JSON.stringify(response, null, 2);
        responseTimestamp = response.timestamp || responseTimestamp;
      } else if (typeof response === 'string') {
        agentContent = response;
      }

      if (!agentContent) {
        throw new Error('No valid response received from agent');
      }

      // Create a ChatResponse for backward compatibility
      const chatResponse: ChatResponse = {
        response: agentContent,
        session_id: this.currentSessionId,
        user_id: user.uid,
        timestamp: responseTimestamp,
      };

      // Save messages to Firebase for persistence (non-critical)
      try {
        if (this.currentSessionId) {
          // Save user message
          await this.sessionHistoryService.saveMessage(this.currentSessionId, {
            type: 'user',
            content: message,
          });

          // Save agent response
          await this.sessionHistoryService.saveMessage(this.currentSessionId, {
            type: 'agent',
            content: agentContent,
          });
        }
      } catch (firebaseError) {
        console.warn(
          'Firebase message save failed (non-critical):',
          firebaseError
        );
      }

      return chatResponse;
    } catch (error) {
      console.error('Error sending message to agent:', error);
      throw error;
    }
  }

  /**
   * Send a message to the 82ndrop agent using SSE for real-time updates
   */
  async sendMessageWithSSE(
    message: string,
    onUpdate: (update: any) => void
  ): Promise<ChatResponse> {
    try {
      // For now, use a fallback approach with simulated progress updates
      // since the server doesn't have a streaming endpoint yet
      console.log(
        'Using fallback approach with regular /run endpoint and simulated progress'
      );

      // Simulate workflow progress
      onUpdate({
        type: 'workflow_step',
        message: 'Starting analysis...',
        agents: ['🤖 Guide Agent'],
        timestamp: new Date().toISOString(),
      });

      // Small delay to show progress
      await new Promise((resolve) => setTimeout(resolve, 500));

      onUpdate({
        type: 'workflow_step',
        message: 'Searching for trends...',
        agents: ['🤖 Guide Agent', '🤖 Search Agent'],
        timestamp: new Date().toISOString(),
      });

      await new Promise((resolve) => setTimeout(resolve, 500));

      onUpdate({
        type: 'workflow_step',
        message: 'Creating composition...',
        agents: ['🤖 Guide Agent', '🤖 Search Agent', '🤖 Prompt Writer Agent'],
        timestamp: new Date().toISOString(),
      });

      // Use the existing working sendMessage method
      const response = await this.sendMessage(message);

      // Send final response update
      onUpdate({
        type: 'final_response',
        message: response.response,
        timestamp: response.timestamp,
      });

      return response;
    } catch (error) {
      console.error('Error sending message with SSE fallback:', error);
      throw error;
    }
  }

  /**
   * Get user-friendly agent names
   */
  private getAgentDisplayName(agentName: string): string {
    const agentNames: { [key: string]: string } = {
      guide_agent: 'Guide Agent',
      search_agent: 'Search Agent',
      prompt_writer_agent: 'Prompt Writer Agent',
      drop_agent: '82ndrop Root Agent',
      task_master_agent: 'Task Master Agent',
    };

    return (
      agentNames[agentName] ||
      agentName.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())
    );
  }

  /**
   * Start a new chat session
   */
  startNewSession(): void {
    this.currentSessionId = null;
    this.messagesSubject.next([]);
  }

  /**
   * Get current session ID
   */
  getCurrentSessionId(): string | null {
    return this.currentSessionId;
  }

  /**
   * Set current session ID (for loading existing sessions)
   */
  setCurrentSession(sessionId: string): void {
    this.currentSessionId = sessionId;
  }

  /**
   * Get user's chat sessions using ADK endpoints
   */
  async getSessions(): Promise<Session[]> {
    try {
      const headers = await this.getAuthHeaders();
      const user = this.authService.getCurrentUser();
      if (!user) {
        throw new Error('User not authenticated');
      }

      const response = await this.http
        .get<Session[]>(
          `${this.apiUrl}/apps/${this.appName}/users/${user.uid}/sessions`,
          { headers }
        )
        .toPromise();

      return response || [];
    } catch (error) {
      console.error('Error fetching sessions:', error);
      throw error;
    }
  }

  /**
   * Delete a chat session using ADK endpoints
   */
  async deleteSession(sessionId: string): Promise<any> {
    try {
      const headers = await this.getAuthHeaders();
      const user = this.authService.getCurrentUser();
      if (!user) {
        throw new Error('User not authenticated');
      }

      return this.http
        .delete(
          `${this.apiUrl}/apps/${this.appName}/users/${user.uid}/sessions/${sessionId}`,
          { headers }
        )
        .toPromise();
    } catch (error) {
      console.error('Error deleting session:', error);
      throw error;
    }
  }

  /**
   * Check API health
   */
  async checkHealth(): Promise<any> {
    try {
      const headers = await this.getAuthHeaders();
      // Use list-apps endpoint as a health check since /health doesn't exist in ADK
      return this.http.get(`${this.apiUrl}/list-apps`, { headers }).toPromise();
    } catch (error) {
      console.error('Error checking API health:', error);
      throw error;
    }
  }

  /**
   * List available apps using ADK endpoints
   */
  async listApps(): Promise<string[]> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await this.http
        .get<string[]>(`${this.apiUrl}/list-apps`, { headers })
        .toPromise();

      return response || [];
    } catch (error) {
      console.error('Error listing apps:', error);
      throw error;
    }
  }

  /**
   * Transform a GCS URL to a cloud storage URL
   */
  transformGcsUrl(gcsUrl: string): string {
    if (!gcsUrl) return '';
    if (!gcsUrl.startsWith('gs://')) return gcsUrl;

    // Remove 'gs://' and split into bucket and path
    const withoutProtocol = gcsUrl.replace('gs://', '');
    const [bucket, ...pathParts] = withoutProtocol.split('/');
    const path = pathParts.join('/');

    // Return the cloud storage URL
    return `https://storage.cloud.google.com/${bucket}/${path}`;
  }

  /**
   * Generate video from prompt using VEO3 API
   */
  async generateVideo(prompt: string): Promise<VideoGenerationResponse> {
    const user = this.authService.getCurrentUser();
    if (!user) {
      throw new Error('User not authenticated');
    }

    if (user.email !== 'turnono@gmail.com') {
      throw new Error('User not authorized for video generation');
    }

    const currentSession = this.sessionHistoryService.getCurrentSession();
    if (!currentSession) {
      throw new Error('No active session');
    }

    const headers = await this.getAuthHeaders();
    const response = await this.http
      .post<VideoGenerationResponse>(
        `${this.apiUrl}/generate-video`,
        {
          prompt,
          user_id: user.uid,
          session_id: currentSession.id,
        },
        { headers }
      )
      .toPromise();

    if (!response) {
      throw new Error('No response received from video generation');
    }

    // Transform the video URL if it exists in the response
    if (response.video_uri) {
      response.videoUrl = this.transformGcsUrl(response.video_uri);
    }

    return response;
  }

  /**
   * Check video generation status
   */
  async checkVideoStatus(jobId: string): Promise<any> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await this.http
        .get<any>(`${this.apiUrl}/video-status/${jobId}`, { headers })
        .toPromise();

      return response;
    } catch (error) {
      console.error('Error checking video status:', error);
      throw error;
    }
  }

  /**
   * Cancel video generation
   */
  async cancelVideoGeneration(jobId: string): Promise<any> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await this.http
        .post<any>(`${this.apiUrl}/cancel-video/${jobId}`, {}, { headers })
        .toPromise();

      return response;
    } catch (error) {
      console.error('Error cancelling video generation:', error);
      throw error;
    }
  }

  // Toggle mock mode
  toggleMockMode(): Observable<MockResponse> {
    return from(this.getAuthHeaders()).pipe(
      switchMap((headers) =>
        this.http
          .post<MockResponse>(`${this.apiUrl}/toggle-mock`, {}, { headers })
          .pipe(
            tap((response) => {
              this.mockModeSubject.next(response.mock_mode);
            })
          )
      )
    );
  }

  // Get mock mode status
  getMockStatus(): Observable<MockResponse> {
    return from(this.getAuthHeaders()).pipe(
      switchMap((headers) =>
        this.http
          .get<MockResponse>(`${this.apiUrl}/mock-status`, { headers })
          .pipe(
            tap((response) => {
              this.mockModeSubject.next(response.mock_mode);
            })
          )
      )
    );
  }
}
