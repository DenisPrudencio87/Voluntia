import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { Api, csrfInterceptor } from './api';
describe('Comunicación API', () => {
  it('envía CSRF en escrituras de la API', async () => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([csrfInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    document.cookie = 'voluntia_csrf=token-ficticio; path=/';
    const pending = TestBed.inject(Api).post('/auth/logout');
    const request = TestBed.inject(HttpTestingController).expectOne('/api/v1/auth/logout');
    expect(request.request.headers.get('X-CSRF-Token')).toBe('token-ficticio');
    request.flush({ mensaje: 'Sesión cerrada' });
    await pending;
    TestBed.inject(HttpTestingController).verify();
  });
});
