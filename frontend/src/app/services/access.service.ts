import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Functions, httpsCallable } from '@angular/fire/functions';
import { AuthService } from './auth.service';
import { firstValueFrom } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class AccessService {
  private checkAndGrantAccessUrl =
    'https://us-central1-taajirah.cloudfunctions.net/checkAndGrantAccess';
  private autoGrantAccessUrl =
    'https://us-central1-taajirah.cloudfunctions.net/autoGrantAccess';

  constructor(
    private functions: Functions,
    private authService: AuthService,
    private http: HttpClient
  ) {}

  /**
   * Request access for the current user
   */
  async requestAccess(): Promise<any> {
    const user = this.authService.getFirebaseUser();
    if (!user) {
      throw new Error('User not authenticated');
    }

    const idToken = await user.getIdToken();
    const headers = new HttpHeaders().set('Authorization', `Bearer ${idToken}`);

    try {
      const result = await firstValueFrom(
        this.http.post(this.checkAndGrantAccessUrl, {}, { headers })
      );
      return result;
    } catch (error) {
      console.error('Error requesting access:', error);
      throw error;
    }
  }

  /**
   * Manually grant access to a user (admin function)
   */
  async grantAccess(uid: string, accessLevel: string = 'basic'): Promise<any> {
    const grantAccessManual = httpsCallable(
      this.functions,
      'grantAccessManual'
    );

    try {
      const result = await grantAccessManual({ uid, accessLevel });
      return result.data;
    } catch (error) {
      console.error('Error granting access:', error);
      throw error;
    }
  }

  /**
   * Auto-grant access to a user
   */
  async autoGrantAccess(uid: string): Promise<any> {
    const user = this.authService.getFirebaseUser();
    if (!user) {
      throw new Error('User not authenticated');
    }
    const idToken = await user.getIdToken();
    const headers = new HttpHeaders().set('Authorization', `Bearer ${idToken}`);

    try {
      const result = await firstValueFrom(
        this.http.post(this.autoGrantAccessUrl, { uid }, { headers })
      );
      return result;
    } catch (error) {
      console.error('Error auto-granting access:', error);
      throw error;
    }
  }
}
