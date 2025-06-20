import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { AuthService } from './auth.service';
import { environment } from '../../environments/environment';

export interface UserAnalytics {
  total_requests: number;
  total_chat_messages: number;
  avg_response_time: number | null;
  success_rate: number | null;
  first_seen: string;
  last_seen: string;
  access_level: string;
  email: string;
  successful_requests: number;
  failed_requests: number;
}

export interface DailyAnalytics {
  total_requests: number;
  unique_users: number;
  avg_response_time: number | null;
  successful_requests: number;
  failed_requests: number;
  chat_messages: number;
  access_levels: { [key: string]: number };
}

export interface AnalyticsOverview {
  user_stats: UserAnalytics;
  daily_stats?: DailyAnalytics;
}

@Injectable({
  providedIn: 'root',
})
export class AnalyticsService {
  private apiUrl = environment.apiUrl || 'http://127.0.0.1:8000';
  private analyticsSubject = new BehaviorSubject<AnalyticsOverview | null>(
    null
  );
  public analytics$ = this.analyticsSubject.asObservable();

  constructor(private http: HttpClient, private authService: AuthService) {}

  private async getAuthHeaders(): Promise<HttpHeaders> {
    return new Promise((resolve, reject) => {
      this.authService.getUser().subscribe(async (user) => {
        if (!user) {
          reject(new Error('User not authenticated'));
          return;
        }

        try {
          // Get the Firebase user for token operations
          const firebaseUser = this.authService.getFirebaseUser();
          if (!firebaseUser) {
            reject(new Error('Firebase user not available'));
            return;
          }

          const token = await firebaseUser.getIdToken();
          resolve(
            new HttpHeaders({
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json',
            })
          );
        } catch (error) {
          reject(error);
        }
      });
    });
  }

  async getAnalyticsOverview(): Promise<Observable<any>> {
    const headers = await this.getAuthHeaders();
    return this.http.get(`${this.apiUrl}/analytics/overview`, { headers });
  }

  async getDailyAnalytics(date?: string): Promise<Observable<any>> {
    const headers = await this.getAuthHeaders();
    const params: any = {};
    if (date) {
      params.date = date;
    }
    return this.http.get(`${this.apiUrl}/analytics/daily`, { headers, params });
  }

  async getUserAnalytics(userId: string): Promise<Observable<any>> {
    const headers = await this.getAuthHeaders();
    return this.http.get(`${this.apiUrl}/analytics/user/${userId}`, {
      headers,
    });
  }

  async exportAnalytics(): Promise<Observable<any>> {
    const headers = await this.getAuthHeaders();
    return this.http.get(`${this.apiUrl}/analytics/export`, { headers });
  }

  async loadUserAnalytics(): Promise<void> {
    try {
      const observable = await this.getAnalyticsOverview();
      observable.subscribe({
        next: (data) => {
          this.analyticsSubject.next(data.analytics_overview);
        },
        error: (error) => {
          console.error('Error loading analytics:', error);
          this.analyticsSubject.next(null);
        },
      });
    } catch (error) {
      console.error('Error loading analytics:', error);
      this.analyticsSubject.next(null);
    }
  }

  getAnalyticsData(): AnalyticsOverview | null {
    return this.analyticsSubject.value;
  }
}
