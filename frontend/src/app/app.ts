import { Component, inject, effect } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet, NavigationEnd } from '@angular/router';
import { Session } from './services/session';
import { Feedback } from './services/api';
import { SessionState } from './services/session-state';
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
    const state = inject(SessionState);
    effect(() => {
      if (state.expired()) {
        state.expired.set(false);
        void this.router.navigateByUrl('/acceso');
      }
    });
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
      this.menu = false;
      await this.router.navigateByUrl('/acceso');
    }, 'Sesión cerrada');
  }
}
