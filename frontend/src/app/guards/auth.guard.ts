import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { Observable, map, take, from } from 'rxjs';
import { AuthService } from '../services/auth.service';
import { AccessService } from '../services/access.service';

@Injectable({
  providedIn: 'root',
})
export class AuthGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private router: Router,
    private accessService: AccessService
  ) {}

  canActivate(): Observable<boolean> {
    return this.authService.getUser().pipe(
      take(1),
      map((user) => {
        if (user && user.hasAgentAccess) {
          return true;
        } else if (user && !user.hasAgentAccess) {
          // User is authenticated but doesn't have agent access
          // Try to auto-grant access instead of redirecting to pending screen
          this.tryAutoGrantAccess(user.uid);
          return false;
        } else {
          // User is not authenticated
          this.router.navigate(['/login']);
          return false;
        }
      })
    );
  }

  private async tryAutoGrantAccess(uid: string) {
    try {
      await this.accessService.autoGrantAccess(uid);

      // Wait for claims to be processed
      await new Promise((resolve) => setTimeout(resolve, 1500));

      // Refresh token to get updated claims
      await this.authService.refreshUserToken();

      // Check if access was granted
      if (this.authService.hasAgentAccess()) {
        // Don't navigate here, let the auth state change handle it
        window.location.reload(); // Force a reload to re-trigger auth check
      } else {
        // If auto-grant failed, show the access-pending screen
        this.router.navigate(['/access-pending']);
      }
    } catch (error) {
      console.error('Error auto-granting access:', error);
      // If auto-granting fails, fall back to the access-pending screen
      this.router.navigate(['/access-pending']);
    }
  }
}
