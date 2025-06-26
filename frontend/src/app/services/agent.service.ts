import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError } from 'rxjs';
import { catchError, switchMap } from 'rxjs/operators';
import { AuthService } from './auth.service';
import { SessionHistoryService } from './session-history.service';
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
        // New logic: Find the response from the video generator agent
        const videoGenEvent = response.find(
          (event: any) => event.author === 'video_generator_agent' && event.content
        );

        if (
          videoGenEvent &&
          videoGenEvent.content &&
          videoGenEvent.content.parts &&
          videoGenEvent.content.parts[0] &&
          videoGenEvent.content.parts[0].text
        ) {
          agentContent = videoGenEvent.content.parts[0].text;
          responseTimestamp = videoGenEvent.timestamp || responseTimestamp;
        } else {
          // Fallback for debugging or if the agent fails
          console.warn('Could not find response from video_generator_agent. Displaying final event for debugging.');
          const finalEvent = response[response.length - 1];
          agentContent = finalEvent?.content?.parts?.[0]?.text || JSON.stringify(finalEvent, null, 2);
          responseTimestamp = finalEvent?.timestamp || responseTimestamp;
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
   * Send a message to the 82ndrop agent using ADK's built-in SSE for real-time updates
   */
  sendMessageWithSSE(
    message: string,
    onUpdate: (update: any) => void,
    onComplete: (finalResponse: ChatResponse) => void,
    onError: (error: any) => void
  ): () => void { // Returns an unsubscribe function
    const user = this.authService.getCurrentUser();
    if (!user) {
      onError(new Error('User not authenticated'));
      return () => {};
    }

    let currentSessionId = this.currentSessionId;

    const getHeaders = async () => {
      const firebaseUser = this.authService.getFirebaseUser();
      if (!firebaseUser) throw new Error('Firebase user not available');
      const token = await firebaseUser.getIdToken();
      return {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      };
    };

    const eventSource = new EventSourcePolyfill(`${this.apiUrl}/stream`, {
      headers: getHeaders(),
      method: 'POST',
      body: JSON.stringify({
        appName: this.appName,
        userId: user.uid,
        sessionId: currentSessionId, // Can be null, ADK will create a new one
        newMessage: {
          role: 'user',
          parts: [{ text: message }],
        },
      }),
    });

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onUpdate(data);

      // If this is the first event, we get the session ID
      if (!currentSessionId && data.session_id) {
        currentSessionId = data.session_id;
        this.currentSessionId = data.session_id;
      }
    };

    eventSource.onerror = (error) => {
      onError(error);
      eventSource.close();
    };

    // The stream is implicitly closed by the server when the agent is done.

    // Return a function to allow the client to close the connection manually
    return () => {
      if (eventSource.readyState !== EventSource.CLOSED) {
        eventSource.close();
      }
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
}
