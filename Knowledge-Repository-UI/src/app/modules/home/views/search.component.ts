import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import {
  distinctUntilChanged,
  Subject,
  take,
  takeUntil,
  timeInterval,
} from 'rxjs';
import { FilterComponent } from '../../../Views/filter/filter.component';
import {
  MatCheckboxChange,
  MatCheckboxModule,
} from '@angular/material/checkbox';

import {
  SearchPayload,
  SearchResultData,
  SearchResultResponse,
} from '../models/search.model';
import { SearchStore } from '../state/search.store';
import { TagComponent } from '../../../Views/tag/tag.component';
import { CommonModule } from '@angular/common';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { SearchApiService } from '../agents/search-api.service';
import { DocumentViewComponent } from '../../../Views/document-view/document-view.component';
import { ToasterService } from '../../../state/toaster.service';

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
    MatButtonModule,
    FormsModule,
    FilterComponent,
    FilterComponent,
    TagComponent,
    MatCheckboxModule,
    CommonModule,
  ],
  templateUrl: './search.component.html',
  styleUrl: './search.component.scss',
})
export class SearchComponent implements OnInit {
  constructor(
    private store: SearchStore,
    private matDialog: MatDialog,
    private searchAPI: SearchApiService,
    private toaster: ToasterService
  ) {}
  private _componentDistroyed = new Subject<void>();
  apiResponseData?: SearchResultResponse;
  searchValue: string = '';
  searchDone: boolean = false;
  showAnimation: boolean = true;
  resultList!: SearchResultData[];
  checkedData: number[] = [];
  showMain: boolean = false;
  showMainAnimation: boolean = true;
  tagList!: string[];
  detailsData!: SearchResultData;
  @ViewChild('detailsTemplate')
  detailTemplate!: TemplateRef<any>;
  detailRef?: MatDialogRef<any>;

  ngOnInit(): void {
    this.searchValue = this.store.getSearchTerm();
    if (this.searchValue) {
      this.searchDone = true;
      this.showAnimation = false;
      this.showMainAnimation = false;
      this.showMain = true;
    }
    this._subscribePayloadChange();
    this._subscribeTagChange();
    this._subscribeDataChange();
  }
  ngOnDestroy(): void {
    this._componentDistroyed.next();
    this._componentDistroyed.complete();
  }

  search(event: Event) {
    event.preventDefault();
    this.store.setPayload({ query: this.searchValue });
    this.checkedData = [];
    this.searchDone = true;
    setTimeout(() => {
      this.showMain = true;
    }, 800);
  }

  onFilter(value: any) {
    console.log(value);
    if (value.tags?.length > 0) {
      value.generate_tag = false;
    }
    this.store.setPayload(value);
  }

  onCheckChange(event: MatCheckboxChange, id: number) {
    if (event.checked) {
      this.checkedData.push(id);
    } else {
      this.checkedData = this.checkedData.filter(
        (checkedId) => checkedId != id
      );
    }
    console.log(this.checkedData);
  }

  onTagClose(event: { tag: string; id: number }) {
    this.store.removeTag(event.tag);
  }

  openDetailDialog(fileData: SearchResultData) {
    this.detailsData = fileData;
    this.detailRef = this.matDialog.open(this.detailTemplate, {
      panelClass: 'dialog',
      width: '960px',
      height: '443px',
    });
  }

  viewDownloadDocument(type: 'view' | 'download') {
    this.searchAPI
      .getFile(this.detailsData.id)
      .pipe(take(1))
      .subscribe((response) => {
        this.detailRef?.close();
        console.log(response.body);
        const fileUrl = window.URL.createObjectURL(response.body!);
        if (type == 'view') {
          this.matDialog.open(DocumentViewComponent, {
            panelClass: 'dialog',
            width: '960px',
            data: {
              fileUrl,
            },
          });
        } else {
          const link = document.createElement('a');
          link.setAttribute('href', fileUrl);
          link.setAttribute('download', this.detailsData.name);
          link.click();
          this.toaster.showToater({
            msg: `${this.detailsData.name} downloaded successfully`,
            type: 'success',
          });
          // window.open(url, '_blank');
        }
      });
  }

  downloadAll() {
    this.searchAPI
      .getFilesInZip(this.checkedData)
      .pipe(take(1))
      .subscribe((response) => {
        console.log(response.headers.keys());
        const fileUrl = window.URL.createObjectURL(
          new Blob([response.body!], { type: response.body?.type })
        );
        const link = document.createElement('a');

        link.setAttribute('href', fileUrl);
        if (this.checkedData.length == 1) {
          const selectedFile = this.apiResponseData!.results.find(
            (data) => data.id == this.checkedData[0]
          );
          link.setAttribute(
            'download',
            selectedFile!.name + '.' + selectedFile!.file_type
          );
        } else {
          link.setAttribute('download', 'KR_files.zip');
        }
        link.click();
        this.toaster.showToater({
          msg: `Download successfully`,
          type: 'success',
        });
      });
  }

  private _subscribeTagChange() {
    this.store.tagList$
      .pipe(takeUntil(this._componentDistroyed))
      .subscribe((tags) => {
        this.tagList = tags;
      });
  }

  private _subscribeDataChange() {
    this.store.searchResultData$
      .pipe(takeUntil(this._componentDistroyed))
      .subscribe((data) => {
        this.apiResponseData = data;
        this.store.setPayload({ tags: data.tags });
      });
  }

  private _compareTags(
    tag1: string[] | null | undefined,
    tag2: string[] | null | undefined
  ): boolean {
    if (tag1 && tag2) {
      for (let i = 0; i < tag1.length; i++) {
        if (!tag2.includes(tag1[i])) {
          return false;
        }
      }
      if (tag1.length == tag2.length) {
        return true;
      }

      for (let i = 0; i < tag2.length; i++) {
        if (!tag1.includes(tag2[i])) {
          return false;
        }
      }
      return true;
    }
    if (tag1 == tag2) {
      return true;
    }
    return false;
  }

  private _subscribePayloadChange() {
    this.store.payload$
      .pipe(
        takeUntil(this._componentDistroyed),
        distinctUntilChanged((pre: SearchPayload, current: SearchPayload) => {
          if (
            pre.date_range_after == current.date_range_after &&
            pre.date_range_before == current.date_range_before &&
            pre.file_type == current.file_type &&
            pre.industry == current.industry &&
            pre.query == current.query &&
            pre.document_type == current.document_type &&
            (this._compareTags(pre.tags, current.tags) ||
              this._compareTags(current.tags, this.apiResponseData?.tags))
            // pre.pageNumber == current.pageNumber &&
            // pre.pageSize == current.pageSize
          ) {
            return true;
          }

          return false;
        })
      )
      .subscribe((value) => {
        if (value.query.trim().length > 0) {
          this.store.getSearchDataFromApi();
        }
      });
  }
}
