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
import { SessionHistoryService } from '../../services/session-history.service';
import { Subscription } from 'rxjs';

interface ChatMessage {
  type: 'user' | 'agent' | 'system' | 'progress' | 'video_loading' | 'video';
  content: string;
  timestamp: string;
  loading?: boolean;
  workflowSteps?: string[];
  jobId?: string;
  videoUrl?: string;
  showConfirmation?: boolean;
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

            <!-- Loading Indicator -->
            <div *ngIf="message.loading" class="spinner"></div>

            <!-- Video Loading Status -->
            <div *ngIf="message.type === 'video_loading'" class="video-loading">
              <div class="loading-spinner"></div>
              <div class="loading-text">{{ message.content }}</div>
              <div *ngIf="message.jobId" class="job-id">
                Job ID: {{ message.jobId }}
              </div>
            </div>

            <!-- Video Player -->
            <div
              *ngIf="message.type === 'video' && message.videoUrl"
              class="video-player-container"
            >
              <div class="video-header">
                <span class="video-title">{{ message.content }}</span>
                <button
                  class="download-video-btn"
                  (click)="
                    downloadVideo(message.videoUrl!, message.jobId || 'video')
                  "
                  title="Download Video"
                >
                  📥 Download
                </button>
              </div>
              <video controls [src]="message.videoUrl" preload="metadata">
                <source [src]="message.videoUrl" type="video/mp4" />
                Your browser does not support the video tag.
              </video>
              <div class="video-info">
                <span *ngIf="message.jobId" class="job-id"
                  >Job ID: {{ message.jobId }}</span
                >
                <span class="video-timestamp">{{
                  formatTimestamp(message.timestamp)
                }}</span>
              </div>
            </div>

            <!-- Confirmation Button -->
            <div
              *ngIf="message.showConfirmation"
              class="confirmation-container"
            >
              <button
                (click)="confirmGeneration(message.content)"
                class="confirm-button"
              >
                Generate Video
              </button>
            </div>

            <div class="message-timestamp">
              {{ formatTimestamp(message.timestamp) }}
            </div>
          </div>
        </div>
      </div>

      <div class="input-container">
        <div class="input-wrapper">
          <textarea
            #messageInput
            [(ngModel)]="currentMessage"
            (keyup.ctrl.enter)="sendMessage()"
            (keyup.meta.enter)="sendMessage()"
            placeholder="Describe your video idea in detail. Use Ctrl+Enter (Cmd+Enter on Mac) to send, or click the send button."
            class="message-input"
            rows="3"
          ></textarea>
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
        border-radius: 16px;
        outline: none;
        font-size: 16px;
        font-family: inherit;
        line-height: 1.4;
        resize: vertical;
        min-height: 48px;
        max-height: 120px;
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

        .video-loading-indicator {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 10px;
        }

        .spinner {
          border: 4px solid rgba(0, 0, 0, 0.1);
          width: 36px;
          height: 36px;
          border-radius: 50%;
          border-left-color: #667eea;
          animation: spin 1s ease infinite;
        }

        @keyframes spin {
          0% {
            transform: rotate(0deg);
          }
          100% {
            transform: rotate(360deg);
          }
        }

        .video-player-container video {
          max-width: 100%;
          border-radius: 12px;
        }

        .confirmation-container {
          margin-top: 12px;
        }

        .confirm-button {
          padding: 10px 20px;
          background: #28a745;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          transition: background-color 0.2s;
        }

        .confirm-button:hover {
          background: #218838;
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

      /* Enhanced Video Generation Styles */
      .video-loading {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 18px;
        margin: 10px 0;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
      }

      .loading-spinner {
        width: 40px;
        height: 40px;
        border: 4px solid rgba(255, 255, 255, 0.3);
        border-top: 4px solid white;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 15px;
      }

      .loading-text {
        font-weight: 600;
        margin-bottom: 8px;
        text-align: center;
      }

      .job-id {
        font-size: 11px;
        opacity: 0.8;
        font-family: monospace;
        background: rgba(255, 255, 255, 0.2);
        padding: 4px 8px;
        border-radius: 4px;
      }

      .video-player-container {
        border: 2px solid #28a745;
        border-radius: 18px;
        overflow: hidden;
        background: white;
        box-shadow: 0 6px 20px rgba(40, 167, 69, 0.2);
        margin: 10px 0;
      }

      .video-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
      }

      .video-title {
        font-weight: 600;
        font-size: 14px;
      }

      .download-video-btn {
        background: rgba(255, 255, 255, 0.2);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 6px 12px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 11px;
        transition: all 0.2s;
        backdrop-filter: blur(10px);
      }

      .download-video-btn:hover {
        background: rgba(255, 255, 255, 0.3);
        transform: translateY(-1px);
      }

      .video-player-container video {
        width: 100%;
        max-height: 400px;
        display: block;
        background: #000;
      }

      .video-info {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 16px;
        background: #f8f9fa;
        font-size: 11px;
      }

      .video-timestamp {
        color: #6c757d;
        font-weight: 500;
      }

      /* Message type specific styling */
      .message.video_loading .message-content {
        background: transparent;
        border: none;
        padding: 0;
        box-shadow: none;
      }

      .message.video .message-content {
        background: transparent;
        border: none;
        padding: 0;
        box-shadow: none;
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

  private subscriptions: Array<Subscription | (() => void)> = [];

  constructor(
    private agentService: AgentService,
    private authService: AuthService,
    private sessionHistoryService: SessionHistoryService
  ) {}

  ngOnInit() {
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
    this.subscriptions.forEach((sub) => {
      if (typeof sub === 'function') {
        sub(); // For unsubscribe functions
      } else {
        sub.unsubscribe(); // For RxJS subscriptions
      }
    });
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

    this.addUserMessage(userMessage);

    const agentMessage: ChatMessage = {
      type: 'agent',
      content: '',
      timestamp: new Date().toISOString(),
      loading: true,
    };
    this.messages.push(agentMessage);
    this.shouldScrollToBottom = true;

    const sseSubscription = this.agentService.sendMessageWithSSE(
      userMessage,
      (update) => {
        // Append the content of the update to the agent message
        if (update.content) {
          agentMessage.content += update.content;
        }
        if (update.type === 'tool_code') {
          // You can add logic here to display tool calls if you want
        }
        this.shouldScrollToBottom = true;
      },
      (finalResponse) => {
        agentMessage.loading = false;

        // Check if the response contains a video generation job ID
        const jobIdMatch = agentMessage.content.match(
          /Job ID is: ([a-f0-9-]+)/i
        );
        if (jobIdMatch) {
          const jobId = jobIdMatch[1];
          console.log('🎬 Video generation job detected:', jobId);

          // Basic content safety check
          if (this.checkContentSafety(agentMessage.content)) {
            // Add video loading message
            this.addVideoLoadingMessage(jobId);

            // Start tracking the video job
            this.trackVideoJob(jobId);
          } else {
            console.warn('⚠️ Content safety check failed for job:', jobId);
            this.addSystemMessage(
              '⚠️ Video generation blocked: Content may violate our safety guidelines. Please try a different prompt.'
            );
          }
        }

        // Check if the response is a prompt that needs confirmation
        if (agentMessage.content.includes('Shall I proceed')) {
          agentMessage.showConfirmation = true;
        }

        this.isLoading = false;
        sseSubscription(); // Unsubscribe
      },
      (error) => {
        agentMessage.content = 'Sorry, an error occurred.';
        agentMessage.loading = false;
        this.isLoading = false;
        console.error('SSE Error:', error);
        sseSubscription(); // Unsubscribe
      }
    );
    // Store the unsubscribe function directly
    this.subscriptions.push(sseSubscription);
  }

  confirmGeneration(prompt: string) {
    // When the user confirms, we send a new message to the agent
    // with the original prompt to maintain context.
    const confirmationMessage = `Yes, please proceed with generating the video for the following prompt:\n\n${prompt}`;
    this.currentMessage = confirmationMessage;
    this.sendMessage();
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

  // --- Video Generation Methods ---

  private addVideoLoadingMessage(jobId: string) {
    const loadingMessage: ChatMessage = {
      type: 'video_loading',
      content: '🎬 Generating your video... This may take a few minutes.',
      timestamp: new Date().toISOString(),
      jobId: jobId,
      loading: true,
    };

    this.messages.push(loadingMessage);
    this.shouldScrollToBottom = true;
  }

  private trackVideoJob(jobId: string) {
    console.log('📺 Starting video job tracking for:', jobId);

    // Subscribe to Firebase real-time updates for this job
    const jobSubscription = this.sessionHistoryService
      .listenForVideoJob(jobId)
      .subscribe({
        next: (jobData) => {
          console.log('📹 Video job update received:', jobData);
          this.handleVideoJobUpdate(jobId, jobData);
        },
        error: (error) => {
          console.error('❌ Video job tracking error:', error);
          this.handleVideoJobError(jobId, error);
        },
        complete: () => {
          console.log('✅ Video job tracking completed for:', jobId);
        },
      });

    this.subscriptions.push(jobSubscription);
  }

  private handleVideoJobUpdate(jobId: string, jobData: any) {
    // Find the loading message for this job
    const loadingMessageIndex = this.messages.findIndex(
      (msg) => msg.jobId === jobId && msg.type === 'video_loading'
    );

    if (loadingMessageIndex === -1) {
      console.warn('⚠️ Could not find loading message for job:', jobId);
      return;
    }

    const loadingMessage = this.messages[loadingMessageIndex];

    switch (jobData.status) {
      case 'pending':
        loadingMessage.content = '⏳ Video generation queued...';
        break;

      case 'processing':
        loadingMessage.content = '🎬 Creating your video... Please wait.';
        break;

      case 'complete':
        // Replace loading message with video message
        this.messages[loadingMessageIndex] = {
          type: 'video',
          content: '🎉 Your video is ready!',
          timestamp: new Date().toISOString(),
          jobId: jobId,
          videoUrl: jobData.videoUrl || jobData.video_url,
        };
        break;

      case 'failed':
        this.messages[loadingMessageIndex] = {
          type: 'system',
          content: `❌ Video generation failed: ${
            jobData.error || 'Unknown error'
          }`,
          timestamp: new Date().toISOString(),
        };
        break;

      default:
        console.log('🔄 Job status update:', jobData.status);
        loadingMessage.content = `🔄 Status: ${jobData.status}`;
    }

    this.shouldScrollToBottom = true;
  }

  private handleVideoJobError(jobId: string, error: any) {
    // Find and update the loading message
    const loadingMessageIndex = this.messages.findIndex(
      (msg) => msg.jobId === jobId && msg.type === 'video_loading'
    );

    if (loadingMessageIndex !== -1) {
      this.messages[loadingMessageIndex] = {
        type: 'system',
        content:
          '❌ Unable to track video generation. Please check back later.',
        timestamp: new Date().toISOString(),
      };
      this.shouldScrollToBottom = true;
    }
  }

  downloadVideo(videoUrl: string, filename: string) {
    try {
      const link = document.createElement('a');
      link.href = videoUrl;
      link.download = `82ndrop-${filename}.mp4`;
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      console.log('📥 Video download initiated');
    } catch (error) {
      console.error('❌ Video download failed:', error);
      // Fallback: open in new tab
      window.open(videoUrl, '_blank');
    }
  }

  private checkContentSafety(content: string): boolean {
    // Basic content safety checks
    const lowercaseContent = content.toLowerCase();

    // List of prohibited keywords (this should be much more comprehensive in production)
    const prohibitedKeywords = [
      'violence',
      'hate',
      'harassment',
      'bullying',
      'abuse',
      'explicit',
      'nsfw',
      'adult',
      'sexual',
      'inappropriate',
      'harmful',
      'dangerous',
      'illegal',
      'weapon',
      'drug',
    ];

    // Check for prohibited content
    for (const keyword of prohibitedKeywords) {
      if (lowercaseContent.includes(keyword)) {
        console.warn(`🚫 Content safety violation detected: "${keyword}"`);
        return false;
      }
    }

    // Additional checks can be added here
    // - Length checks (too short/long)
    // - Spam detection
    // - External API calls for AI-based content moderation

    return true; // Content appears safe
  }
}
