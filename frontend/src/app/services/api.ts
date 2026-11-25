import { HttpClient, HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom, catchError, throwError } from 'rxjs';
import { SessionState } from './session-state';

export const csrfInterceptor: HttpInterceptorFn = (request, next) => {
  const state = inject(SessionState);
  const token = document.cookie
    .split('; ')
    .find((c) => c.startsWith('voluntia_csrf='))
    ?.split('=')
    .slice(1)
    .join('=');
  if (
    token &&
    !['GET', 'HEAD', 'OPTIONS'].includes(request.method) &&
    request.url.startsWith('/api/')
  ) {
    request = request.clone({ setHeaders: { 'X-CSRF-Token': decodeURIComponent(token) } });
  }
  return next(request).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401 && request.url.startsWith('/api/')) {
        if (state.user()) state.expired.set(true);
        state.user.set(null);
      }
      return throwError(() => error);
    }),
  );
};

@Injectable({ providedIn: 'root' })
export class Api {
  private http = inject(HttpClient);
  get<T>(path: string) {
    return firstValueFrom(this.http.get<T>('/api/v1' + path));
  }
  post<T>(path: string, data: unknown = {}) {
    return firstValueFrom(this.http.post<T>('/api/v1' + path, data));
  }
  put<T>(path: string, data: unknown) {
    return firstValueFrom(this.http.put<T>('/api/v1' + path, data));
  }
}

@Injectable({ providedIn: 'root' })
export class Feedback {
  private pending = 0;
  error = signal('');
  success = signal('');
  busy = signal(false);
  async run<T>(work: () => Promise<T>, message = ''): Promise<T | undefined> {
    this.error.set('');
    this.success.set('');
    this.pending++;
    this.busy.set(true);
    try {
      const result = await work();
      if (message) this.success.set(message);
      return result;
    } catch (error) {
      const e = error as HttpErrorResponse;
      const body = e.error;
      this.error.set(
        typeof body?.detail === 'string'
          ? body.detail +
              (body.campos?.length
                ? ': ' +
                  body.campos
                    .map((c: { campo: string; mensaje: string }) => c.campo + ' ' + c.mensaje)
                    .join(', ')
                : '')
          : 'No se pudo completar la operación. Revisa la conexión e intenta de nuevo.',
      );
      return undefined;
    } finally {
      this.pending--;
      this.busy.set(this.pending > 0);
    }
  }
}
