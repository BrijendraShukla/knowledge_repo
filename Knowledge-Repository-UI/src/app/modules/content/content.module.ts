import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ContentApiService } from './agents/content-api.service';
import { MyContributionStore } from './state/my-contribution.store';

@NgModule({
  declarations: [],
  imports: [CommonModule],
  providers: [ContentApiService, MyContributionStore],
})
export class ContentModule {}
