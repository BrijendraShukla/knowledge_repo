import { Routes } from '@angular/router';
import { LoginComponent } from './Views/login/login.component';
import { authGuard } from './guards/auth.guard';
import { SearchComponent } from './modules/home/views/search.component';
import { ContentComponent } from './modules/content/views/content.component';

export const routes: Routes = [
  {
    path: '',
    component: SearchComponent,
    canActivate: [authGuard],
  },
  {
    path: 'login',
    component: LoginComponent,
  },
  {
    path: 'content',
    component: ContentComponent,
    canActivate: [authGuard],
  },
];
