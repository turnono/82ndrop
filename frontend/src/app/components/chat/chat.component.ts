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
      <div class="chat-header">
        <h2>82ndrop Video Prompt Generator</h2>
        <button (click)="startNewSession()" class="new-session-btn">
          New Session
        </button>
      </div>

      <div class="messages-container" #messagesContainer>
        <div
          *ngFor="let message of messages"
          class="message"
          [ngClass]="message.type"
        >
          <div class="message-content">
            <div
              class="message-text"
              [innerHTML]="formatMessageText(message.content)"
            ></div>
            <div class="message-timestamp">
              {{ formatTimestamp(message.timestamp) }}
            </div>
            <div *ngIf="message.loading" class="loading-indicator">
              <div class="spinner"></div>
              <span>Generating response...</span>
            </div>
          </div>
        </div>
      </div>

      <div class="input-container">
        <div class="input-wrapper">
          <textarea
            [(ngModel)]="currentMessage"
            (keydown)="onEnterKey($event)"
            placeholder="Describe your video idea..."
            class="message-input"
            rows="2"
            [disabled]="isLoading"
          ></textarea>
          <button
            (click)="sendMessage()"
            [disabled]="!currentMessage.trim() || isLoading"
            class="send-button"
          >
            <span *ngIf="!isLoading">Send</span>
            <span *ngIf="isLoading" class="loading">
              <div class="spinner"></div>
            </span>
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .chat-container {
        display: flex;
        flex-direction: column;
        height: 100vh;
        max-width: 800px;
        margin: 0 auto;
        background: #f8f9fa;
      }

      .chat-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem;
        background: white;
        border-bottom: 1px solid #e9ecef;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      }

      .chat-header h2 {
        margin: 0;
        color: #333;
        font-size: 1.5rem;
      }

      .new-session-btn {
        padding: 0.5rem 1rem;
        background: #007bff;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.9rem;
      }

      .new-session-btn:hover {
        background: #0056b3;
      }

      .messages-container {
        flex: 1;
        overflow-y: auto;
        padding: 1rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
      }

      .message {
        display: flex;
        max-width: 80%;
      }

      .message.user {
        align-self: flex-end;
      }

      .message.agent {
        align-self: flex-start;
      }

      .message.system {
        align-self: center;
        max-width: 90%;
      }

      .message-content {
        padding: 0.75rem 1rem;
        border-radius: 12px;
        position: relative;
      }

      .user .message-content {
        background: #007bff;
        color: white;
      }

      .agent .message-content {
        background: white;
        border: 1px solid #e9ecef;
        color: #333;
      }

      .system .message-content {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        color: #6c757d;
        text-align: center;
      }

      .message-text {
        line-height: 1.4;
        word-wrap: break-word;
      }

      .message-timestamp {
        font-size: 0.75rem;
        opacity: 0.7;
        margin-top: 0.25rem;
      }

      .loading-indicator {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-top: 0.5rem;
        font-size: 0.9rem;
        opacity: 0.8;
      }

      .input-container {
        padding: 1rem;
        background: white;
        border-top: 1px solid #e9ecef;
      }

      .input-wrapper {
        display: flex;
        gap: 0.5rem;
        align-items: flex-end;
      }

      .message-input {
        flex: 1;
        padding: 0.75rem;
        border: 1px solid #ced4da;
        border-radius: 8px;
        resize: vertical;
        min-height: 44px;
        max-height: 120px;
        font-family: inherit;
        font-size: 1rem;
      }

      .message-input:focus {
        outline: none;
        border-color: #007bff;
        box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
      }

      .send-button {
        padding: 0.75rem 1.5rem;
        background: #007bff;
        color: white;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-size: 1rem;
        min-width: 80px;
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

      /* Enhanced formatting for agent responses */
      .message-text :global(strong) {
        font-weight: bold;
      }

      .message-text :global(em) {
        font-style: italic;
      }

      .message-text :global(code) {
        background: rgba(0, 0, 0, 0.1);
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
      }

      .message-text :global(.json-block) {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 4px;
        padding: 1rem;
        margin: 0.5rem 0;
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
        white-space: pre-wrap;
        overflow-x: auto;
      }

      .agent .message-text :global(code) {
        background: #f8f9fa;
      }

      .user .message-text :global(code) {
        background: rgba(255, 255, 255, 0.2);
      }
    `,
  ],
})
export class ChatComponent implements OnInit, OnDestroy, AfterViewChecked {
  @ViewChild('messagesContainer') messagesContainer!: ElementRef;
  @Output() promptGenerated = new EventEmitter<any>();

  messages: ChatMessage[] = [];
  currentMessage = '';
  isLoading = false;
  private shouldScrollToBottom = false;

  private subscriptions: Subscription[] = [];

  constructor(
    private agentService: AgentService,
    private authService: AuthService
  ) {}

  ngOnInit() {
    this.addSystemMessage(
      "Welcome to 82ndrop! Describe your video idea and I'll help you create engaging prompts."
    );
  }

  ngOnDestroy() {
    this.subscriptions.forEach((sub) => sub.unsubscribe());
  }

  ngAfterViewChecked() {
    if (this.shouldScrollToBottom) {
      this.scrollToBottom();
      this.shouldScrollToBottom = false;
    }
  }

  private scrollToBottom(): void {
    try {
      this.messagesContainer.nativeElement.scrollTop =
        this.messagesContainer.nativeElement.scrollHeight;
    } catch (err) {
      console.error('Error scrolling to bottom:', err);
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

  async sendMessage() {
    if (!this.currentMessage.trim() || this.isLoading) {
      return;
    }

    const userMessage = this.currentMessage.trim();
    this.addUserMessage(userMessage);
    this.currentMessage = '';
    this.isLoading = true;

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
        userMessage
      );

      // Remove loading message
      this.messages = this.messages.filter((m) => !m.loading);

      // Add agent response
      this.addAgentMessage(response.response, response.timestamp);

      // Check if response contains JSON prompts and emit them
      try {
        const jsonMatch = response.response.match(/```json\n([\s\S]*?)\n```/);
        if (jsonMatch) {
          const promptData = JSON.parse(jsonMatch[1]);
          this.promptGenerated.emit(promptData);
        }
      } catch (e) {
        // Not a JSON response, that's fine
      }
    } catch (error) {
      console.error('Error sending message:', error);

      // Remove loading message
      this.messages = this.messages.filter((m) => !m.loading);

      // Add error message
      this.addSystemMessage(
        `❌ Error: ${
          error instanceof Error
            ? error.message
            : 'Failed to send message. Please try again.'
        }`
      );
    } finally {
      this.isLoading = false;
    }
  }

  onEnterKey(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  startNewSession() {
    this.agentService.startNewSession();
    this.messages = [];
    this.addSystemMessage(
      'New session started. What video idea would you like to explore?'
    );
  }

  formatTimestamp(timestamp: string): string {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  formatMessageText(text: string): string {
    // Basic markdown formatting and line breaks
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
      .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic
      .replace(/\n/g, '<br>') // Line breaks
      .replace(/```json\n([\s\S]*?)\n```/g, '<pre class="json-block">$1</pre>') // JSON blocks
      .replace(/`(.*?)`/g, '<code>$1</code>'); // Inline code
  }
}
