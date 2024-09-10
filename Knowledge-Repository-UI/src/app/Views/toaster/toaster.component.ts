import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { ToasterService } from '../../state/toaster.service';
import { ToasterData } from '../../models/model';
import { Subject, takeUntil } from 'rxjs';

@Component({
  selector: 'app-toaster',
  standalone: true,
  imports: [MatButtonModule, MatIconModule],
  templateUrl: './toaster.component.html',
  styleUrl: './toaster.component.scss',
})
export class ToasterComponent implements OnInit {
  constructor(private toasterService: ToasterService) {}
  private _componentDistroyed = new Subject<void>();
  toasterData!: ToasterData[];

  ngOnInit(): void {
    this.toasterService.toasterData$
      .pipe(takeUntil(this._componentDistroyed))
      .subscribe((data) => {
        this.toasterData = data;
      });
  }
  ngOnDestroy(): void {
    this._componentDistroyed.next();
    this._componentDistroyed.complete();
  }

  close(toaster: ToasterData) {
    this.toasterService.closeToaster(toaster);
  }
}
