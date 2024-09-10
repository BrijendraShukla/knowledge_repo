import { Component, Input, OnDestroy, OnInit } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatToolbarModule } from '@angular/material/toolbar';

import { NavigationEnd, Router } from '@angular/router';
import { Subject, pipe, takeUntil } from 'rxjs';
import { CommonModule } from '@angular/common';
import { UserStore } from '../../state/user.store';
import { USER } from '../../../constant/constant';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [MatToolbarModule, MatButtonModule, MatIconModule, CommonModule],
  templateUrl: './header.component.html',
  styleUrl: './header.component.scss',
})
export class HeaderComponent implements OnInit, OnDestroy {
  constructor(private userStore: UserStore, private router: Router) {}
  private _componentDistroyed = new Subject<void>();
  user!: { id: number; email: string; token: string; name: string };
  src = 'profile.jpg'; //this need to change
  initials!: string;
  isLogin!: boolean;
  showInitials: boolean = false;
  @Input() activeUrl!: string;

  ngOnInit(): void {
    this.userStore.user$
      .pipe(pipe(takeUntil(this._componentDistroyed)))
      .subscribe((user) => {
        this.user = user;
        if (user.token) {
          this.isLogin = true;
        } else {
          this.isLogin = localStorage.getItem(USER.IS_LOGIN) ? true : false;
        }
        const nameArray = user.name.split(' ');
        this.initials =
          nameArray[0].toUpperCase().charAt(0) +
          nameArray[1].toUpperCase().charAt(0);
      });
  }

  ngOnDestroy(): void {
    this._componentDistroyed.next();
    this._componentDistroyed.complete();
  }

  toggleSideNav() {
    this.userStore.showSideNav$.next(!this.userStore.showSideNav$.value);
  }

  redirect(url: string) {
    this.router.navigateByUrl(url);
  }
}
