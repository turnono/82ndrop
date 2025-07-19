import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { AgentService } from '../../services/agent.service';

@Component({
  selector: 'app-subscribe',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './subscribe.component.html',
  styleUrls: ['./subscribe.component.scss']
})
export class SubscribeComponent implements OnInit {
  userEmail: string | null = null;

  constructor(
    private authService: AuthService,
    private agentService: AgentService
  ) {}

  ngOnInit(): void {
    this.userEmail = this.authService.getCurrentUser()?.email || null;
  }

  async purchaseCredits(amount: number) {
    if (!this.userEmail) {
      console.error('User email not found');
      return;
    }
    try {
      const response = await this.agentService.initializePayment(this.userEmail, amount);
      if (response && response.data && response.data.authorization_url) {
        window.location.href = response.data.authorization_url;
      } else {
        console.error('Invalid response from payment initialization');
      }
    } catch (error) {
      console.error('Error initializing payment:', error);
    }
  }

  
}