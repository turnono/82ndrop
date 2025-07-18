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

  async sendMessageWithSSE(
    message: string,
    onUpdate: (update: any) => void
  ): Promise<ChatResponse> {
    const user = this.authService.getCurrentUser();
    if (!user) {
      throw new Error('User not authenticated');
    }

    if (!this.currentSessionId) {
      const session = await this.createSession();
      this.currentSessionId = session.id;
      await this.sessionHistoryService.createSession(
        `Video Session - ${new Date().toLocaleDateString()}`,
        session.id
      );
    }

    const firebaseUser = this.authService.getFirebaseUser();
    if (!firebaseUser) {
      throw new Error('Firebase user not available');
    }
    const token = await firebaseUser.getIdToken();

    const runRequest = {
      appName: this.appName,
      userId: user.uid,
      sessionId: this.currentSessionId,
      newMessage: {
        role: 'user',
        parts: [{ text: message }],
      },
      streaming: true,
    };

    const response = await fetch(`${this.apiUrl}/run_sse`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(runRequest),
    });

    if (!response.body) {
      throw new Error('No response body');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let lastMessage = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const json = JSON.parse(line.substring(6));
          onUpdate(json);
          if (json.content && json.content.parts && json.content.parts[0] && json.content.parts[0].text) {
            lastMessage = json.content.parts[0].text;
          }
        }
      }
    }

    return {
      response: lastMessage,
      session_id: this.currentSessionId,
      user_id: user.uid,
      timestamp: new Date().toISOString(),
    };
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