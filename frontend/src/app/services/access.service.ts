import { Injectable } from '@angular/core';
import { Functions, httpsCallable } from '@angular/fire/functions';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root',
})
export class AccessService {
  constructor(private functions: Functions, private authService: AuthService) {}

  /**
   * Request access for the current user
   */
  async requestAccess(): Promise<any> {
    const user = this.authService.getCurrentUser();
    if (!user) {
      throw new Error('User not authenticated');
    }

    const checkAndGrantAccess = httpsCallable(
      this.functions,
      'checkAndGrantAccess'
    );

    try {
      const result = await checkAndGrantAccess({ uid: user.uid });
      return result.data;
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
    const autoGrantAccess = httpsCallable(this.functions, 'autoGrantAccess');

    try {
      const result = await autoGrantAccess({ uid });
      return result.data;
    } catch (error) {
      console.error('Error auto-granting access:', error);
      throw error;
    }
  }
}
