import { HttpInterceptorFn } from '@angular/common/http';
import { USER } from '../../constant/constant';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  console.log('In interseptor');
  const authTocken = localStorage.getItem(USER.TOKEN);
  // if (authTocken) {
  //   req = req.clone({
  //     setHeaders: { authorization: `Token ${authTocken}` },
  //   });
  // }
  //commenting for now

  //  else {
  //   req = req.clone({
  //     setHeaders: { observe: 'response' },
  //   });
  // }  //need to uncomment this after login implementation
  return next(req);
};
