import {
  Component,
  OnInit,
  OnDestroy,
  ViewChild,
  ElementRef,
  AfterViewChecked,
  Output,
  EventEmitter,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  AgentService,
  ChatResponse,
  VideoGenerationResponse,
} from '../../services/agent.service';
import { AuthService } from '../../services/auth.service';
import { SessionHistoryService } from '../../services/session-history.service';
import { Subscription, Observable } from 'rxjs';
import { MatButtonModule } from '@angular/material/button';
import { AI, getImagenModel, ImagenModel } from '@angular/fire/ai';

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
  imports: [CommonModule, FormsModule, MatButtonModule],
  template: `
    <div class="chat-container">
      <div class="mock-controls" *ngIf="isAuthorizedForVideo()">
        <button mat-raised-button color="accent" (click)="toggleMockMode()">
          {{ (mockMode$ | async) ? 'Disable Mock Mode' : 'Enable Mock Mode' }}
        </button>
        <div class="mock-status" *ngIf="mockMode$ | async">
          Mock Mode Enabled
        </div>
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

        <!-- Generated Image Display -->
        <div *ngIf="generatedImageUrl" class="video-result-container">
          <div class="video-result-card">
            <h3>✅ Image Generated Successfully!</h3>
            <img
              [src]="generatedImageUrl"
              alt="Generated Image"
              class="generated-video"
            />
          </div>
        </div>

        <!-- Image and Video Generation UI -->
        <div *ngIf="showGenerateImagePrompt" class="video-generation-container">
          <div class="video-generation-card">
            <h3>🎬 Generate Image and Video</h3>
            <p>
              Ready to create your image and video? Click the buttons below to
              start generation.
            </p>

            <div class="video-actions">
              <button
                (click)="onGenerateImageClick()"
                class="primary-btn"
                [disabled]="isGeneratingImage || isGeneratingVideo"
              >
                {{
                  isGeneratingImage ? '🖼️ Generating...' : '🖼️ Generate Image'
                }}
              </button>
              <button
                (click)="onGenerateVideoClick()"
                class="primary-btn"
                [disabled]="
                  isGeneratingVideo || isGeneratingImage || !generatedImageUrl
                "
              >
                {{
                  isGeneratingVideo ? '🎬 Generating...' : '🎬 Generate Video'
                }}
              </button>
              <button
                (click)="resetImageGeneration()"
                class="secondary-btn"
                [disabled]="isGeneratingImage || isGeneratingVideo"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>

        <!-- Generated Video Display -->
        <div *ngIf="generatedVideoUrl" class="video-result-container">
          <div class="video-result-card">
            <h3>✅ Video Generated Successfully!</h3>
            <video
              [src]="generatedVideoUrl"
              controls
              class="generated-video"
              preload="metadata"
            >
              Your browser does not support the video tag.
            </video>
            <div class="video-actions">
              <a
                [href]="generatedVideoUrl"
                class="download-btn"
                (click)="openVideoInNewTab($event)"
              >
                📥 Download Video
              </a>
              <button (click)="resetVideoGeneration()" class="secondary-btn">
                Generate Another
              </button>
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
        height: 100dvh;
        display: flex;
        flex-direction: column;
        background: #f8f9fa;
      }

      .mock-controls {
        padding: 16px;
        display: flex;
        align-items: center;
        gap: 12px;
        background: white;
        border-bottom: 1px solid #e9ecef;
      }

      .mock-status {
        color: #1976d2;
        font-weight: 500;
        font-size: 14px;
      }

      .messages-container {
        flex: 1;
        overflow-y: auto;
        padding: 20px;
        display: flex;
        flex-direction: column;
        gap: 16px;
        max-height: 60% !important;
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
        flex-shrink: 0;
        bottom: 0;
        position: fixed;
        width: 100%;
      }

      .input-wrapper {
        display: flex;
        gap: 12px;
        align-items: flex-end;
        max-width: 800px;
        margin: 0 auto;
        min-width: 90% !important;
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
        max-width: 74% !important;
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

      @media (min-width: 768px) {
        .input-wrapper {
          min-width: 90% !important;
        }

        .message-input[_ngcontent-ng-c1996228786] {
          max-width: 58% !important;
        }
      }

      /* Video Generation Styles */
      .video-generation-prompt {
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid #dee2e6;
      }

      .generate-video-btn {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 20px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        transition: transform 0.2s;
      }

      .generate-video-btn:hover {
        transform: translateY(-1px);
      }

      .video-generation-container {
        margin: 20px 0;
        display: flex;
        justify-content: center;
      }

      .video-generation-card {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        max-width: 500px;
        width: 100%;
      }

      .video-generation-card h3 {
        margin: 0 0 12px 0;
        color: #495057;
        font-size: 18px;
      }

      .video-generation-card p {
        margin: 0 0 20px 0;
        color: #6c757d;
        font-size: 14px;
      }

      .video-actions {
        display: flex;
        gap: 12px;
        margin-top: 16px;
      }

      .primary-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        transition: transform 0.2s;
      }

      .primary-btn:hover:not(:disabled) {
        transform: translateY(-1px);
      }

      .primary-btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }

      .secondary-btn {
        background: #f8f9fa;
        color: #495057;
        border: 1px solid #dee2e6;
        padding: 12px 24px;
        border-radius: 8px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.2s;
      }

      .secondary-btn:hover {
        background: #e9ecef;
      }

      .api-key-input {
        margin-top: 16px;
      }

      .api-key-input label {
        display: block;
        margin-bottom: 8px;
        font-weight: 500;
        color: #495057;
      }

      .api-key-field {
        width: 100%;
        padding: 12px;
        border: 2px solid #e9ecef;
        border-radius: 8px;
        font-size: 14px;
        margin-bottom: 16px;
        transition: border-color 0.2s;
      }

      .api-key-field:focus {
        outline: none;
        border-color: #667eea;
      }

      .api-key-actions {
        display: flex;
        gap: 12px;
      }

      .video-result-container {
        margin: 20px 0;
        display: flex;
        justify-content: center;
      }

      .video-result-card {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        max-width: 600px;
        width: 100%;
      }

      .video-result-card h3 {
        margin: 0 0 16px 0;
        color: #28a745;
        font-size: 18px;
      }

      .generated-video {
        width: 100%;
        max-width: 100%;
        border-radius: 8px;
        margin-bottom: 16px;
      }

      .download-btn {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        text-decoration: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        transition: transform 0.2s;
        display: inline-block;
      }

      .download-btn:hover {
        transform: translateY(-1px);
      }

      /* Desktop enhancements for video generation */
      @media (min-width: 1200px) {
        .video-generation-card,
        .video-result-card {
          max-width: 600px;
          padding: 32px;
        }

        .video-generation-card h3,
        .video-result-card h3 {
          font-size: 20px;
        }

        .video-generation-card p {
          font-size: 15px;
        }

        .primary-btn,
        .secondary-btn,
        .download-btn {
          padding: 14px 28px;
          font-size: 15px;
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

  // State for VEO video generation flow
  showGeneratePrompt = false;
  showApiKeyInput = false;
  veoApiKey = '';
  isGeneratingVideo = false;
  generatedVideoUrl: string | null = null;

  // State for image generation flow
  showGenerateImagePrompt = false;
  isGeneratingImage = false;
  generatedImageUrl: string | null = null;
  imagePrompt: string | null = null;

  private currentOperationName: string | null = null;
  private pollingInterval: any = null;

  private subscriptions: Subscription[] = [];

  mockMode$: Observable<boolean>;
  private ai = inject(AI);
  private imagenModel!: ImagenModel;

  constructor(
    private agentService: AgentService,
    private authService: AuthService,
    private sessionHistoryService: SessionHistoryService
  ) {
    this.mockMode$ = this.agentService.mockMode$;
  }

  ngOnInit() {
    this.imagenModel = getImagenModel(this.ai, {
      model: 'imagen-3.0-generate-002',
    });

    // Only get mock status if user is authorized
    if (this.isAuthorizedForVideo()) {
      this.agentService.getMockStatus().subscribe();
    }

    this.addSystemMessage(
      "Welcome to 82ndrop! Describe your video idea and I'll help you create engaging prompts."
    );

    // Subscribe to Firebase messages for session history
    this.subscriptions.push(
      this.sessionHistoryService.messages$.subscribe((firebaseMessages) => {
        console.log(
          '🔄 Chat received Firebase messages:',
          firebaseMessages.length
        );

        if (firebaseMessages.length > 0) {
          // Clear current messages and load from Firebase
          this.messages = [
            {
              type: 'system',
              content: 'Session restored. Continue your conversation below.',
              timestamp: new Date().toISOString(),
            },
          ];

          // Convert Firebase messages to chat messages
          firebaseMessages.forEach((fbMsg) => {
            this.messages.push({
              type: fbMsg.type as 'user' | 'agent' | 'system' | 'progress',
              content: fbMsg.content,
              timestamp: new Date(fbMsg.timestamp).toISOString(),
            });
          });

          console.log(
            `✅ Chat loaded ${this.messages.length - 1} messages from Firebase`
          );
          this.shouldScrollToBottom = true;
        } else {
          // If no messages, show only the welcome message (for new sessions)
          console.log('📭 No Firebase messages, keeping welcome message only');
        }
      })
    );
  }

  ngOnDestroy() {
    // Clean up polling when component is destroyed
    this.stopPolling();
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

  prettifyAgentName(name: string): string {
    return name.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
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
            const workflowSteps =
              this.messages[progressIndex].workflowSteps || [];
            if (update.content && update.content.parts) {
              const part = update.content.parts[0];
              if (part.functionCall) {
                const step = `Calling: ${part.functionCall.name}`;
                if (workflowSteps[workflowSteps.length - 1] !== step) {
                  workflowSteps.push(step);
                }
              }
            } else if (update.author) {
              const step = `Running: ${this.prettifyAgentName(update.author)}`;
              if (workflowSteps[workflowSteps.length - 1] !== step) {
                workflowSteps.push(step);
              }
            }
            this.messages[progressIndex].workflowSteps = workflowSteps;
            this.shouldScrollToBottom = true;
          }
        }
      );

      // Remove progress message and add final response
      const progressIndex = this.messages.findIndex(
        (m) => m.type === 'progress'
      );
      if (progressIndex >= 0) {
        this.messages.splice(progressIndex, 1);
      }
      this.addAgentMessage(response.response, response.timestamp);

      // Check if response contains JSON and emit it
      try {
        const jsonMatch = response.response.match(/```json\s*([\s\S]*?)\s*```/);
        if (jsonMatch) {
          const jsonContent = jsonMatch[1];
          const parsedJson = JSON.parse(jsonContent);
          this.promptGenerated.emit(parsedJson);
          if (this.isAuthorizedForVideo()) {
            this.imagePrompt = parsedJson.prompt;
            this.showGenerateImagePrompt = true;
          }
        } else if (
          response.response.includes(
            'Generate a single, cohesive vertical short-form video'
          )
        ) {
          if (this.isAuthorizedForVideo()) {
            this.imagePrompt = response.response;
            this.showGenerateImagePrompt = true;
          }
        }
      } catch (e) {
        console.log(
          'Response does not contain valid JSON, continuing normally'
        );
      }
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

  // Call this after displaying the Master Prompt
  isAuthorizedForVideo(): boolean {
    const user = this.authService.getCurrentUser();
    return user?.email === 'turnono@gmail.com';
  }

  // Handle image generation
  async onGenerateImageClick(): Promise<void> {
    if (!this.isAuthorizedForVideo()) {
      this.addAgentMessage(
        'Sorry, you are not authorized to generate images.',
        new Date().toISOString()
      );
      return;
    }
    if (!this.imagePrompt) return;
    this.isGeneratingImage = true;
    this.generatedImageUrl = null;
    try {
      const result = await this.imagenModel.generateImages(this.imagePrompt);
      if (result.filteredReason) {
        console.log(result.filteredReason);
      }
      if (result.images?.length === 0) {
        throw new Error('No images in the response.');
      }
      const image = result.images[0];
      const rawBase64 = image.bytesBase64Encoded;
      const mimeType = image.mimeType;
      this.generatedImageUrl = `data:${mimeType};base64,${rawBase64}`;
    } catch (e) {
      console.error(e);
    } finally {
      this.isGeneratingImage = false;
    }
  }

  resetImageGeneration() {
    this.showGenerateImagePrompt = false;
    this.isGeneratingImage = false;
    this.generatedImageUrl = null;
    this.imagePrompt = null;
  }

  // Handle video generation
  async onGenerateVideoClick(): Promise<void> {
    if (!this.isAuthorizedForVideo()) {
      this.addAgentMessage(
        'Sorry, you are not authorized to generate videos.',
        new Date().toISOString()
      );
      return;
    }

    this.isGeneratingVideo = true;
    this.generatedVideoUrl = null;

    try {
      // Get the last agent message as the video prompt
      const lastAgentMessage = this.messages
        .filter((m) => m.type === 'agent')
        .pop();

      if (!lastAgentMessage) {
        throw new Error(
          'No video prompt available. Please generate a prompt first.'
        );
      }

      // Call the backend to generate video
      const response = await this.agentService.generateVideo(
        lastAgentMessage.content
      );

      // If status is in_progress, start polling
      if (response.status === 'in_progress') {
        this.addAgentMessage(
          '🎬 Video generation has started. Please wait while we process your request...',
          new Date().toISOString()
        );

        // Store operation name and start polling
        this.startPolling(response.operation_name);
        return;
      }

      this.isGeneratingVideo = false;

      // Only try to access video URL if status is completed
      if (response.status === 'completed') {
        await this.handleCompletedVideo(response);
      } else if (response.status === 'error') {
        throw new Error(response.error || 'Video generation failed');
      }
    } catch (error) {
      console.error('Error generating video:', error);
      this.isGeneratingVideo = false;
      this.generatedVideoUrl = null;

      // Show error message to user
      this.addAgentMessage(
        `❌ Video generation failed: ${
          error instanceof Error ? error.message : 'Unknown error'
        }`,
        new Date().toISOString()
      );
    }
  }

  private startPolling(operationName: string): void {
    if (this.pollingInterval) {
      this.stopPolling();
    }

    this.currentOperationName = operationName;
    this.pollingInterval = setInterval(async () => {
      try {
        const status = await this.agentService.checkVideoStatus(operationName);

        if (status.status === 'completed' && status.video_uri) {
          // Stop polling when we get a successful completion
          this.stopPolling();
          this.handleCompletedVideo(status);
        } else if (status.status === 'error' || status.error) {
          // Stop polling on error
          this.stopPolling();
          this.handleVideoError(status.error || 'Video generation failed');
        }
        // Continue polling only if status is 'in_progress'
      } catch (error) {
        // Stop polling on error (like 404)
        this.stopPolling();
        console.error('Error checking video status:', error);
        this.handleVideoError('Failed to check video status');
      }
    }, 5000); // Poll every 5 seconds
  }

  private stopPolling(): void {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
    this.currentOperationName = null;
  }

  private handleCompletedVideo(response: any): void {
    const videoUrl = this.agentService.transformGcsUrl(response.video_uri);
    console.log('Video generated successfully:', videoUrl);
    this.isGeneratingVideo = false;
    this.generatedVideoUrl = videoUrl;
    this.addAgentMessage(
      `🎥 Video generated successfully! You can now view or download the video.`,
      new Date().toISOString()
    );
  }

  private handleVideoError(error: string): void {
    console.error('Video generation error:', error);
    this.isGeneratingVideo = false;
    this.addAgentMessage(
      `❌ Failed to generate video: ${error}`,
      new Date().toISOString()
    );
  }

  resetVideoGeneration() {
    try {
      // Cancel any ongoing video generation processes
      if (this.isGeneratingVideo && this.currentOperationName) {
        console.log('Cancelling ongoing video generation...');
        this.agentService
          .cancelVideoGeneration(this.currentOperationName)
          .catch((error) =>
            console.error('Error cancelling video generation:', error)
          );
      }

      // Stop polling
      this.stopPolling();

      // Reset state variables
      this.showGeneratePrompt = false;
      this.showApiKeyInput = false;
      this.veoApiKey = '';
      this.isGeneratingVideo = false;
      this.generatedVideoUrl = null;

      console.log('Video generation state reset successfully');
    } catch (error) {
      console.error('Error during video generation reset:', error);
      // Ensure critical state is reset even if there's an error
      this.stopPolling();
      this.isGeneratingVideo = false;
      this.generatedVideoUrl = null;
    }
  }

  openVideoInNewTab(event: MouseEvent): void {
    event.preventDefault();
    if (this.generatedVideoUrl) {
      window.open(this.generatedVideoUrl, '_blank');
    }
  }

  async toggleMockMode() {
    if (this.isAuthorizedForVideo()) {
      try {
        await this.agentService.toggleMockMode().toPromise();
      } catch (error) {
        console.error('Error toggling mock mode:', error);
      }
    }
  }
}
