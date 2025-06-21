import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError } from 'rxjs';
import { catchError, switchMap } from 'rxjs/operators';
import { AuthService } from './auth.service';
import { environment } from '../../environments/environment';

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
  app_name: string;
  user_id: string;
  session_id: string;
  new_message: {
    role: string;
    parts: { text: string }[];
  };
}

export interface AgentEvent {
  id: string;
  author: string;
  content: string;
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

@Injectable({
  providedIn: 'root',
})
export class AgentService {
  private apiUrl = environment.apiUrl || 'http://127.0.0.1:8000'; // Use environment config
  private currentSessionId: string | null = null;
  private appName = 'drop_agent'; // Updated app name

  // Observable for chat messages
  private messagesSubject = new BehaviorSubject<any[]>([]);
  public messages$ = this.messagesSubject.asObservable();

  constructor(private http: HttpClient, private authService: AuthService) {}

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
      }

      const runRequest = {
        app_name: this.appName,
        user_id: user.uid,
        session_id: this.currentSessionId,
        new_message: {
          role: 'user',
          parts: [{ text: message }],
        },
      };

      const events = await this.http
        .post<AgentEvent[]>(`${this.apiUrl}/run`, runRequest, { headers })
        .toPromise();

      if (!events || events.length === 0) {
        throw new Error('No response received from agent');
      }

      // Find the agent's response from the events
      const agentResponse = events.find(
        (event) => event.author !== 'user' && event.content
      );
      if (!agentResponse) {
        throw new Error('No agent response found in events');
      }

      // Create a ChatResponse for backward compatibility
      const response: ChatResponse = {
        response: agentResponse.content,
        session_id: this.currentSessionId,
        user_id: user.uid,
        timestamp: agentResponse.timestamp || new Date().toISOString(),
      };

      // Add to messages stream
      const currentMessages = this.messagesSubject.value;
      const newMessages = [
        ...currentMessages,
        { type: 'user', content: message, timestamp: new Date().toISOString() },
        {
          type: 'agent',
          content: response.response,
          timestamp: response.timestamp,
        },
      ];
      this.messagesSubject.next(newMessages);

      return response;
    } catch (error) {
      console.error('Error sending message to agent:', error);
      throw error;
    }
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
      // Use list-apps endpoint as a health check since /health doesn't exist in ADK
      return this.http.get(`${this.apiUrl}/list-apps`).toPromise();
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
}
