import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { USER } from '../../constant/constant';

export const authGuard: CanActivateFn = (route, state) => {
  const router = inject(Router);
  if (localStorage.getItem(USER.TOKEN)) {
    return true;
  }
  router.navigate(['/login']);
  return false;
};
