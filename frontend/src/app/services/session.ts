import { Injectable, inject, signal } from '@angular/core';
import { Api } from './api';
import { User } from '../models/domain';
import { HttpErrorResponse } from '@angular/common/http';
import { SessionState } from './session-state';

@Injectable({ providedIn: 'root' })
export class Session {
  private api = inject(Api);
  user = inject(SessionState).user;
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
    } catch (error) {
      this.user.set(null);
      if (![401, 403].includes((error as HttpErrorResponse).status)) throw error;
    }
  }
  has(role: string) {
    return !!this.user()?.roles.includes(role);
  }
  async logout() {
    await this.api.get('/auth/csrf');
    await this.api.post('/auth/logout');
    this.user.set(null);
    await this.api.get('/auth/csrf');
  }
}
