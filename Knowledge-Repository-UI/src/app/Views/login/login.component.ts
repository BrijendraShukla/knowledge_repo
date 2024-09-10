import {
  ChangeDetectionStrategy,
  Component,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { LoginApiService } from '../../agents/login-api.service';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { Router } from '@angular/router';
import { UserStore } from '../../state/user.store';
import { MatButton, MatButtonModule } from '@angular/material/button';
import {
  MatIcon,
  MatIconModule,
  MatIconRegistry,
} from '@angular/material/icon';
import { CommonModule } from '@angular/common';
import { Subject, catchError, of, takeUntil } from 'rxjs';
import {
  TOASTER_TYPE,
  USER,
  displayErrorMsg,
} from '../../../constant/constant';
import { ToasterService } from '../../state/toaster.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatIconModule,
    ReactiveFormsModule,
  ],
  providers: [LoginApiService],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
})
export class LoginComponent implements OnInit, OnDestroy {
  constructor(
    private loginService: LoginApiService,
    private userStore: UserStore,
    private fb: FormBuilder,
    private router: Router,
    private toasterService: ToasterService
  ) {
    if (localStorage.getItem(USER.IS_LOGIN)) {
      router.navigate(['/']);
    }
  }
  private _componentDistroyed = new Subject<void>();
  form!: FormGroup<any>;
  showPassword: boolean = false;
  loginFail: boolean = false;
  ngOnInit(): void {
    this._setUpForm();
  }
  ngOnDestroy(): void {
    this._componentDistroyed.next();
    this._componentDistroyed.complete();
  }

  logIn() {
    this.loginService
      .getAuth(this.form.value)
      .pipe(takeUntil(this._componentDistroyed))
      .subscribe({
        next: (val) => {
          console.log(val);
          this.userStore.setUser({ token: val.token, ...val.user });
          localStorage.setItem(USER.TOKEN, val.token);
          localStorage.setItem(USER.IS_LOGIN, 'true');
          // localStorage.setItem(USER.NAME, val.user.name);
          this.toasterService.showToater({
            msg: 'LogIn Success',
            type: TOASTER_TYPE.SUCCESS,
          });

          this.router.navigate(['/']);
        },
        error: (error) => {
          this.loginFail = true;
        },
      });
  }

  hasError(control: 'username' | 'password'): boolean {
    const formControl = this.form.controls[control];
    if (formControl.touched && formControl.errors) {
      return true;
    }
    return false;
  }
  errorMsg(formControlName: string, label: string) {
    return displayErrorMsg(this.form, formControlName, label);
  }
  private _setUpForm() {
    this.form = this.fb.group({
      username: ['', [Validators.required, Validators.minLength(3)]],
      password: ['', [Validators.required, Validators.minLength(3)]],
    });
  }
}
