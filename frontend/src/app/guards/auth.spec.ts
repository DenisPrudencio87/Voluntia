import { TestBed } from '@angular/core/testing';
import {
  provideRouter,
  Router,
  UrlTree,
  ActivatedRouteSnapshot,
  RouterStateSnapshot,
} from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { authGuard } from './auth';
import { Session } from '../services/session';
describe('Guard de permisos', () => {
  beforeEach(() =>
    TestBed.configureTestingModule({ providers: [provideRouter([]), provideHttpClient()] }),
  );
  it('envía al acceso a visitantes y bloquea roles no autorizados', () => {
    const route = { data: { role: 'administrador' } } as unknown as ActivatedRouteSnapshot;
    const run = () =>
      TestBed.runInInjectionContext(() => authGuard(route, {} as RouterStateSnapshot));
    expect(TestBed.inject(Router).serializeUrl(run() as UrlTree)).toBe('/acceso');
    TestBed.inject(Session).user.set({
      id_usuario: 1,
      correo: 'demo@example.org',
      roles: ['voluntario'],
      email_verificado: true,
      estado: 'activo',
    });
    expect(TestBed.inject(Router).serializeUrl(run() as UrlTree)).toBe('/panel');
    TestBed.inject(Session).user.update((u) => ({ ...u!, roles: ['administrador'] }));
    expect(run()).toBe(true);
  });
});
