import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { Observable, of } from 'rxjs';
import { switchMap, filter, take } from 'rxjs/operators';
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
      // Wait until the user is no longer null
      filter(user => user !== null),
      take(1),
      switchMap(user => {
        if (user) {
          if (user.hasAgentAccess) {
            return of(true);
          } else {
            // User is authenticated but doesn't have agent access.
            // Start the auto-grant process.
            this.tryAutoGrantAccessAndReload(user.uid);
            // Immediately redirect to a pending page and block the current navigation.
            this.router.navigate(['/access-pending']);
            return of(false);
          }
        } else {
          // User is not authenticated.
          this.router.navigate(['/login']);
          return of(false);
        }
      })
    );
  }

  private async tryAutoGrantAccessAndReload(uid: string): Promise<void> {
    try {
      await this.accessService.autoGrantAccess(uid);
      // Wait for backend claims to propagate.
      await new Promise(resolve => setTimeout(resolve, 2500));
      // Refresh the token to get the latest claims.
      await this.authService.refreshUserToken();

      // Check if access was granted.
      if (this.authService.hasAgentAccess()) {
        // Reload the entire application to ensure the new state is loaded correctly.
        window.location.reload();
      } else {
        // If access was not granted, the user is already on the access-pending page.
        console.error('Auto-grant access failed.');
      }
    } catch (error) {
      console.error('Error during auto-grant access process:', error);
      // On error, the user remains on the access-pending page.
    }
  }
}
