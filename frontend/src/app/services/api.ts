import { HttpClient, HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

export const csrfInterceptor: HttpInterceptorFn = (request, next) => {
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
  return next(request);
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
  error = signal('');
  success = signal('');
  busy = signal(false);
  async run<T>(work: () => Promise<T>, message = ''): Promise<T | undefined> {
    this.error.set('');
    this.success.set('');
    this.busy.set(true);
    try {
      const result = await work();
      this.success.set(message);
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
      this.busy.set(false);
    }
  }
}
