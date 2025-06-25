import { Component, OnInit, OnDestroy, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AuthService, AuthUser } from '../../services/auth.service';
import { AgentService } from '../../services/agent.service';
import { SessionHistoryService } from '../../services/session-history.service';
import { ChatComponent } from '../chat/chat.component';
import { SessionHistoryComponent } from '../session-history/session-history.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, ChatComponent, SessionHistoryComponent],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
})
export class DashboardComponent implements OnInit, OnDestroy {
  @ViewChild(ChatComponent) chatComponent!: ChatComponent;
  user: AuthUser | null = null;
  private _showChat = true; // Start directly in chat, user can go back to dashboard with back button
  showMobileSessionMenu = false;

  constructor(
    private authService: AuthService,
    private agentService: AgentService,
    private sessionHistoryService: SessionHistoryService
  ) {}

  get showChat(): boolean {
    return this._showChat;
  }

  set showChat(value: boolean) {
    this._showChat = value;
    this.updateBodyScrolling();
  }

  ngOnInit() {
    this.authService.getUser().subscribe((user) => {
      this.user = user;
    });
    this.updateBodyScrolling();
  }

  ngOnDestroy() {
    // Re-enable scrolling when component is destroyed
    document.body.classList.remove('no-scroll');
  }

  private updateBodyScrolling() {
    if (this._showChat) {
      document.body.classList.add('no-scroll');
    } else {
      document.body.classList.remove('no-scroll');
    }
  }

  async onSignOut() {
    try {
      await this.authService.signOut();
    } catch (error) {
      console.error('Sign out error:', error);
    }
  }

  onButtonMouseDown() {
    console.log('🖱️ BUTTON MOUSE DOWN DETECTED!');
  }

  async onSessionSelected(sessionId: string) {
    console.log('🎯 Dashboard: Session selected:', sessionId);

    try {
      // Set this as the current ADK session
      console.log('🔧 Setting ADK current session to:', sessionId);
      this.agentService.setCurrentSession(sessionId);

      // Load the session messages from Firebase
      console.log('📚 Loading session from Firebase...');
      await this.sessionHistoryService.loadSession(sessionId);

      // Show chat view if not already visible
      this.showChat = true;

      console.log('✅ Dashboard: Session loaded successfully');
    } catch (error) {
      console.error('❌ Dashboard: Error loading session:', error);
    }
  }

  onNewSessionCreated() {
    console.log('✨ New session created');
    // Reset chat component to show new session
    if (this.chatComponent) {
      this.chatComponent.startNewSession();
    }
  }

  startNewSession() {
    console.log('🚀 NEW SESSION BUTTON CLICKED!');

    // If chat is already shown, just start a new session
    if (this.showChat && this.chatComponent) {
      console.log('Chat already visible, starting new session directly');
      this.chatComponent.startNewSession();
      return;
    }

    // Show chat first, then start new session
    this.showChat = true;

    // Always call the agent service to reset the session
    this.agentService.startNewSession();

    // Wait for the view to update and chat component to be available
    setTimeout(() => {
      if (this.chatComponent) {
        console.log('Chat component found, initializing new session');
        this.chatComponent.startNewSession();
      } else {
        console.log(
          'Chat component not immediately available, session reset via service'
        );
        // Try again with a longer delay for Angular change detection
        setTimeout(() => {
          if (this.chatComponent) {
            console.log(
              'Chat component found on retry, initializing new session'
            );
            this.chatComponent.startNewSession();
          } else {
            console.log('Chat component handled via service fallback');
          }
        }, 200);
      }
    }, 100);
  }

  // Mobile session menu methods
  toggleMobileSessionMenu() {
    this.showMobileSessionMenu = !this.showMobileSessionMenu;
  }

  closeMobileSessionMenu() {
    this.showMobileSessionMenu = false;
  }

  onMobileSessionSelected(sessionId: string) {
    this.onSessionSelected(sessionId);
    this.closeMobileSessionMenu();
  }

  onMobileNewSession() {
    this.onNewSessionCreated();
    this.closeMobileSessionMenu();
  }
}
