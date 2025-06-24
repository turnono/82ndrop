import {
  Component,
  OnInit,
  OnDestroy,
  Output,
  EventEmitter,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  SessionHistoryService,
  ChatSession,
} from '../../services/session-history.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-session-history',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="session-history-container">
      <div class="session-history-header">
        <h3>Recent Sessions</h3>
        <button
          class="new-session-btn"
          (click)="createNewSession()"
          title="New Session"
        >
          <span class="plus-icon">+</span>
        </button>
      </div>

      <div class="sessions-list" *ngIf="sessions.length > 0">
        <div
          *ngFor="let session of sessions; trackBy: trackSession"
          class="session-item"
          [class.active]="currentSession?.id === session.id"
          (click)="loadSession(session.id)"
        >
          <div class="session-info">
            <div class="session-title" [title]="session.title">
              {{ session.title }}
            </div>
            <div class="session-preview" [title]="session.preview">
              {{ session.preview }}
            </div>
            <div class="session-meta">
              <span class="message-count"
                >{{ session.messageCount }} messages</span
              >
              <span class="session-date">{{
                formatDate(session.updatedAt)
              }}</span>
            </div>
          </div>
          <div class="session-actions">
            <button
              class="edit-btn"
              (click)="startEdit(session, $event)"
              title="Rename session"
            >
              ✏️
            </button>
            <button
              class="delete-btn"
              (click)="confirmDelete(session, $event)"
              title="Delete session"
            >
              🗑️
            </button>
          </div>
        </div>
      </div>

      <div class="empty-state" *ngIf="sessions.length === 0">
        <div class="empty-icon">💬</div>
        <p>No chat sessions yet</p>
        <button class="btn btn-primary" (click)="createNewSession()">
          Start Your First Chat
        </button>
      </div>

      <!-- Edit Modal -->
      <div class="modal-overlay" *ngIf="editingSession" (click)="cancelEdit()">
        <div class="modal-content" (click)="$event.stopPropagation()">
          <h4>Rename Session</h4>
          <input
            type="text"
            [(ngModel)]="editTitle"
            class="title-input"
            placeholder="Enter session title"
            (keyup.enter)="saveEdit()"
            (keyup.escape)="cancelEdit()"
            #titleInput
          />
          <div class="modal-actions">
            <button class="btn btn-secondary" (click)="cancelEdit()">
              Cancel
            </button>
            <button class="btn btn-primary" (click)="saveEdit()">Save</button>
          </div>
        </div>
      </div>

      <!-- Delete Confirmation Modal -->
      <div
        class="modal-overlay"
        *ngIf="deletingSession"
        (click)="cancelDelete()"
      >
        <div class="modal-content" (click)="$event.stopPropagation()">
          <h4>Delete Session</h4>
          <p>Are you sure you want to delete "{{ deletingSession.title }}"?</p>
          <p class="warning">This action cannot be undone.</p>
          <div class="modal-actions">
            <button class="btn btn-secondary" (click)="cancelDelete()">
              Cancel
            </button>
            <button class="btn btn-danger" (click)="deleteSession()">
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .session-history-container {
        height: 100%;
        display: flex;
        flex-direction: column;
        background: white;
        border-right: 1px solid #e9ecef;
      }

      .session-history-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 20px;
        border-bottom: 1px solid #e9ecef;
        background: #f8f9fa;
      }

      .session-history-header h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        color: #2c3e50;
      }

      .new-session-btn {
        width: 32px;
        height: 32px;
        background: #667eea;
        border: none;
        border-radius: 50%;
        color: white;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s;
      }

      .new-session-btn:hover {
        background: #5a6fd8;
        transform: scale(1.05);
      }

      .plus-icon {
        font-size: 16px;
        font-weight: 300;
      }

      .sessions-list {
        flex: 1;
        overflow-y: auto;
        padding: 8px 0;
      }

      .session-item {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        padding: 12px 20px;
        cursor: pointer;
        transition: all 0.2s;
        border-bottom: 1px solid #f0f0f0;
      }

      .session-item:hover {
        background: #f8f9fa;
      }

      .session-item.active {
        background: #e3f2fd;
        border-left: 4px solid #667eea;
      }

      .session-info {
        flex: 1;
        min-width: 0;
      }

      .session-title {
        font-weight: 600;
        font-size: 14px;
        color: #2c3e50;
        margin-bottom: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .session-preview {
        font-size: 12px;
        color: #6c757d;
        margin-bottom: 6px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .session-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 11px;
        color: #9ca3af;
      }

      .session-actions {
        display: flex;
        gap: 8px;
        opacity: 0;
        transition: opacity 0.2s;
      }

      .session-item:hover .session-actions {
        opacity: 1;
      }

      .edit-btn,
      .delete-btn {
        width: 24px;
        height: 24px;
        border: none;
        background: transparent;
        cursor: pointer;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        transition: all 0.2s;
      }

      .edit-btn:hover {
        background: #e3f2fd;
      }

      .delete-btn:hover {
        background: #ffebee;
      }

      .empty-state {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px 20px;
        text-align: center;
        color: #6c757d;
      }

      .empty-icon {
        font-size: 48px;
        margin-bottom: 16px;
        opacity: 0.5;
      }

      .empty-state p {
        margin-bottom: 20px;
        font-size: 14px;
      }

      .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
      }

      .modal-content {
        background: white;
        border-radius: 12px;
        padding: 24px;
        min-width: 300px;
        max-width: 400px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
      }

      .modal-content h4 {
        margin: 0 0 16px 0;
        font-size: 18px;
        color: #2c3e50;
      }

      .title-input {
        width: 100%;
        padding: 12px 16px;
        border: 2px solid #e9ecef;
        border-radius: 8px;
        font-size: 14px;
        margin-bottom: 20px;
        outline: none;
        transition: border-color 0.2s;
      }

      .title-input:focus {
        border-color: #667eea;
      }

      .modal-actions {
        display: flex;
        gap: 12px;
        justify-content: flex-end;
      }

      .btn {
        padding: 8px 16px;
        border: none;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
      }

      .btn-primary {
        background: #667eea;
        color: white;
      }

      .btn-primary:hover {
        background: #5a6fd8;
      }

      .btn-secondary {
        background: #e9ecef;
        color: #6c757d;
      }

      .btn-secondary:hover {
        background: #dee2e6;
      }

      .btn-danger {
        background: #dc3545;
        color: white;
      }

      .btn-danger:hover {
        background: #c82333;
      }

      .warning {
        color: #dc3545;
        font-size: 12px;
        margin-bottom: 20px;
      }

      /* Mobile responsive */
      @media (max-width: 768px) {
        .session-history-header {
          padding: 12px 16px;
        }

        .session-item {
          padding: 10px 16px;
        }

        .session-title {
          font-size: 13px;
        }

        .session-preview {
          font-size: 11px;
        }

        .modal-content {
          margin: 20px;
          min-width: auto;
        }
      }
    `,
  ],
})
export class SessionHistoryComponent implements OnInit, OnDestroy {
  @Output() sessionSelected = new EventEmitter<string>();
  @Output() newSessionCreated = new EventEmitter<void>();

  sessions: ChatSession[] = [];
  currentSession: ChatSession | null = null;
  editingSession: ChatSession | null = null;
  deletingSession: ChatSession | null = null;
  editTitle = '';

  private subscriptions: Subscription[] = [];

  constructor(private sessionHistoryService: SessionHistoryService) {}

  ngOnInit() {
    // Subscribe to sessions
    this.subscriptions.push(
      this.sessionHistoryService.sessions$.subscribe((sessions) => {
        this.sessions = sessions;
      })
    );

    // Subscribe to current session
    this.subscriptions.push(
      this.sessionHistoryService.currentSession$.subscribe((session) => {
        this.currentSession = session;
      })
    );
  }

  ngOnDestroy() {
    this.subscriptions.forEach((sub) => sub.unsubscribe());
  }

  trackSession(index: number, session: ChatSession): string {
    return session.id;
  }

  async createNewSession() {
    try {
      const session = await this.sessionHistoryService.createSession();
      this.newSessionCreated.emit();
    } catch (error) {
      console.error('Error creating new session:', error);
    }
  }

  async loadSession(sessionId: string) {
    try {
      await this.sessionHistoryService.loadSession(sessionId);
      this.sessionSelected.emit(sessionId);
    } catch (error) {
      console.error('Error loading session:', error);
    }
  }

  startEdit(session: ChatSession, event: Event) {
    event.stopPropagation();
    this.editingSession = session;
    this.editTitle = session.title;

    // Focus input after view update
    setTimeout(() => {
      const input = document.querySelector('.title-input') as HTMLInputElement;
      if (input) {
        input.focus();
        input.select();
      }
    }, 100);
  }

  async saveEdit() {
    if (this.editingSession && this.editTitle.trim()) {
      try {
        await this.sessionHistoryService.updateSessionTitle(
          this.editingSession.id,
          this.editTitle.trim()
        );
        this.cancelEdit();
      } catch (error) {
        console.error('Error updating session title:', error);
      }
    }
  }

  cancelEdit() {
    this.editingSession = null;
    this.editTitle = '';
  }

  confirmDelete(session: ChatSession, event: Event) {
    event.stopPropagation();
    this.deletingSession = session;
  }

  async deleteSession() {
    if (this.deletingSession) {
      try {
        await this.sessionHistoryService.deleteSession(this.deletingSession.id);
        this.cancelDelete();
      } catch (error) {
        console.error('Error deleting session:', error);
      }
    }
  }

  cancelDelete() {
    this.deletingSession = null;
  }

  formatDate(timestamp: number): string {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;

    return date.toLocaleDateString();
  }
}
