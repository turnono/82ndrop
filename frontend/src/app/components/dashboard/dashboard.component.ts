import { Component, OnInit, OnDestroy, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AuthService, AuthUser } from '../../services/auth.service';
import { AgentService } from '../../services/agent.service';
import { ChatComponent } from '../chat/chat.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, ChatComponent],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
})
export class DashboardComponent implements OnInit, OnDestroy {
  @ViewChild(ChatComponent) chatComponent!: ChatComponent;
  user: AuthUser | null = null;
  private _showChat = true; // Start directly in chat, user can go back to dashboard with back button

  constructor(
    private authService: AuthService,
    private agentService: AgentService
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
}
