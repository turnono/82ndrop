import { Injectable } from '@angular/core';
import {
  Database,
  ref,
  push,
  set,
  get,
  child,
  onValue,
  off,
  query,
  orderByChild,
  limitToLast,
} from 'firebase/database';
import { AuthService } from './auth.service';
import { BehaviorSubject, Observable } from 'rxjs';
import { environment } from '../../environments/environment';

function getCollectionName(base: string): string {
  return environment.production ? base : `staging_${base}`;
}

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
  private db!: Database;
  private sessionsSubject = new BehaviorSubject<ChatSession[]>([]);
  private currentSessionSubject = new BehaviorSubject<ChatSession | null>(null);
  private messagesSubject = new BehaviorSubject<ChatMessage[]>([]);
  private currentMessagesListener: (() => void) | null = null; // Track active listener

  public sessions$ = this.sessionsSubject.asObservable();
  public currentSession$ = this.currentSessionSubject.asObservable();
  public messages$ = this.messagesSubject.asObservable();

  constructor(private authService: AuthService) {
    // Initialize Firebase Database
    import('firebase/app').then(({ getApp }) => {
      import('firebase/database').then(({ getDatabase }) => {
        this.db = getDatabase(getApp());
        this.initializeRealtimeListeners();
      });
    });
  }

  private initializeRealtimeListeners() {
    this.authService.getUser().subscribe((user) => {
      if (user) {
        this.loadUserSessions(user.uid);
      } else {
        this.sessionsSubject.next([]);
        this.currentSessionSubject.next(null);
        this.messagesSubject.next([]);
      }
    });
  }

  private loadUserSessions(userId: string) {
    const sessionsRef = ref(
      this.db,
      `${getCollectionName('sessions')}/${userId}`
    );
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

    const sessionsRef = ref(
      this.db,
      `${getCollectionName('sessions')}/${user.uid}`
    );

    // Use ADK session ID if provided, otherwise generate new one
    let sessionRef;
    if (adkSessionId) {
      sessionRef = ref(
        this.db,
        `${getCollectionName('sessions')}/${user.uid}/${adkSessionId}`
      );
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

    // Remove any existing message listener
    if (this.currentMessagesListener) {
      console.log('🗑️ Removing old message listener');
      this.currentMessagesListener();
      this.currentMessagesListener = null;
    }

    // Clear messages immediately to show we're switching sessions
    this.messagesSubject.next([]);

    // Load session info
    const sessionRef = ref(
      this.db,
      `${getCollectionName('sessions')}/${user.uid}/${sessionId}`
    );
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
    const messagesRef = ref(
      this.db,
      `${getCollectionName('messages')}/${sessionId}`
    );
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

    const now = Date.now();
    const messageData = {
      ...message,
      sessionId,
      timestamp: now,
    };

    // Save message
    const messagesRef = ref(
      this.db,
      `${getCollectionName('messages')}/${sessionId}`
    );
    const newMessageRef = push(messagesRef);
    await set(newMessageRef, messageData);

    // Update session metadata
    const sessionRef = ref(
      this.db,
      `${getCollectionName('sessions')}/${user.uid}/${sessionId}`
    );
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

    const sessionRef = ref(
      this.db,
      `${getCollectionName('sessions')}/${user.uid}/${sessionId}/title`
    );
    await set(sessionRef, title);
  }

  async deleteSession(sessionId: string): Promise<void> {
    const user = this.authService.getCurrentUser();
    if (!user) throw new Error('User not authenticated');

    // Delete messages
    const messagesRef = ref(
      this.db,
      `${getCollectionName('messages')}/${sessionId}`
    );
    await set(messagesRef, null);

    // Delete session
    const sessionRef = ref(
      this.db,
      `${getCollectionName('sessions')}/${user.uid}/${sessionId}`
    );
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
  }
}
