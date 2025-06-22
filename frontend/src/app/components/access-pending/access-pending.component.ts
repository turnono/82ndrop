import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth.service';
import { AccessService } from '../../services/access.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-access-pending',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="access-pending-container">
      <div class="access-pending-card">
        <div class="icon">
          <svg
            width="64"
            height="64"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"
              fill="#f39c12"
            />
          </svg>
        </div>

        <h1>Access Pending</h1>

        <p class="message">
          Your account has been created successfully! Click "Request Access"
          below to activate your 82ndrop agent system access.
        </p>

        <div class="user-info" *ngIf="user">
          <p><strong>Account:</strong> {{ user.email }}</p>
          <p><strong>User ID:</strong> {{ user.uid }}</p>
        </div>

        <div class="instructions">
          <h3>What's Next?</h3>
          <ol>
            <li>Click "Request Access" to automatically grant agent access</li>
            <li>Access is typically granted immediately</li>
            <li>Contact support if you encounter any issues</li>
          </ol>
        </div>

        <div class="actions">
          <button
            class="refresh-btn"
            (click)="checkAccess()"
            [disabled]="isChecking"
          >
            <span *ngIf="!isChecking">Check Access Status</span>
            <span *ngIf="isChecking">Checking...</span>
          </button>

          <button
            class="request-btn"
            (click)="requestAccess()"
            [disabled]="isRequesting"
          >
            <span *ngIf="!isRequesting">Request Access</span>
            <span *ngIf="isRequesting">Requesting...</span>
          </button>

          <button class="logout-btn" (click)="signOut()">Sign Out</button>
        </div>

        <div class="support-info">
          <p><strong>Need Help?</strong></p>
          <p>Contact our support team for assistance with account access.</p>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .access-pending-container {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
      }

      .access-pending-card {
        background: white;
        border-radius: 16px;
        padding: 40px;
        max-width: 500px;
        width: 100%;
        text-align: center;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
      }

      .icon {
        margin-bottom: 24px;
      }

      h1 {
        color: #2c3e50;
        margin-bottom: 16px;
        font-size: 2rem;
        font-weight: 600;
      }

      .message {
        color: #7f8c8d;
        margin-bottom: 24px;
        font-size: 1.1rem;
        line-height: 1.6;
      }

      .user-info {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 24px;
        text-align: left;
      }

      .user-info p {
        margin: 8px 0;
        color: #495057;
      }

      .instructions {
        text-align: left;
        margin-bottom: 32px;
      }

      .instructions h3 {
        color: #2c3e50;
        margin-bottom: 16px;
      }

      .instructions ol {
        color: #7f8c8d;
        line-height: 1.6;
      }

      .instructions li {
        margin-bottom: 8px;
      }

      .actions {
        display: flex;
        gap: 16px;
        justify-content: center;
        margin-bottom: 32px;
      }

      .refresh-btn,
      .request-btn,
      .logout-btn {
        padding: 12px 24px;
        border-radius: 8px;
        border: none;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
      }

      .refresh-btn {
        background: #3498db;
        color: white;
      }

      .refresh-btn:hover {
        background: #2980b9;
      }

      .refresh-btn:disabled {
        background: #bdc3c7;
        cursor: not-allowed;
      }

      .request-btn {
        background: #27ae60;
        color: white;
      }

      .request-btn:hover {
        background: #229954;
      }

      .request-btn:disabled {
        background: #bdc3c7;
        cursor: not-allowed;
      }

      .logout-btn {
        background: #e74c3c;
        color: white;
      }

      .logout-btn:hover {
        background: #c0392b;
      }

      .support-info {
        border-top: 1px solid #ecf0f1;
        padding-top: 24px;
        color: #7f8c8d;
      }

      .support-info p {
        margin: 8px 0;
      }

      @media (max-width: 600px) {
        .access-pending-card {
          padding: 24px;
        }

        .actions {
          flex-direction: column;
        }
      }
    `,
  ],
})
export class AccessPendingComponent implements OnInit {
  user: any = null;
  isChecking = false;
  isRequesting = false;

  constructor(
    private authService: AuthService,
    private accessService: AccessService,
    private router: Router
  ) {}

  ngOnInit() {
    this.authService.getUser().subscribe((user) => {
      this.user = user;
    });
  }

  async checkAccess() {
    this.isChecking = true;
    try {
      // Refresh the user token to get updated claims
      await this.authService.refreshUserToken();

      // Check if user now has access
      if (this.authService.hasAgentAccess()) {
        this.router.navigate(['/dashboard']);
      } else {
        alert(
          'Access is still pending. Please try again later or contact support.'
        );
      }
    } catch (error) {
      console.error('Error checking access:', error);
      alert('Failed to check access status. Please try again.');
    } finally {
      this.isChecking = false;
    }
  }

  async requestAccess() {
    this.isRequesting = true;
    try {
      // Request access via the access service
      const result = await this.accessService.requestAccess();

      if (result.was_granted) {
        // Access was granted, refresh token and redirect
        await this.authService.refreshUserToken();
        alert('Access granted! Redirecting to dashboard...');
        this.router.navigate(['/dashboard']);
      } else {
        alert(
          'Access request submitted. You already have access or it will be reviewed.'
        );
      }
    } catch (error) {
      console.error('Error requesting access:', error);
      alert('Failed to request access. Please try again or contact support.');
    } finally {
      this.isRequesting = false;
    }
  }

  async signOut() {
    try {
      await this.authService.signOut();
    } catch (error) {
      console.error('Error signing out:', error);
    }
  }
}
