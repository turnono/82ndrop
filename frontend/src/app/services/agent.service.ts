import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError } from 'rxjs';
import { catchError, switchMap } from 'rxjs/operators';
import { AuthService } from './auth.service';

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
  private apiUrl = 'http://127.0.0.1:8000'; // Update for production
  private currentSessionId: string | null = null;

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
   * Send a message to the 82ndrop agent
   */
  async sendMessage(message: string): Promise<ChatResponse> {
    try {
      const headers = await this.getAuthHeaders();

      const chatMessage: ChatMessage = {
        message,
        session_id: this.currentSessionId || undefined,
      };

      const response = await this.http
        .post<ChatResponse>(`${this.apiUrl}/chat`, chatMessage, { headers })
        .toPromise();

      if (!response) {
        throw new Error('No response received from server');
      }

      // Update session ID for future messages
      if (response.session_id) {
        this.currentSessionId = response.session_id;
      }

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
   * Get user's chat sessions
   */
  async getSessions(): Promise<any> {
    try {
      const headers = await this.getAuthHeaders();
      return this.http.get(`${this.apiUrl}/sessions`, { headers }).toPromise();
    } catch (error) {
      console.error('Error fetching sessions:', error);
      throw error;
    }
  }

  /**
   * Delete a chat session
   */
  async deleteSession(sessionId: string): Promise<any> {
    try {
      const headers = await this.getAuthHeaders();
      return this.http
        .delete(`${this.apiUrl}/sessions/${sessionId}`, { headers })
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
      return this.http.get(`${this.apiUrl}/health`).toPromise();
    } catch (error) {
      console.error('Error checking API health:', error);
      throw error;
    }
  }
}
