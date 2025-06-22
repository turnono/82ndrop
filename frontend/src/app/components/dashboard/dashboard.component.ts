import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AuthService, AuthUser } from '../../services/auth.service';
import { ChatComponent } from '../chat/chat.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, ChatComponent],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
})
export class DashboardComponent implements OnInit, OnDestroy {
  user: AuthUser | null = null;
  private _showChat = true; // Start directly in chat, user can go back to dashboard with back button

  constructor(private authService: AuthService) {}

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
}
