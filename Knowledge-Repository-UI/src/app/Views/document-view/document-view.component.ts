import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { NgxDocViewerModule } from 'ngx-doc-viewer';

@Component({
  selector: 'app-document-view',
  standalone: true,
  imports: [NgxDocViewerModule],
  templateUrl: './document-view.component.html',
  styleUrl: './document-view.component.scss',
})
export class DocumentViewComponent implements OnInit {
  constructor(
    @Inject(MAT_DIALOG_DATA)
    public data: {
      fileUrl: string;
    }
  ) {}

  ngOnInit(): void {
    // window.open(this.data.fileUrl);
  }
}
