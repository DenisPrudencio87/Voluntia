import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { Session } from '../services/session';

export const authGuard: CanActivateFn = (route) => {
  const session = inject(Session),
    router = inject(Router);
  if (!session.user()) return router.createUrlTree(['/acceso']);
  const role = route.data['role'] as string | undefined;
  if (role && !session.has(role)) return router.createUrlTree(['/panel']);
  return true;
};
