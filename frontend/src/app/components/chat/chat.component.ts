import {
  Component,
  OnInit,
  OnDestroy,
  ViewChild,
  ElementRef,
  AfterViewChecked,
  Output,
  EventEmitter,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AgentService, ChatResponse } from '../../services/agent.service';
import { AuthService } from '../../services/auth.service';
import { Subscription } from 'rxjs';

interface ChatMessage {
  type: 'user' | 'agent' | 'system';
  content: string;
  timestamp: string;
  loading?: boolean;
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="chat-container">
      <!-- Header -->
      <div class="chat-header">
        <button class="back-button" (click)="onBackToMenu()">← Back</button>
        <div class="chat-title">
          <h2>AI Agent Chat</h2>
          <div class="connection-status" [class.connected]="isConnected">
            {{ isConnected ? 'Connected' : 'Connecting...' }}
          </div>
        </div>
      </div>

      <!-- Messages -->
      <div class="chat-messages" #messagesContainer>
        <div
          *ngFor="let message of messages"
          class="message"
          [class.user-message]="message.type === 'user'"
          [class.agent-message]="message.type === 'agent'"
          [class.system-message]="message.type === 'system'"
        >
          <div class="message-content">
            <div class="message-text">{{ message.content }}</div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>

          <div *ngIf="message.loading" class="loading-indicator">
            <div class="spinner"></div>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div class="chat-input">
        <div class="input-container">
          <textarea
            [(ngModel)]="currentMessage"
            (keydown)="onEnterKey($event)"
            placeholder="Ask me to create a video prompt..."
            [disabled]="isLoading"
            rows="2"
          >
          </textarea>
          <button
            (click)="sendMessage()"
            [disabled]="!currentMessage.trim() || isLoading"
            class="send-button"
          >
            <span *ngIf="!isLoading">Send</span>
            <span *ngIf="isLoading">Sending...</span>
          </button>
        </div>
      </div>

      <!-- Error Message -->
      <div *ngIf="error" class="error-message">
        {{ error }}
        <button (click)="clearError()" class="close-error">×</button>
      </div>
    </div>
  `,
  styles: [
    `
      .chat-container {
        display: flex;
        flex-direction: column;
        height: 100vh;
        background: white;
        position: relative;
      }

      .chat-header {
        display: flex;
        align-items: center;
        padding: 1rem;
        background: #f8f9fa;
        border-bottom: 1px solid #e0e0e0;
        flex-shrink: 0;
      }

      .back-button {
        background: none;
        border: none;
        font-size: 1rem;
        color: #007bff;
        cursor: pointer;
        padding: 0.5rem;
        margin-right: 1rem;
        border-radius: 4px;
      }

      .back-button:hover {
        background: #e9ecef;
      }

      .chat-title h2 {
        margin: 0;
        font-size: 1.2rem;
        color: #333;
      }

      .connection-status {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.2rem;
      }

      .connection-status.connected {
        color: #28a745;
      }

      .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 1rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        scroll-behavior: smooth;
        -webkit-overflow-scrolling: touch;
      }

      .message {
        display: flex;
        max-width: 80%;
      }

      .user-message {
        align-self: flex-end;
      }

      .agent-message,
      .system-message {
        align-self: flex-start;
      }

      .message-content {
        background: #f1f3f4;
        padding: 0.75rem;
        border-radius: 12px;
        position: relative;
      }

      .user-message .message-content {
        background: #007bff;
        color: white;
      }

      .system-message .message-content {
        background: #ffc107;
        color: #212529;
      }

      .message-text {
        margin-bottom: 0.25rem;
        white-space: pre-wrap;
        word-wrap: break-word;
      }

      .message-time {
        font-size: 0.7rem;
        opacity: 0.7;
      }

      .loading-indicator {
        display: flex;
        align-items: center;
        margin-left: 0.5rem;
      }

      .spinner {
        width: 16px;
        height: 16px;
        border: 2px solid #f3f3f3;
        border-top: 2px solid #007bff;
        border-radius: 50%;
        animation: spin 1s linear infinite;
      }

      @keyframes spin {
        0% {
          transform: rotate(0deg);
        }
        100% {
          transform: rotate(360deg);
        }
      }

      .chat-input {
        padding: 1rem;
        background: #f8f9fa;
        border-top: 1px solid #e0e0e0;
        flex-shrink: 0;
      }

      .input-container {
        display: flex;
        gap: 0.5rem;
        align-items: flex-end;
      }

      textarea {
        flex: 1;
        border: 1px solid #ced4da;
        border-radius: 4px;
        padding: 0.75rem;
        resize: none;
        min-height: 44px;
        max-height: 120px;
        font-size: 16px; /* Prevents zoom on iOS */
        font-family: inherit;
        line-height: 1.4;
      }

      textarea:focus {
        outline: none;
        border-color: #007bff;
        box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
      }

      .send-button {
        background: #007bff;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.75rem 1rem;
        cursor: pointer;
        font-size: 14px;
        min-width: 70px;
        height: 44px;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .send-button:hover:not(:disabled) {
        background: #0056b3;
      }

      .send-button:disabled {
        background: #6c757d;
        cursor: not-allowed;
      }

      .error-message {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: #dc3545;
        color: white;
        padding: 1rem 2rem;
        border-radius: 4px;
        display: flex;
        align-items: center;
        gap: 1rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1000;
      }

      .close-error {
        background: none;
        border: none;
        color: white;
        font-size: 1.2rem;
        cursor: pointer;
        padding: 0;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
      }

      .close-error:hover {
        background: rgba(255, 255, 255, 0.2);
      }

      /* Mobile optimizations */
      @media (max-width: 768px) {
        .chat-header {
          padding: 0.75rem;
        }

        .chat-title h2 {
          font-size: 1.1rem;
        }

        .message {
          max-width: 90%;
        }

        .message-content {
          padding: 0.6rem;
        }

        .chat-input {
          padding: 0.75rem;
        }

        textarea {
          font-size: 16px; /* Critical for iOS to prevent zoom */
        }
      }
    `,
  ],
})
export class ChatComponent implements OnInit, OnDestroy, AfterViewChecked {
  @ViewChild('messagesContainer') private messagesContainer!: ElementRef;
  @Output() backToMenu = new EventEmitter<void>();

  messages: ChatMessage[] = [];
  currentMessage = '';
  isLoading = false;
  isConnected = false;
  error: string | null = null;
  private subscriptions = new Subscription();
  private shouldScrollToBottom = false;

  constructor(
    private agentService: AgentService,
    private authService: AuthService
  ) {}

  ngOnInit() {
    this.checkConnection();
    this.addSystemMessage(
      "Welcome! I'm your 82ndrop AI agent. Ask me to create video prompts for you."
    );
  }

  ngAfterViewChecked() {
    if (this.shouldScrollToBottom) {
      this.scrollToBottom();
      this.shouldScrollToBottom = false;
    }
  }

  ngOnDestroy() {
    this.subscriptions.unsubscribe();
  }

  private scrollToBottom(): void {
    try {
      if (this.messagesContainer) {
        const element = this.messagesContainer.nativeElement;
        // Force scroll to bottom with a slight delay to ensure DOM is updated
        setTimeout(() => {
          element.scrollTop = element.scrollHeight;
        }, 100);
      }
    } catch (err) {
      console.error('Error scrolling to bottom:', err);
    }
  }

  private async checkConnection() {
    try {
      await this.agentService.checkHealth();
      this.isConnected = true;
      this.addSystemMessage('Connected to 82ndrop AI Agent');
    } catch (error) {
      this.isConnected = false;
      this.addSystemMessage(
        'Failed to connect to agent. Please check your authentication.'
      );
      console.error('Connection check failed:', error);
    }
  }

  private addSystemMessage(content: string) {
    this.messages.push({
      type: 'system',
      content,
      timestamp: new Date().toISOString(),
    });
    this.shouldScrollToBottom = true;
  }

  private addUserMessage(content: string) {
    this.messages.push({
      type: 'user',
      content,
      timestamp: new Date().toISOString(),
    });
    this.shouldScrollToBottom = true;
  }

  private addAgentMessage(content: string, timestamp?: string) {
    this.messages.push({
      type: 'agent',
      content,
      timestamp: timestamp || new Date().toISOString(),
    });
    this.shouldScrollToBottom = true;
  }

  onEnterKey(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  async sendMessage() {
    if (!this.currentMessage.trim() || this.isLoading) {
      return;
    }

    const message = this.currentMessage.trim();
    this.currentMessage = '';
    this.isLoading = true;
    this.error = null;

    // Add user message
    this.addUserMessage(message);

    // Add loading message
    const loadingMessage: ChatMessage = {
      type: 'agent',
      content: 'Thinking...',
      timestamp: new Date().toISOString(),
      loading: true,
    };
    this.messages.push(loadingMessage);
    this.shouldScrollToBottom = true;

    try {
      const response: ChatResponse = await this.agentService.sendMessage(
        message
      );

      // Remove loading message
      this.messages = this.messages.filter((m) => !m.loading);

      // Add agent response
      this.addAgentMessage(response.response, response.timestamp);
    } catch (error: any) {
      console.error('Error sending message:', error);

      // Remove loading message
      this.messages = this.messages.filter((m) => !m.loading);

      // Show error
      if (error.status === 401 || error.status === 403) {
        this.error = 'Authentication failed. Please sign in again.';
        this.addSystemMessage(
          'Authentication error. Please refresh and sign in again.'
        );
      } else {
        this.error =
          error.message || 'Failed to send message. Please try again.';
        this.addSystemMessage('Error: ' + this.error);
      }
    } finally {
      this.isLoading = false;
    }
  }

  clearError() {
    this.error = null;
  }

  onBackToMenu() {
    this.backToMenu.emit();
  }

  formatTime(timestamp: string): string {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  }
}
