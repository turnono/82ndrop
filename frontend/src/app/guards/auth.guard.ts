import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { Observable, map, take } from 'rxjs';
import { AuthService } from '../services/auth.service';

@Injectable({
  providedIn: 'root',
})
export class AuthGuard implements CanActivate {
  constructor(private authService: AuthService, private router: Router) {}

  canActivate(): Observable<boolean> {
    return this.authService.getUser().pipe(
      take(1),
      map((user) => {
        if (user && user.hasAgentAccess) {
          return true;
        } else if (user && !user.hasAgentAccess) {
          // User is authenticated but doesn't have agent access
          this.router.navigate(['/access-pending']);
          return false;
        } else {
          // User is not authenticated
          this.router.navigate(['/login']);
          return false;
        }
      })
    );
  }
}
