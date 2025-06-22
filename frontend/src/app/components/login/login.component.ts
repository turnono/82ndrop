import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  FormGroup,
  Validators,
  ReactiveFormsModule,
} from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { Subscription } from 'rxjs';
import { AccessService } from '../../services/access.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
})
export class LoginComponent implements OnInit, OnDestroy {
  loginForm: FormGroup;
  isLoading = false;
  errorMessage = '';
  isSignUpMode = false;
  private authSubscription?: Subscription;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private accessService: AccessService
  ) {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
    });
  }

  ngOnInit() {
    // Check if user is already authenticated
    this.authSubscription = this.authService.getUser().subscribe((user) => {
      if (user) {
        // User is authenticated, redirect to dashboard
        this.router.navigate(['/dashboard']);
      }
    });
  }

  ngOnDestroy() {
    if (this.authSubscription) {
      this.authSubscription.unsubscribe();
    }
  }

  async onEmailSubmit() {
    if (this.loginForm.valid) {
      this.isLoading = true;
      this.errorMessage = '';

      try {
        const { email, password } = this.loginForm.value;

        if (this.isSignUpMode) {
          await this.authService.signUpWithEmail(email, password);
          // For new users, wait a moment then check if they need access granted
          await this.handleNewUserAccess();
        } else {
          await this.authService.signInWithEmail(email, password);
          // For existing users, check their access status
          await this.handleExistingUserAccess();
        }
      } catch (error: any) {
        this.errorMessage = this.getErrorMessage(error);
      } finally {
        this.isLoading = false;
      }
    } else {
      this.markFormGroupTouched();
    }
  }

  private async handleNewUserAccess() {
    try {
      // Wait a moment for the user to be fully created
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Automatically grant access to new users
      const user = this.authService.getCurrentUser();
      if (user) {
        await this.accessService.autoGrantAccess(user.uid);

        // Wait a moment for the claims to be processed
        await new Promise((resolve) => setTimeout(resolve, 1500));

        // Refresh token to get updated claims
        await this.authService.refreshUserToken();

        // Redirect directly to dashboard
        this.router.navigate(['/dashboard']);
      } else {
        throw new Error('User not found after signup');
      }
    } catch (error) {
      console.error('Error handling new user access:', error);
      // If auto-granting fails, fall back to the access-pending screen
      this.router.navigate(['/access-pending']);
    }
  }

  private async handleExistingUserAccess() {
    try {
      // Check if user has access
      if (this.authService.hasAgentAccess()) {
        this.router.navigate(['/dashboard']);
      } else {
        // Automatically grant access to existing users who don't have it
        const user = this.authService.getCurrentUser();
        if (user) {
          await this.accessService.autoGrantAccess(user.uid);

          // Wait a moment for the claims to be processed
          await new Promise((resolve) => setTimeout(resolve, 1500));

          // Refresh token to get updated claims
          await this.authService.refreshUserToken();

          // Redirect to dashboard
          this.router.navigate(['/dashboard']);
        } else {
          throw new Error('User not found');
        }
      }
    } catch (error) {
      console.error('Error checking user access:', error);
      // If auto-granting fails, fall back to the access-pending screen
      this.router.navigate(['/access-pending']);
    }
  }

  async onGoogleLogin() {
    this.isLoading = true;
    this.errorMessage = '';

    try {
      await this.authService.signInWithGoogle();
      // Handle Google login access check
      await this.handleExistingUserAccess();
    } catch (error: any) {
      this.errorMessage = this.getErrorMessage(error);
    } finally {
      this.isLoading = false;
    }
  }

  toggleMode() {
    this.isSignUpMode = !this.isSignUpMode;
    this.errorMessage = '';
    this.loginForm.reset();
  }

  private getErrorMessage(error: any): string {
    switch (error.code) {
      case 'auth/user-not-found':
        return 'No account found with this email address.';
      case 'auth/wrong-password':
        return 'Incorrect password.';
      case 'auth/invalid-email':
        return 'Invalid email address.';
      case 'auth/user-disabled':
        return 'This account has been disabled.';
      case 'auth/email-already-in-use':
        return 'An account with this email already exists.';
      case 'auth/weak-password':
        return 'Password is too weak. Please choose a stronger password.';
      case 'auth/too-many-requests':
        return 'Too many failed attempts. Please try again later.';
      case 'auth/popup-closed-by-user':
        return 'Sign-in popup was closed. Please try again.';
      default:
        return this.isSignUpMode
          ? 'An error occurred during sign-up. Please try again.'
          : 'An error occurred during sign-in. Please try again.';
    }
  }

  private markFormGroupTouched() {
    Object.keys(this.loginForm.controls).forEach((key) => {
      this.loginForm.get(key)?.markAsTouched();
    });
  }

  get email() {
    return this.loginForm.get('email');
  }
  get password() {
    return this.loginForm.get('password');
  }
}
