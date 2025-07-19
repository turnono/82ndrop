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
import { Observable, BehaviorSubject, from, of } from 'rxjs';
import { switchMap, shareReplay, take } from 'rxjs/operators';

export interface UserClaims {
  agent_access?: boolean;
  access_level?: string;
  agent_permissions?: {
    [key: string]: boolean;
  };
  granted_at?: string;
  credits?: number;
}

export interface AuthUser {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoURL: string | null;
  claims: UserClaims;
  hasAgentAccess: boolean;
  credits: number;
}

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private userSubject = new BehaviorSubject<AuthUser | null>(null);
  public user$ = this.userSubject.asObservable().pipe(shareReplay(1));

  constructor(private auth: Auth, private router: Router) {
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
      const idTokenResult = await user.getIdTokenResult();
      const claims = idTokenResult.claims as UserClaims;
      return {
        uid: user.uid,
        email: user.email,
        displayName: user.displayName,
        photoURL: user.photoURL,
        claims: claims,
        hasAgentAccess: claims.agent_access === true,
        credits: claims.credits || 0,
      };
    } catch (error) {
      console.error('Error getting user claims:', error);
      return {
        uid: user.uid,
        email: user.email,
        displayName: user.displayName,
        photoURL: user.photoURL,
        claims: {},
        hasAgentAccess: false,
        credits: 0,
      };
    }
  }

  async signUpWithEmail(email: string, password: string): Promise<void> {
    try {
      await createUserWithEmailAndPassword(this.auth, email, password);
    } catch (error) {
      console.error('Sign up error:', error);
      throw error;
    }
  }

  async signInWithEmail(email: string, password: string): Promise<void> {
    try {
      await signInWithEmailAndPassword(this.auth, email, password);
    } catch (error) {
      console.error('Sign in error:', error);
      throw error;
    }
  }

  async signInWithGoogle(): Promise<void> {
    try {
      const provider = new GoogleAuthProvider();
      await signInWithPopup(this.auth, provider);
    } catch (error) {
      console.error('Google sign in error:', error);
      throw error;
    }
  }

  async signOut(): Promise<void> {
    try {
      await signOut(this.auth);
      this.router.navigate(['/']);
    } catch (error) {
      console.error('Sign out error:', error);
      throw error;
    }
  }

  async refreshUserToken(): Promise<void> {
    const currentUser = this.auth.currentUser;
    if (currentUser) {
      try {
        await currentUser.getIdToken(true);
        const authUser = await this.createAuthUser(currentUser);
        this.userSubject.next(authUser);
      } catch (error) {
        console.error('Error refreshing token:', error);
        throw error;
      }
    }
  }

  getUser(): Observable<AuthUser | null> {
    return this.user$;
  }

  isAuthenticated(): boolean {
    return this.userSubject.value !== null;
  }

  hasAgentAccess(): boolean {
    const user = this.userSubject.value;
    return user?.hasAgentAccess === true;
  }

  getCurrentUser(): AuthUser | null {
    return this.userSubject.value;
  }

  getFirebaseUser(): User | null {
    return this.auth.currentUser;
  }
}
