import { Injectable } from '@angular/core';
import { AuthService } from './auth.service';
import { BehaviorSubject, Observable } from 'rxjs';
import {
  Database,
  ref,
  push,
  set,
  get,
  onValue,
  off,
  query,
  orderByChild,
  limitToLast,
} from '@angular/fire/database';

export interface ChatSession {
  id: string;
  title: string;
  userId: string;
  createdAt: number;
  updatedAt: number;
  messageCount: number;
  lastMessage?: string;
  preview?: string;
}

export interface ChatMessage {
  id: string;
  sessionId: string;
  type: 'user' | 'agent' | 'system' | 'progress';
  content: string;
  timestamp: number;
  workflowSteps?: string[];
}

@Injectable({
  providedIn: 'root',
})
export class SessionHistoryService {
  private db: Database;
  private sessionsSubject = new BehaviorSubject<ChatSession[]>([]);
  private currentSessionSubject = new BehaviorSubject<ChatSession | null>(null);
  private messagesSubject = new BehaviorSubject<ChatMessage[]>([]);
  private currentMessagesListener: (() => void) | null = null; // Track active listener

  public sessions$ = this.sessionsSubject.asObservable();
  public currentSession$ = this.currentSessionSubject.asObservable();
  public messages$ = this.messagesSubject.asObservable();

  constructor(private authService: AuthService, db: Database) {
    // Use constructor injection for Angular Fire Database
    this.db = db;
    console.log('✅ Firebase Database initialized successfully');
    this.initializeRealtimeListeners();
  }

  private ensureDatabase(): boolean {
    // Database is always available when injected via Angular Fire
    return true;
  }

  private initializeRealtimeListeners() {
    this.authService.getUser().subscribe((user) => {
      if (user && this.ensureDatabase()) {
        this.loadUserSessions(user.uid);
      } else {
        this.sessionsSubject.next([]);
        this.currentSessionSubject.next(null);
        this.messagesSubject.next([]);
      }
    });
  }

  private loadUserSessions(userId: string) {
    if (!this.ensureDatabase()) return;

    const sessionsRef = ref(this.db, `sessions/${userId}`);
    const sessionsQuery = query(
      sessionsRef,
      orderByChild('updatedAt'),
      limitToLast(50)
    );

    onValue(sessionsQuery, (snapshot) => {
      const sessions: ChatSession[] = [];

      if (snapshot.exists()) {
        snapshot.forEach((childSnapshot) => {
          const session = {
            id: childSnapshot.key!,
            ...childSnapshot.val(),
          } as ChatSession;
          sessions.unshift(session); // Most recent first
        });
      }

      this.sessionsSubject.next(sessions);
    });
  }

  async createSession(
    title?: string,
    adkSessionId?: string
  ): Promise<ChatSession> {
    const user = this.authService.getCurrentUser();
    if (!user) throw new Error('User not authenticated');

    const now = Date.now();
    const sessionData = {
      title: title || `New Session ${new Date().toLocaleDateString()}`,
      userId: user.uid,
      createdAt: now,
      updatedAt: now,
      messageCount: 0,
      lastMessage: '',
      preview: 'New conversation started',
    };

    // If Firebase Database is not available, return a local session
    if (!this.ensureDatabase()) {
      const session: ChatSession = {
        id: adkSessionId || `session_${now}`,
        ...sessionData,
      };
      this.currentSessionSubject.next(session);
      return session;
    }

    const sessionsRef = ref(this.db, `sessions/${user.uid}`);

    // Use ADK session ID if provided, otherwise generate new one
    let sessionRef;
    if (adkSessionId) {
      sessionRef = ref(this.db, `sessions/${user.uid}/${adkSessionId}`);
      await set(sessionRef, sessionData);
    } else {
      sessionRef = push(sessionsRef);
      await set(sessionRef, sessionData);
    }

    const session: ChatSession = {
      id: adkSessionId || sessionRef.key!,
      ...sessionData,
    };

    this.currentSessionSubject.next(session);
    return session;
  }

  async loadSession(sessionId: string): Promise<ChatMessage[]> {
    const user = this.authService.getCurrentUser();
    if (!user) throw new Error('User not authenticated');

    console.log('🔄 Loading session:', sessionId);

    // If Firebase Database is not available, return empty messages
    if (!this.ensureDatabase()) {
      console.log(
        '📭 Firebase Database not available, returning empty messages'
      );
      this.messagesSubject.next([]);
      return [];
    }

    // Remove any existing message listener
    if (this.currentMessagesListener) {
      console.log('🗑️ Removing old message listener');
      this.currentMessagesListener();
      this.currentMessagesListener = null;
    }

    // Clear messages immediately to show we're switching sessions
    this.messagesSubject.next([]);

    // Load session info
    const sessionRef = ref(this.db, `sessions/${user.uid}/${sessionId}`);
    const sessionSnapshot = await get(sessionRef);

    if (sessionSnapshot.exists()) {
      const session: ChatSession = {
        id: sessionId,
        ...sessionSnapshot.val(),
      };
      console.log('📋 Session info loaded:', session.title);
      this.currentSessionSubject.next(session);
    } else {
      console.log('⚠️ Session not found in Firebase:', sessionId);
      this.currentSessionSubject.next(null);
      return [];
    }

    // Load messages for this specific session
    const messagesRef = ref(this.db, `messages/${sessionId}`);
    const messagesQuery = query(messagesRef, orderByChild('timestamp'));

    return new Promise((resolve) => {
      const unsubscribe = onValue(
        messagesQuery,
        (snapshot) => {
          const messages: ChatMessage[] = [];

          if (snapshot.exists()) {
            snapshot.forEach((childSnapshot) => {
              const message = {
                id: childSnapshot.key!,
                ...childSnapshot.val(),
              } as ChatMessage;
              messages.push(message);
            });
            console.log(
              `💬 Loaded ${messages.length} messages for session ${sessionId}`
            );
          } else {
            console.log(`📭 No messages found for session ${sessionId}`);
          }

          this.messagesSubject.next(messages);
          resolve(messages);
        },
        { onlyOnce: true }
      );

      // Store the unsubscribe function
      this.currentMessagesListener = unsubscribe;
    });
  }

  async saveMessage(
    sessionId: string,
    message: Omit<ChatMessage, 'id' | 'sessionId' | 'timestamp'>
  ): Promise<void> {
    const user = this.authService.getCurrentUser();
    if (!user) throw new Error('User not authenticated');

    // If Firebase Database is not available, just log the message
    if (!this.ensureDatabase()) {
      console.log(
        '💬 Saving message (offline mode):',
        message.content.substring(0, 50)
      );
      return;
    }

    const now = Date.now();
    const messageData = {
      ...message,
      sessionId,
      timestamp: now,
    };

    // Save message
    const messagesRef = ref(this.db, `messages/${sessionId}`);
    const newMessageRef = push(messagesRef);
    await set(newMessageRef, messageData);

    // Update session metadata
    const sessionRef = ref(this.db, `sessions/${user.uid}/${sessionId}`);
    const sessionSnapshot = await get(sessionRef);

    if (sessionSnapshot.exists()) {
      const sessionData = sessionSnapshot.val();
      const preview =
        message.type === 'user'
          ? message.content.substring(0, 100) + '...'
          : message.type === 'agent'
          ? 'Generated video prompt'
          : sessionData.preview;

      await set(sessionRef, {
        ...sessionData,
        updatedAt: now,
        messageCount: (sessionData.messageCount || 0) + 1,
        lastMessage: message.content.substring(0, 100),
        preview,
      });
    }
  }

  async updateSessionTitle(sessionId: string, title: string): Promise<void> {
    const user = this.authService.getCurrentUser();
    if (!user) throw new Error('User not authenticated');

    if (!this.ensureDatabase()) {
      console.log('📝 Updating session title (offline mode):', title);
      return;
    }

    const sessionRef = ref(this.db, `sessions/${user.uid}/${sessionId}`);
    const sessionSnapshot = await get(sessionRef);

    if (sessionSnapshot.exists()) {
      const sessionData = sessionSnapshot.val();
      await set(sessionRef, {
        ...sessionData,
        title: title,
        updatedAt: Date.now(),
      });
    }
  }

  async deleteSession(sessionId: string): Promise<void> {
    const user = this.authService.getCurrentUser();
    if (!user) throw new Error('User not authenticated');

    if (!this.ensureDatabase()) {
      console.log('🗑️ Deleting session (offline mode):', sessionId);
      return;
    }

    // Delete messages
    const messagesRef = ref(this.db, `messages/${sessionId}`);
    await set(messagesRef, null);

    // Delete session
    const sessionRef = ref(this.db, `sessions/${user.uid}/${sessionId}`);
    await set(sessionRef, null);
  }

  getCurrentSession(): ChatSession | null {
    return this.currentSessionSubject.value;
  }

  getCurrentMessages(): ChatMessage[] {
    return this.messagesSubject.value;
  }

  // Auto-generate session title from first message
  async generateSessionTitle(
    sessionId: string,
    firstMessage: string
  ): Promise<void> {
    const words = firstMessage.split(' ').slice(0, 6).join(' ');
    const title = words.length > 0 ? words + '...' : 'New Session';
    await this.updateSessionTitle(sessionId, title);
  }

  // Cleanup listeners
  destroy() {
    // Remove Firebase listeners when service is destroyed
    // This prevents memory leaks
    if (this.currentMessagesListener) {
      this.currentMessagesListener();
      this.currentMessagesListener = null;
    }
  }

  // --- Real-time Video Job Updates ---
  listenForVideoJob(jobId: string): Observable<any> {
    if (!this.ensureDatabase()) {
      console.log('📺 Video job listening (offline mode):', jobId);
      return new BehaviorSubject(null).asObservable();
    }

    const jobRef = ref(this.db, `video_jobs/${jobId}`);

    return new Observable((observer) => {
      const unsubscribe = onValue(jobRef, (snapshot) => {
        if (snapshot.exists()) {
          const jobData = snapshot.val();
          console.log(`[Firebase Listener] Job ${jobId} updated:`, jobData);
          observer.next(jobData); // Emit the updated job data

          // If job is complete or failed, stop listening
          if (jobData.status === 'complete' || jobData.status === 'failed') {
            observer.complete(); // Complete the observable stream
          }
        } else {
          console.log(`[Firebase Listener] Job ${jobId} not found yet.`);
        }
      });

      // Return a cleanup function to be called on unsubscription
      return () => {
        console.log(`[Firebase Listener] Unsubscribing from job ${jobId}`);
        unsubscribe();
      };
    });
  }
}
