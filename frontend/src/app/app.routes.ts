import { Routes } from '@angular/router';
import { AuthGuard } from './guards/auth.guard';
import { LoginGuard } from './guards/login.guard';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./components/home/home.component').then((m) => m.HomeComponent),
  },
  {
    path: 'login',
    canActivate: [LoginGuard],
    loadComponent: () =>
      import('./components/login/login.component').then(
        (m) => m.LoginComponent
      ),
  },
  {
    path: 'dashboard',
    canActivate: [AuthGuard],
    loadComponent: () =>
      import('./components/dashboard/dashboard.component').then(
        (m) => m.DashboardComponent
      ),
  },
  {
    path: 'analytics',
    canActivate: [AuthGuard],
    loadComponent: () =>
      import('./components/analytics/analytics.component').then(
        (m) => m.AnalyticsComponent
      ),
  },
  {
    path: 'access-pending',
    loadComponent: () =>
      import('./components/access-pending/access-pending.component').then(
        (m) => m.AccessPendingComponent
      ),
  },
  {
    path: 'ai-test',
    canActivate: [AuthGuard],
    loadComponent: () =>
      import('./components/ai-test/ai-test.component').then(
        (m) => m.AiTestComponent
      ),
  },
  {
    path: '**',
    redirectTo: '',
  },
];
