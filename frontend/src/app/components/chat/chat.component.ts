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
  type: 'user' | 'agent' | 'system' | 'progress';
  content: string;
  timestamp: string;
  loading?: boolean;
  workflowSteps?: string[];
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="chat-container">
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

            <!-- Workflow progress indicator -->
            <div
              *ngIf="message.type === 'progress' && message.workflowSteps"
              class="workflow-steps"
            >
              <div
                *ngFor="let step of message.workflowSteps"
                class="workflow-step"
              >
                {{ step }}
              </div>
            </div>

            <div class="message-timestamp">
              {{ formatTimestamp(message.timestamp) }}
            </div>
          </div>
        </div>
      </div>

      <div class="input-container">
        <div class="input-wrapper">
          <input
            #messageInput
            type="text"
            [(ngModel)]="currentMessage"
            (keyup.enter)="sendMessage()"
            placeholder="What kind of video do you want to create?"
            class="message-input"
          />
          <button
            (click)="sendMessage()"
            class="send-button"
            [disabled]="isLoading || !currentMessage.trim()"
          >
            <span class="send-icon">→</span>
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .chat-container {
        height: 100%;
        display: flex;
        flex-direction: column;
        background: #f8f9fa;
      }

      .messages-container {
        flex: 1;
        overflow-y: auto;
        padding: 20px;
        display: flex;
        flex-direction: column;
        gap: 16px;
      }

      .message {
        max-width: 80%;
        word-wrap: break-word;
      }

      .message.user {
        align-self: flex-end;
      }

      .message.assistant {
        align-self: flex-start;
      }

      .message.progress {
        align-self: flex-start;
        max-width: 90%;
      }

      .message-content {
        padding: 12px 16px;
        border-radius: 18px;
        position: relative;
      }

      .message.user .message-content {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
      }

      .message.assistant .message-content {
        background: white;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      }

      .message.progress .message-content {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-left: 4px solid #667eea;
      }

      .message-text {
        margin-bottom: 4px;
        -webkit-user-select: text;
        -moz-user-select: text;
        -ms-user-select: text;
        user-select: text;
      }

      .message-timestamp {
        font-size: 11px;
        opacity: 0.7;
      }

      .input-container {
        padding: 20px;
        background: white;
        border-top: 1px solid #e9ecef;
      }

      .input-wrapper {
        display: flex;
        gap: 12px;
        align-items: flex-end;
        max-width: 800px;
        margin: 0 auto;
      }

      .message-input {
        flex: 1;
        padding: 12px 16px;
        border: 2px solid #e9ecef;
        border-radius: 20px;
        outline: none;
        font-size: 16px;
        resize: none;
        transition: border-color 0.2s;
      }

      .message-input:focus {
        border-color: #667eea;
      }

      .send-button {
        padding: 12px 24px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 20px;
        cursor: pointer;
        transition: transform 0.2s;
        font-size: 14px;
        font-weight: 500;
      }

      .send-button:hover:not(:disabled) {
        transform: translateY(-1px);
      }

      .send-button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      .send-icon {
        font-size: 16px;
      }

      .workflow-steps {
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px solid #dee2e6;
      }

      .workflow-step {
        font-size: 12px;
        color: #6c757d;
        margin: 2px 0;
        padding: 2px 8px;
        background: rgba(102, 126, 234, 0.1);
        border-radius: 12px;
        display: inline-block;
        margin-right: 4px;
        margin-bottom: 4px;
      }

      .json-container {
        margin: 12px 0;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        overflow: hidden;
        background: #f8f9fa;
        -webkit-user-select: text;
        -moz-user-select: text;
        -ms-user-select: text;
        user-select: text;
      }

      .json-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 12px;
        background: #e9ecef;
        border-bottom: 1px solid #dee2e6;
      }

      .json-label {
        font-weight: 600;
        color: #495057;
        font-size: 14px;
      }

      .copy-json-btn {
        padding: 4px 8px;
        background: #007bff;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 11px;
        transition: all 0.2s;
      }

      .copy-json-btn:hover {
        background: #0056b3;
        transform: translateY(-1px);
      }

      .json-block {
        background: white;
        padding: 12px;
        margin: 0;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        font-size: 12px;
        line-height: 1.4;
        white-space: pre-wrap;
        overflow-x: auto;
        -webkit-user-select: text;
        -moz-user-select: text;
        -ms-user-select: text;
        user-select: text;
      }

      /* Desktop enhancements for chat */
      @media (min-width: 1200px) {
        .chat-container {
          background: #fafbfc;
        }

        .messages-container {
          padding: 32px 48px;
          gap: 24px;
        }

        .message {
          max-width: 70%;
        }

        .message-content {
          padding: 16px 20px;
          border-radius: 20px;
        }

        .message.assistant .message-content {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        }

        .message-text {
          font-size: 15px;
          line-height: 1.6;
        }

        .message-timestamp {
          font-size: 12px;
        }

        .input-container {
          padding: 32px 48px;
          background: white;
          border-top: 1px solid #e9ecef;
        }

        .input-wrapper {
          max-width: 1000px;
          gap: 16px;
        }

        .message-input {
          padding: 16px 20px;
          font-size: 16px;
          border-radius: 24px;
          border-width: 2px;
        }

        .send-button {
          padding: 16px 28px;
          border-radius: 24px;
          font-size: 15px;
        }

        .workflow-step {
          font-size: 13px;
          padding: 4px 12px;
          border-radius: 14px;
        }

        .json-container {
          margin: 16px 0;
          border-radius: 12px;
        }

        .json-header {
          padding: 12px 16px;
        }

        .json-label {
          font-size: 15px;
        }

        .copy-json-btn {
          padding: 6px 12px;
          font-size: 12px;
          border-radius: 6px;
        }

        .json-block {
          padding: 16px;
          font-size: 13px;
          line-height: 1.5;
        }
      }

      @media (min-width: 1400px) {
        .messages-container {
          padding: 40px 64px;
          gap: 28px;
        }

        .message-content {
          padding: 18px 24px;
          border-radius: 22px;
        }

        .message-text {
          font-size: 16px;
        }

        .input-container {
          padding: 40px 64px;
        }

        .message-input {
          padding: 18px 24px;
          font-size: 17px;
          border-radius: 26px;
        }

        .send-button {
          padding: 18px 32px;
          border-radius: 26px;
          font-size: 16px;
        }

        .json-block {
          padding: 20px;
          font-size: 14px;
        }
      }
    `,
  ],
})
export class ChatComponent implements OnInit, OnDestroy, AfterViewChecked {
  @ViewChild('messagesContainer') messagesContainer!: ElementRef;
  @Output() promptGenerated = new EventEmitter<any>();
  @Output() backToMenu = new EventEmitter<void>();

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

  private addProgressMessage(content: string, workflowSteps: string[] = []) {
    this.messages.push({
      type: 'progress',
      content,
      timestamp: new Date().toISOString(),
      workflowSteps,
    });
    this.shouldScrollToBottom = true;
  }

  async sendMessage() {
    if (!this.currentMessage.trim() || this.isLoading) {
      return;
    }

    const userMessage = this.currentMessage.trim();
    this.currentMessage = '';
    this.isLoading = true;

    // Add user message
    this.addUserMessage(userMessage);

    // Add progress message that will be updated in real-time
    const progressMessage: ChatMessage = {
      type: 'progress',
      content: 'Starting analysis...',
      timestamp: new Date().toISOString(),
      workflowSteps: [],
    };
    this.messages.push(progressMessage);
    this.shouldScrollToBottom = true;

    try {
      // Use SSE for real-time updates
      const response = await this.agentService.sendMessageWithSSE(
        userMessage,
        (update) => {
          // Update progress message in real-time
          const progressIndex = this.messages.length - 1;
          if (this.messages[progressIndex]?.type === 'progress') {
            if (update.type === 'workflow_step') {
              this.messages[progressIndex].content = update.message;
              this.messages[progressIndex].workflowSteps = update.agents;
            } else if (update.type === 'final_response') {
              // Remove progress message and add final response
              this.messages.splice(progressIndex, 1);
              this.addAgentMessage(update.message, update.timestamp);

              // Check if response contains JSON and emit it
              try {
                const jsonMatch = update.message.match(
                  /```json\s*([\s\S]*?)\s*```/
                );
                if (jsonMatch) {
                  const jsonContent = jsonMatch[1];
                  const parsedJson = JSON.parse(jsonContent);
                  this.promptGenerated.emit(parsedJson);
                }
              } catch (e) {
                console.log(
                  'Response does not contain valid JSON, continuing normally'
                );
              }
            }
            this.shouldScrollToBottom = true;
          }
        }
      );

      console.log('SSE Response received:', response);
    } catch (error) {
      console.error('Error sending message:', error);

      // Remove progress message and show error
      const progressIndex = this.messages.findIndex(
        (m) => m.type === 'progress'
      );
      if (progressIndex >= 0) {
        this.messages.splice(progressIndex, 1);
      }

      this.addAgentMessage(
        'Sorry, I encountered an error while processing your request. Please try again.',
        new Date().toISOString()
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
      .replace(/```json\n([\s\S]*?)\n```/g, (match, jsonContent) => {
        return `<div class="json-container">
          <div class="json-header">
            <span class="json-label">📋 Video Composition JSON</span>
            <button class="copy-json-btn" onclick="
              navigator.clipboard.writeText(\`${jsonContent.replace(
                /`/g,
                '\\`'
              )}\`).then(() => {
                this.textContent = '✅ Copied!';
                this.style.background = '#28a745';
                setTimeout(() => {
                  this.textContent = '📋 Copy';
                  this.style.background = '#007bff';
                }, 2000);
              }).catch(() => {
                this.textContent = '❌ Failed';
                setTimeout(() => this.textContent = '📋 Copy', 2000);
              })
            ">📋 Copy</button>
          </div>
          <pre class="json-block">${jsonContent}</pre>
        </div>`;
      }) // JSON blocks with copy button
      .replace(/`(.*?)`/g, '<code>$1</code>'); // Inline code
  }
}
