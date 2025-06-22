import {
  Component,
  OnInit,
  OnDestroy,
  ViewChild,
  ElementRef,
  AfterViewChecked,
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
      <div class="chat-header">
        <h3>82ndrop AI Agent</h3>
        <div class="status-indicator" [class.connected]="isConnected">
          {{ isConnected ? 'Connected' : 'Disconnected' }}
        </div>
      </div>

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
        height: 600px;
        max-width: 800px;
        margin: 0 auto;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        background: white;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        position: relative;
      }

      .chat-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem;
        background: #f8f9fa;
        border-bottom: 1px solid #e0e0e0;
        border-radius: 8px 8px 0 0;
      }

      .status-indicator {
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        background: #dc3545;
        color: white;
      }

      .status-indicator.connected {
        background: #28a745;
      }

      .chat-messages {
        flex: 1;
        overflow-y: scroll;
        overflow-x: hidden;
        padding: 1rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        scroll-behavior: smooth;
        -webkit-overflow-scrolling: touch;
        min-height: 0;
        max-height: calc(
          600px - 120px
        ); /* Account for header + input on desktop */
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
        border-top: 1px solid #e0e0e0;
        background: #f8f9fa;
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
        padding: 0.5rem;
        resize: vertical;
        min-height: 40px;
        max-height: 120px;
      }

      .send-button {
        background: #007bff;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        cursor: pointer;
        height: fit-content;
      }

      .send-button:disabled {
        background: #6c757d;
        cursor: not-allowed;
      }

      .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 0.75rem;
        margin: 1rem;
        border-radius: 4px;
        border: 1px solid #f5c6cb;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .close-error {
        background: none;
        border: none;
        font-size: 1.2rem;
        cursor: pointer;
        color: #721c24;
      }

      /* Mobile optimizations */
      @media (max-width: 768px) {
        .chat-container {
          height: 100vh;
          border-radius: 0;
          box-shadow: none;
          max-height: 100vh;
          display: flex;
          flex-direction: column;
          position: relative;
        }

        .chat-header {
          padding: 12px 16px;
        }

        .chat-header h3 {
          font-size: 16px;
        }

        .status-indicator {
          font-size: 11px;
          padding: 3px 6px;
        }

        .chat-messages {
          padding: 12px;
          gap: 12px;
          flex: 1;
          min-height: 0;
          overflow-y: scroll;
          -webkit-overflow-scrolling: touch;
          padding-bottom: 100px; /* Extra space for input */
        }

        .message {
          max-width: 90%;
        }

        .message-content {
          padding: 12px 16px;
          border-radius: 18px;
        }

        .message-text {
          font-size: 14px;
          line-height: 1.4;
        }

        .message-time {
          font-size: 10px;
          margin-top: 4px;
        }

        .chat-input {
          padding: 12px;
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(10px);
          position: fixed;
          bottom: 30px;
          left: 0;
          right: 0;
          border-top: 1px solid #e0e0e0;
          z-index: 1000;
          box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
        }

        .input-container {
          gap: 8px;
        }

        textarea {
          border-radius: 20px;
          padding: 12px 16px;
          font-size: 14px;
          border: 1px solid #e0e0e0;
          background: white;
        }

        .send-button {
          border-radius: 20px;
          padding: 12px 20px;
          font-size: 14px;
          font-weight: 600;
          min-width: 60px;
        }

        .error-message {
          margin: 12px;
          padding: 12px;
          border-radius: 12px;
          font-size: 14px;
        }
      }
    `,
  ],
})
export class ChatComponent implements OnInit, OnDestroy, AfterViewChecked {
  @ViewChild('messagesContainer') private messagesContainer!: ElementRef;

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

  formatTime(timestamp: string): string {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  }
}
