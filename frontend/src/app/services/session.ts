import { Injectable, inject, signal } from '@angular/core';
import { Api } from './api';
import { User } from '../models/domain';

@Injectable({ providedIn: 'root' })
export class Session {
  private api = inject(Api);
  user = signal<User | null>(null);
  config = signal({ public_signup_enabled: false, email_enabled: false, app_env: 'local' });
  available = signal(true);
  async initialize() {
    try {
      this.config.set(await this.api.get('/auth/csrf'));
      await this.refresh();
    } catch {
      this.available.set(false);
    }
  }
  async refresh() {
    try {
      this.user.set(await this.api.get<User>('/auth/me'));
    } catch {
      this.user.set(null);
    }
  }
  has(role: string) {
    return !!this.user()?.roles.includes(role);
  }
  async logout() {
    await this.api.post('/auth/logout');
    this.user.set(null);
    await this.api.get('/auth/csrf');
  }
}
