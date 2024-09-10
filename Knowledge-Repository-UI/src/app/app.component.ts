import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { LoginComponent } from './Views/login/login.component';
import { HeaderComponent } from './Views/header/header.component';
import { ToasterComponent } from './Views/toaster/toaster.component';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatIconRegistry } from '@angular/material/icon';
import { DomSanitizer } from '@angular/platform-browser';
import { LoaderService } from './state/loader.service';
import { BehaviorSubject, Subject, takeUntil } from 'rxjs';
import { USER } from '../constant/constant';
import { SidenavComponent } from './Views/sidenav/sidenav.component';
import { UserStore } from './state/user.store';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet,
    CommonModule,
    LoginComponent,
    HeaderComponent,
    ToasterComponent,
    MatProgressSpinnerModule,
    SidenavComponent,
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent implements OnInit, OnDestroy {
  constructor(
    private matIconRegistry: MatIconRegistry,
    private domSanitizer: DomSanitizer,
    private loaderService: LoaderService,
    private router: Router,
    public userStore: UserStore
  ) {
    this.matIconRegistry.addSvgIconSet(
      this.domSanitizer.bypassSecurityTrustResourceUrl('assets/images.svg')
    );
  }
  showLoader!: boolean;
  activeUrl!: string;
  private _componentDistroyed = new Subject<void>();

  ngOnInit(): void {
    this.router.events
      .pipe(takeUntil(this._componentDistroyed))
      .subscribe((event) => {
        if (event instanceof NavigationEnd) {
          this.activeUrl = event.url;
        }
      });
    localStorage.setItem(USER.IS_LOGIN, 'true');
    localStorage.setItem(USER.TOKEN, 'temp token'); // need to remove this after login implementation
    this._subscribeLoader();
  }
  ngOnDestroy(): void {
    this._componentDistroyed.next();
    this._componentDistroyed.complete();
  }

  hideSideNav() {
    if (this.userStore.showSideNav$.value) {
      this.userStore.showSideNav$.next(false);
    }
  }
  private _subscribeLoader() {
    this.loaderService.showLoader$
      .pipe(takeUntil(this._componentDistroyed))
      .subscribe((value: boolean) => {
        if (value) {
          document.body.style.setProperty('overflow', 'hidden');
        } else {
          document.body.style.setProperty('overflow', 'auto');
        }
        this.showLoader = value;
      });
  }
}
