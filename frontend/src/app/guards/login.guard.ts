import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { map, take, filter } from 'rxjs/operators';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class LoginGuard implements CanActivate {
  constructor(private authService: AuthService, private router: Router) {}

  canActivate(): Observable<boolean> {
    return this.authService.getUser().pipe(
      filter(user => user !== null), // Wait until auth state is resolved
      take(1),
      map((user) => {
        if (user) {
          // User is authenticated, redirect to dashboard
          this.router.navigate(['/dashboard']);
          return false;
        }
        // User is not authenticated, allow access to login
        return true;
      })
    );
  }
}
