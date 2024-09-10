import { Component, Input, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { Router } from '@angular/router';
import { Observable, Subject, takeUntil } from 'rxjs';
import { UserStore } from '../../state/user.store';

@Component({
  selector: 'app-sidenav',
  standalone: true,
  imports: [MatButtonModule],
  host: {
    '[class.hide-sidenav]': 'hideSideNav',
    '[class.show-sidenav]': '!hideSideNav',
  },
  templateUrl: './sidenav.component.html',
  styleUrl: './sidenav.component.scss',
})
export class SidenavComponent implements OnInit, OnDestroy {
  constructor(private router: Router, private userStore: UserStore) {}
  private _componentDistroyed = new Subject<void>();

  @Input() activeUrl!: string;
  hideSideNav!: boolean;

  ngOnInit(): void {
    this.userStore.showSideNav$
      .pipe(takeUntil(this._componentDistroyed))
      .subscribe((value) => {
        this.hideSideNav = !value;
        if (value) {
          document.documentElement.style.setProperty(
            'overflow',
            'hidden',
            'important'
          );
        } else {
          document.documentElement.style.setProperty(
            'overflow',
            'visible',
            'important'
          );
        }
      });
  }

  ngOnDestroy(): void {
    this._componentDistroyed.next();
    this._componentDistroyed.complete();
  }
  redirect(url: string) {
    this.router.navigateByUrl(url);
    this.userStore.showSideNav$.next(false);
  }
}
