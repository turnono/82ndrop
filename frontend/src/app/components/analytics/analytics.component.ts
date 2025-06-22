import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import {
  AnalyticsService,
  AnalyticsOverview,
  UserAnalytics,
  DailyAnalytics,
} from '../../services/analytics.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-analytics',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './analytics.component.html',
  styleUrls: ['./analytics.component.scss'],
})
export class AnalyticsComponent implements OnInit, OnDestroy {
  analytics: AnalyticsOverview | null = null;
  loading = true;
  error: string | null = null;
  isAdmin = false;
  private subscription: Subscription = new Subscription();

  constructor(
    private analyticsService: AnalyticsService,
    private authService: AuthService
  ) {}

  async ngOnInit() {
    // Check if user is admin
    this.authService.getUser().subscribe((user) => {
      if (user) {
        // You might want to check custom claims for admin status
        // For now, we'll load analytics and see if daily stats are available
        this.loadAnalytics();
      }
    });

    // Subscribe to analytics updates
    this.subscription.add(
      this.analyticsService.analytics$.subscribe((analytics) => {
        this.analytics = analytics;
        this.isAdmin = !!analytics?.daily_stats;
        this.loading = false;
      })
    );
  }

  ngOnDestroy() {
    this.subscription.unsubscribe();
  }

  async loadAnalytics() {
    this.loading = true;
    this.error = null;

    try {
      await this.analyticsService.loadUserAnalytics();
    } catch (error) {
      this.error = 'Failed to load analytics data';
      this.loading = false;
    }
  }

  async exportAnalytics() {
    if (!this.isAdmin) return;

    try {
      const observable = await this.analyticsService.exportAnalytics();
      observable.subscribe({
        next: (response) => {
          alert(`Analytics exported: ${response.filename}`);
        },
        error: (error) => {
          alert('Failed to export analytics');
        },
      });
    } catch (error) {
      alert('Failed to export analytics');
    }
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString();
  }

  formatTime(ms: number | null | undefined): string {
    if (ms == null || ms === undefined) {
      return 'N/A';
    }
    return `${ms.toFixed(0)}ms`;
  }

  formatPercentage(value: number | null | undefined): string {
    if (value == null || value === undefined) {
      return 'N/A';
    }
    return `${(value * 100).toFixed(1)}%`;
  }

  getAccessLevelColor(level: string): string {
    switch (level) {
      case 'admin':
        return '#e74c3c';
      case 'premium':
        return '#f39c12';
      case 'basic':
        return '#3498db';
      default:
        return '#95a5a6';
    }
  }

  getAccessLevels(): Array<{
    name: string;
    count: number;
    percentage: number;
  }> {
    if (!this.analytics?.daily_stats?.access_levels) {
      return [];
    }

    const levels = this.analytics.daily_stats.access_levels;
    const total = Object.values(levels).reduce((sum, count) => sum + count, 0);

    return Object.entries(levels).map(([name, count]) => ({
      name,
      count,
      percentage: total > 0 ? (count / total) * 100 : 0,
    }));
  }
}
