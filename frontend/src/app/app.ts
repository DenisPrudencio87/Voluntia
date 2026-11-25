import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet, NavigationEnd } from '@angular/router';
import { Session } from './services/session';
import { Feedback } from './services/api';
@Component({
  selector: 'app-root',
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  session = inject(Session);
  feedback = inject(Feedback);
  router = inject(Router);
  menu = false;
  constructor() {
    this.router.events.subscribe((e) => {
      if (e instanceof NavigationEnd) {
        this.feedback.error.set('');
        this.feedback.success.set('');
        window.scrollTo(0, 0);
      }
    });
  }
  async logout() {
    await this.feedback.run(async () => {
      await this.session.logout();
      await this.router.navigateByUrl('/');
    }, 'Sesión cerrada');
  }
}
