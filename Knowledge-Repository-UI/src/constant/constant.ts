import { AbstractControl, FormGroup } from '@angular/forms';
import { environment } from '../environments/environment';

export const displayErrorMsg = (
  formGroup: FormGroup,
  formControlName: string,
  label: string
): string => {
  const formControl: AbstractControl = formGroup.controls[formControlName];
  for (let error in formControl.errors) {
    switch (error) {
      case 'required':
        return `${label} is a required field`;
      case 'minlength':
        return `minimum ${formControl.errors[error].requiredLength} character allowed`;
      case 'maxlength':
        return `maximum ${formControl.errors[error].requiredLength} character allowed`;
      case 'extension':
        let errString: string = '';
        formControl.errors[error].forEach((val: string) => {
          errString = errString + val + ' ';
        });
        return `only ${errString.trim()} extension allowed`;
      case 'pattern':
        return 'special characters are not allowed';
    }
  }
  return '';
};

export const createBaseUrl = (baseEndpoint?: string): string => {
  return baseEndpoint
    ? environment.baseAPIUrl + '/' + baseEndpoint + '/'
    : environment.baseAPIUrl + '/';
};
export const createUrl = (baseUrl: string, endpoint: string) =>
  baseUrl + endpoint + '/';

export const USER = {
  IS_LOGIN: 'isLogin',
  TOKEN: 'token',
  NAME: 'name',
};

export const TOASTER_TYPE = {
  SUCCESS: 'success',
  ERROR: 'error',
};
