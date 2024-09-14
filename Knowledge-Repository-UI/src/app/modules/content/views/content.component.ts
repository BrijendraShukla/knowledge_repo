import {
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
  TemplateRef,
  ViewChild,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import {
  MatDialog,
  MatDialogModule,
  MatDialogRef,
} from '@angular/material/dialog';
import { MatTableModule } from '@angular/material/table';
import { ContentActionComponent } from './content-action/content-action.component';
import { FilterComponent } from '../../../Views/filter/filter.component';
import { ContentApiService } from '../agents/content-api.service';
import { MyContributionStore } from '../state/my-contribution.store';
import {
  delay,
  distinctUntilChanged,
  fromEvent,
  Observable,
  Subject,
  take,
  takeUntil,
} from 'rxjs';
import { PageEvent, MatPaginatorModule } from '@angular/material/paginator';
import {
  myContribution,
  myContributionData,
  myContributionPayload,
} from '../models/content.model';
import { CommonModule } from '@angular/common';
import { LoaderService } from '../../../state/loader.service';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MapPipe } from '../../../pipes/map.pipe';
import { TagColumnDirective } from '../../../directives/tag-column.directive';

@Component({
  selector: 'app-content',
  standalone: true,
  imports: [
    MatButtonModule,
    MatIconModule,
    MatDialogModule,
    MatTableModule,
    FilterComponent,
    CommonModule,
    MatTooltipModule,
    MapPipe,
    TagColumnDirective,
  ],

  templateUrl: './content.component.html',
  styleUrl: './content.component.scss',
})
export class ContentComponent implements OnInit, OnDestroy {
  constructor(
    private matDialog: MatDialog,
    private contributionStore: MyContributionStore,
    private contentApi: ContentApiService,
    private loaderService: LoaderService,
    private cdr: ChangeDetectorRef
  ) {}

  data!: myContributionData;
  @ViewChild('thanksForUploading')
  thanksTempletRef!: TemplateRef<any>;
  @ViewChild('confirmDelete')
  confirmDeleteTempleteRef!: TemplateRef<any>;
  confirmDialogRef!: MatDialogRef<any>;

  displayedColumns = [
    'fileName',
    'industry',
    'fileType',
    'tags',
    'date',
    'action',
  ];
  private _componentDistroyed = new Subject<void>();
  aboutToDeleteContribution: number | null = null;
  toDeleteContribution: myContribution | null = null;
  inputFiles = document.createElement('input');
  private browseButtonClicked!: Observable<any>;

  ngOnInit(): void {
    this.inputFiles.setAttribute('type', 'file');
    this.inputFiles.setAttribute('multiple', 'multiple');
    this.inputFiles.setAttribute('accept', '.pdf , .docx');
    this.browseButtonClicked = fromEvent(this.inputFiles, 'change');
    this._subscribeToBrowse();
    this._subscribePayloadChange();
    this._subscribeDataChange();
  }

  ngOnDestroy(): void {
    this._componentDistroyed.next();
    this._componentDistroyed.complete();
    this.contributionStore.resetToInitialState();
  }
  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    if (event.dataTransfer?.files && event.dataTransfer?.files.length > 0) {
      this.openAddContent(Array.from(event.dataTransfer.files));
    }
  }
  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
  }
  openAddContent(file?: File[]) {
    this.matDialog.open(ContentActionComponent, {
      disableClose: true,
      panelClass: 'dialog',
      height: '726px',
      width: '960px',
      data: {
        file,
        type: 'add',
        onAction: () => {
          const thanksTempletRef = this.matDialog.open(this.thanksTempletRef, {
            panelClass: 'dialog',
            width: '960px',
            height: '383px',
          });
          thanksTempletRef
            .afterOpened()
            .pipe(take(1))
            .subscribe(() => {
              setTimeout(() => {
                thanksTempletRef.close();
              }, 5000);
            });
          this.contributionStore.getContributionDataFromApi();
        },
      },
    });
  }

  onFilter(value: any) {
    this.contributionStore.setPayload(value);
  }
  editContribution(data: any) {
    console.log(data);
    this.matDialog.open(ContentActionComponent, {
      disableClose: true,
      panelClass: 'dialog',
      height: '726px',
      width: '960px',
      data: {
        type: 'edit',
        id: data.id,
        formData: data,
        onAction: () => {
          this.contributionStore.updateListFromApi();
        },
      },
    });
  }

  openConfirmDelete(data: myContribution) {
    this.confirmDialogRef = this.matDialog.open(this.confirmDeleteTempleteRef, {
      panelClass: 'dialog',
      width: '960px',
      height: '383px',
    });
    this.toDeleteContribution = data;
  }
  cancelDelete() {
    this.confirmDialogRef.close();
    this.aboutToDeleteContribution = null;
  }
  deleteContribution() {
    this.confirmDialogRef.close();
    this.aboutToDeleteContribution = this.toDeleteContribution!.id;
    this.contentApi
      .deleteContribution(this.toDeleteContribution!.id)
      .pipe(take(1), delay(500))
      .subscribe({
        next: (response) => {
          this.aboutToDeleteContribution = null;
          this.contributionStore.updateListFromApi();
        },
        error: (err) => {
          this.aboutToDeleteContribution = null;
        },
      });
  }

  loadNext() {
    this.contributionStore.getNextPage();
  }

  private _subscribeToBrowse() {
    this.browseButtonClicked
      .pipe(takeUntil(this._componentDistroyed))
      .subscribe((event) => {
        console.log(event.target?.files?.length);
        if (event.target?.files && event.target?.files?.length > 0) {
          this.openAddContent(Array.from(event.target.files));
        }
        event.target.value = '';
      });
  }

  private _subscribeDataChange() {
    this.contributionStore.myContributionData$
      .pipe(takeUntil(this._componentDistroyed))
      .subscribe((data) => {
        this.loaderService.hideLoader();
        this.data = data;
        this.cdr.detectChanges();
      });
  }

  private _subscribePayloadChange() {
    this.contributionStore.payload$
      .pipe(
        takeUntil(this._componentDistroyed),
        distinctUntilChanged(
          (pre: myContributionPayload, current: myContributionPayload) => {
            if (
              pre.date_range_after == current.date_range_after &&
              pre.date_range_before == current.date_range_before &&
              pre.file_type == current.file_type &&
              pre.industry == current.industry &&
              pre.document_type == current.document_type
            ) {
              return true;
            }
            return false;
          }
        )
      )
      .subscribe((value) => {
        this.loaderService.showLoader();
        this.contributionStore.getContributionDataFromApi();
      });
  }
}
