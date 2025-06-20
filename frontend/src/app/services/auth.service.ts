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

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private userSubject = new BehaviorSubject<User | null>(null);
  public user$ = this.userSubject.asObservable();

  constructor(private auth: Auth, private router: Router) {
    // Listen to auth state changes
    onAuthStateChanged(this.auth, (user) => {
      this.userSubject.next(user);
    });
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
      console.log('Sign up successful:', credential.user);
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
      console.log('Sign in successful:', credential.user);
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
      console.log('Google sign in successful:', credential.user);
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
      console.log('Sign out successful');
    } catch (error) {
      console.error('Sign out error:', error);
      throw error;
    }
  }

  /**
   * Get current user as observable
   */
  getUser(): Observable<User | null> {
    return this.user$;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.userSubject.value !== null;
  }

  /**
   * Get current user (synchronous)
   */
  getCurrentUser(): User | null {
    return this.userSubject.value;
  }
}
