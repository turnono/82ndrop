import { Injectable } from '@angular/core';
import {
  Auth,
  User,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  signOut,
  onAuthStateChanged,
} from '@angular/fire/auth';
import { Router } from '@angular/router';
import { Observable, BehaviorSubject } from 'rxjs';

export interface UserClaims {
  agent_access?: boolean;
  access_level?: string;
  agent_permissions?: {
    [key: string]: boolean;
  };
  granted_at?: string;
}

export interface AuthUser {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoURL: string | null;
  claims: UserClaims;
  hasAgentAccess: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private userSubject = new BehaviorSubject<AuthUser | null>(null);
  public user$ = this.userSubject.asObservable();

  constructor(private auth: Auth, private router: Router) {
    // Listen to auth state changes
    onAuthStateChanged(this.auth, async (user) => {
      if (user) {
        const authUser = await this.createAuthUser(user);
        this.userSubject.next(authUser);
      } else {
        this.userSubject.next(null);
      }
    });
  }

  private async createAuthUser(user: User): Promise<AuthUser> {
    try {
      // Get ID token result to access custom claims
      const idTokenResult = await user.getIdTokenResult();
      const claims = idTokenResult.claims as UserClaims;

      return {
        uid: user.uid,
        email: user.email,
        displayName: user.displayName,
        photoURL: user.photoURL,
        claims: claims,
        hasAgentAccess: claims.agent_access === true,
      };
    } catch (error) {
      console.error('Error getting user claims:', error);
      // Return user with no claims if there's an error
      return {
        uid: user.uid,
        email: user.email,
        displayName: user.displayName,
        photoURL: user.photoURL,
        claims: {},
        hasAgentAccess: false,
      };
    }
  }

  /**
   * Sign up with email and password
   */
  async signUpWithEmail(email: string, password: string): Promise<void> {
    try {
      const credential = await createUserWithEmailAndPassword(
        this.auth,
        email,
        password
      );
      // Note: Custom claims will be set by backend or cloud function
      // User may need to wait or refresh token to get access
    } catch (error) {
      console.error('Sign up error:', error);
      throw error;
    }
  }

  /**
   * Sign in with email and password
   */
  async signInWithEmail(email: string, password: string): Promise<void> {
    try {
      const credential = await signInWithEmailAndPassword(
        this.auth,
        email,
        password
      );
    } catch (error) {
      console.error('Sign in error:', error);
      throw error;
    }
  }

  /**
   * Sign in with Google
   */
  async signInWithGoogle(): Promise<void> {
    try {
      const provider = new GoogleAuthProvider();
      const credential = await signInWithPopup(this.auth, provider);
    } catch (error) {
      console.error('Google sign in error:', error);
      throw error;
    }
  }

  /**
   * Sign out
   */
  async signOut(): Promise<void> {
    try {
      await signOut(this.auth);
      this.router.navigate(['/']);
    } catch (error) {
      console.error('Sign out error:', error);
      throw error;
    }
  }

  /**
   * Refresh user token to get updated claims
   */
  async refreshUserToken(): Promise<void> {
    const currentUser = this.auth.currentUser;
    if (currentUser) {
      try {
        // Force refresh the token to get updated claims
        await currentUser.getIdToken(true);
        // Update the user subject with new claims
        const authUser = await this.createAuthUser(currentUser);
        this.userSubject.next(authUser);
      } catch (error) {
        console.error('Error refreshing token:', error);
        throw error;
      }
    }
  }

  /**
   * Get current user as observable
   */
  getUser(): Observable<AuthUser | null> {
    return this.user$;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.userSubject.value !== null;
  }

  /**
   * Check if user has agent access
   */
  hasAgentAccess(): boolean {
    const user = this.userSubject.value;
    return user?.hasAgentAccess === true;
  }

  /**
   * Get user's access level
   */
  getAccessLevel(): string {
    const user = this.userSubject.value;
    return user?.claims.access_level || 'none';
  }

  /**
   * Check if user has specific permission
   */
  hasPermission(permission: string): boolean {
    const user = this.userSubject.value;
    return user?.claims.agent_permissions?.[permission] === true;
  }

  /**
   * Get current user (synchronous)
   */
  getCurrentUser(): AuthUser | null {
    return this.userSubject.value;
  }

  /**
   * Get Firebase user for token operations
   */
  getFirebaseUser(): User | null {
    return this.auth.currentUser;
  }
}
