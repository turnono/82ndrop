import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { BehaviorSubject, Observable, firstValueFrom, from } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { AuthService } from './auth.service';
import { SessionHistoryService } from './session-history.service';
import { environment } from '../../environments/environment';
import { Functions, httpsCallable } from '@angular/fire/functions';

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

export interface MockResponse {
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

  private messagesSubject = new BehaviorSubject<any[]>([]);
  public messages$ = this.messagesSubject.asObservable();

  constructor(
    private http: HttpClient,
    private authService: AuthService,
    private sessionHistoryService: SessionHistoryService,
    private functions: Functions
  ) {}

  private async getAuthHeaders(): Promise<HttpHeaders> {
    const user = this.authService.getCurrentUser();
    if (!user) {
      throw new Error('User not authenticated');
    }

    const firebaseUser = this.authService.getFirebaseUser();
    if (!firebaseUser) {
      throw new Error('Firebase user not available');
    }

    const token = await firebaseUser.getIdToken();
    return new HttpHeaders({
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    });
  }

  async getUserProfile(): Promise<UserProfile> {
    const user = this.authService.getCurrentUser();
    if (!user) {
      throw new Error('User not authenticated');
    }

    const firebaseUser = this.authService.getFirebaseUser();
    if (!firebaseUser) {
      throw new Error('Firebase user not available');
    }

    const token = await firebaseUser.getIdToken();
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    });

    try {
      const response = await firstValueFrom(
        this.http.get<UserProfile>(`${this.apiUrl}/user-profile`, {
          headers,
        })
      );
      return response;
    } catch (error) {
      console.error('Error fetching user profile:', error);
      throw error;
    }
  }

  private async createSession(): Promise<Session> {
    const user = this.authService.getCurrentUser();
    if (!user) {
      throw new Error('User not authenticated');
    }

    const firebaseUser = this.authService.getFirebaseUser();
    if (!firebaseUser) {
      throw new Error('Firebase user not available');
    }

    const token = await firebaseUser.getIdToken();
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    });

    try {
      const response = await firstValueFrom(
        this.http.post<Session>(
          `${this.apiUrl}/apps/${this.appName}/users/${user.uid}/sessions`,
          {},
          { headers }
        )
      );
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
      throw new Error("User not authenticated");
    }

    if (!this.currentSessionId) {
      const session = await this.createSession();
      this.currentSessionId = session.id;
    }

    const firebaseUser = this.authService.getFirebaseUser();
    if (!firebaseUser) {
      throw new Error("Firebase user not available");
    }
    const token = await firebaseUser.getIdToken();

    const requestBody = {
      app_name: this.appName,
      user_id: user.uid,
      session_id: this.currentSessionId,
      new_message: {
        role: 'user',
        parts: [{ text: message }],
      },
    };

    return new Promise(async (resolve, reject) => {
      try {
        const response = await fetch(`${this.apiUrl}/run_sse`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('Failed to get response reader');
        }

        const decoder = new TextDecoder();
        let lastMessage = '';
        let buffer = '';

        const processStream = async () => {
          while (true) {
            const { done, value } = await reader.read();
            if (done) {
              break;
            }

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (line.startsWith('data:')) {
                try {
                  const json = line.substring(5).trim();
                  if (json) {
                    const data = JSON.parse(json);
                    onUpdate(data);

                    if (data.type === 'message') {
                      lastMessage = data.content;
                    }

                    if (data.type === 'end') {
                      resolve({
                        response: lastMessage,
                        session_id: this.currentSessionId!,
                        user_id: user.uid,
                        timestamp: new Date().toISOString(),
                      });
                      return;
                    }
                  }
                } catch (error) {
                  console.error('Error parsing SSE data:', error);
                }
              }
            }
          }
        };

        processStream().catch(reject);

      } catch (error) {
        console.error('SSE fetch error:', error);
        reject(error);
      }
    });
  }

  async initializePayment(email: string, amount: number): Promise<any> {
    const initializePaymentUrl =
      'https://us-central1-taajirah.cloudfunctions.net/initializePayment';

    const headers = await this.getAuthHeaders();
    const url = initializePaymentUrl; // Use environment-specific URL
    return firstValueFrom(
      this.http.post<any>(url, { email, amount }, { headers })
    );
  }

  async deductCredits(amount: number): Promise<any> {
    const headers = await this.getAuthHeaders();
    return firstValueFrom(
      this.http.post<any>(
        `${this.apiUrl}/deduct-credits`,
        { amount },
        { headers }
      )
    );
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

      const response = await firstValueFrom(
        this.http.get<Session[]>(
          `${this.apiUrl}/apps/${this.appName}/users/${user.uid}/sessions`,
          { headers }
        )
      );

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

      return firstValueFrom(
        this.http.delete(
          `${this.apiUrl}/apps/${this.appName}/users/${user.uid}/sessions/${sessionId}`,
          { headers }
        )
      );
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
      return firstValueFrom(
        this.http.get(`${this.apiUrl}/list-apps`, { headers })
      );
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
      const response = await firstValueFrom(
        this.http.get<string[]>(`${this.apiUrl}/list-apps`, { headers })
      );

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

    // Get mock status
    const mockStatus = await firstValueFrom(this.getMockStatus());

    // Only check email authorization in non-mock mode
    if (!mockStatus.mock_mode && user.email !== 'turnono@gmail.com') {
      throw new Error('User not authorized for video generation');
    }

    const currentSession = this.sessionHistoryService.getCurrentSession();
    if (!currentSession) {
      throw new Error('No active session');
    }

    const headers = await this.getAuthHeaders();
    const response = await firstValueFrom(
      this.http.post<VideoGenerationResponse>(
        `${this.apiUrl}/generate-video`,
        {
          prompt,
          user_id: user.uid,
          session_id: currentSession.id,
        },
        { headers }
      )
    );

    if (!response) {
      throw new Error('No response received from video generation');
    }

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
      const response = await firstValueFrom(
        this.http.get<any>(`${this.apiUrl}/video-status/${jobId}`, { headers })
      );

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
      const response = await firstValueFrom(
        this.http.post<any>(
          `${this.apiUrl}/cancel-video/${jobId}`,
          {},
          { headers }
        )
      );

      return response;
    } catch (error) {
      console.error('Error cancelling video generation:', error);
      throw error;
    }
  }

  // Get mock mode status
  getMockStatus(): Observable<MockResponse> {
    return from(this.getAuthHeaders()).pipe(
      switchMap((headers) =>
        this.http.get<MockResponse>(`${this.apiUrl}/mock-status`, { headers })
      )
    );
  }
}
