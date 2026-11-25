import { Injectable, signal } from '@angular/core';
import { User } from '../models/domain';

// Estado sin cliente HTTP: el interceptor puede invalidarlo sin ciclos de inyección.
@Injectable({ providedIn: 'root' })
export class SessionState {
  user = signal<User | null>(null);
  expired = signal(false);
}
