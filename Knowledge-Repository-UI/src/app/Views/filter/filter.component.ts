import {
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Input,
  OnDestroy,
  OnInit,
  Output,
  ViewChild,
} from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import {
  MatDatepickerModule,
  MatDateRangePicker,
} from '@angular/material/datepicker';
import { provideNativeDateAdapter } from '@angular/material/core';
import { MatIconModule } from '@angular/material/icon';
import {
  BehaviorSubject,
  debounceTime,
  distinctUntilChanged,
  Observable,
  startWith,
  Subject,
  takeUntil,
} from 'rxjs';
import { MasterStore } from '../../state/master.store';
import { CommonModule } from '@angular/common';
import {
  MatCheckboxChange,
  MatCheckboxModule,
} from '@angular/material/checkbox';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { AutocompleteMultiselectComponent } from '../autocomplete-multiselect/autocomplete-multiselect.component';

@Component({
  selector: 'app-filter',
  standalone: true,
  imports: [
    MatButtonModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatDatepickerModule,
    MatIconModule,
    CommonModule,
    MatAutocompleteModule,
    MatCheckboxModule,
    AutocompleteMultiselectComponent,
  ],
  providers: [provideNativeDateAdapter()],
  templateUrl: './filter.component.html',
  styleUrl: './filter.component.scss',
})
export class FilterComponent implements OnInit, OnDestroy {
  constructor(
    private fb: FormBuilder,
    private cdr: ChangeDetectorRef,
    private masterStore: MasterStore
  ) {}

  private _componentDistroyed = new Subject<void>();
  form!: FormGroup;
  showCalander: boolean = false;
  @Input() tags: boolean = false;
  @Input() enableReset: BehaviorSubject<boolean> = new BehaviorSubject(false);
  @Output() formAction: EventEmitter<any> = new EventEmitter();
  @ViewChild('picker') picker!: MatDateRangePicker<any>;
  disableFilterButton: boolean = true;
  resetButtonClicked: boolean = false;
  previousSelectedDateRange: {
    date_range_after: Date;
    date_range_before: Date;
  }[] = [];
  industries!: string[];
  filteredIndustry: string[] = [];
  documentType$!: Observable<string[]>;
  fileTypes$!: Observable<string[]>;

  ngOnInit(): void {
    this.documentType$ = this.masterStore.getDocumentType();
    this.masterStore
      .getindustries()
      .pipe(takeUntil(this._componentDistroyed))
      .subscribe((industries: string[]) => {
        this.industries = industries;
      });
    this.fileTypes$ = this.masterStore.getfileType();
    this._setUpForm();
    if (this.tags) {
      this.form.addControl('tags', this.fb.control(null));
    }
    this.enableReset
      .pipe(takeUntil(this._componentDistroyed))
      .subscribe((value) => {
        this.disableFilterButton = !value;
        this.cdr.detectChanges();
      });
    this._subscribeFormChange();
  }
  ngOnDestroy(): void {
    this._componentDistroyed.next();
    this._componentDistroyed.complete();
  }
  get fromDateControl() {
    return this.form.controls['date_range_after'];
  }
  get toDateControl() {
    return this.form.controls['date_range_before'];
  }

  addTag(tag: HTMLInputElement) {
    this.form.controls['tags'].setValue([tag.value]);
    tag.value = '';
  }
  onPickerClosed() {
    if (
      this.fromDateControl.value == null ||
      this.toDateControl.value == null ||
      this.fromDateControl.value == 'Invalid Date' ||
      this.toDateControl.value == 'Invalid Date'
    ) {
      this.fromDateControl.setValue(null);
      this.toDateControl.setValue(null);
      this.form.controls['date'].setValue(null);
    } else {
      this.previousSelectedDateRange.push({
        date_range_after: this.fromDateControl.value,
        date_range_before: this.toDateControl.value,
      });
      this.form.controls['date'].setValue(
        this.fromDateControl.value.toLocaleDateString() +
          '-' +
          this.toDateControl.value.toLocaleDateString()
      );
    }
    this.showCalander = false;
  }

  dateSelect(event: string) {
    const currentDate = new Date();
    switch (event) {
      case 'last week':
        this.toDateControl.setValue(currentDate);
        this.fromDateControl.setValue(
          new Date(currentDate.getTime() - 7 * 24 * 60 * 60 * 1000)
        );
        break;
      case 'last month':
        this.toDateControl.setValue(currentDate);
        // Get the current month and year
        let currentMonth = currentDate.getMonth();
        let currentYear = currentDate.getFullYear();

        // Calculate 1 month ago
        let oneMonthAgoMonth = currentMonth - 1;
        let oneMonthAgoYear = currentYear;

        if (oneMonthAgoMonth < 0) {
          // If the previous month is in the previous year
          oneMonthAgoMonth = 11; // December (0-based index)
          oneMonthAgoYear = currentYear - 1;
        }

        // Get the number of days in the previous month
        let daysInPreviousMonth = new Date(
          oneMonthAgoYear,
          oneMonthAgoMonth + 1,
          0
        ).getDate();

        // Create the date 1 month ago
        this.fromDateControl.setValue(
          new Date(
            oneMonthAgoYear,
            oneMonthAgoMonth,
            Math.min(currentDate.getDate(), daysInPreviousMonth)
          )
        );

        break;
      case 'custom':
        break;
      default:
        let [date_range_after, date_range_before] = event.split('-');
        this.fromDateControl.setValue(new Date(date_range_after));
        this.toDateControl.setValue(new Date(date_range_before));
        this.form.updateValueAndValidity();
    }
  }

  private _setUpForm() {
    this.form = this.fb.group({
      date: [null],
      date_range_after: [null],
      date_range_before: [null],
      file_type: [null],
      industry: [null],
      industryDisplay: [null],
      document_type: [null],
    });
  }
  resetFilter() {
    this.form.reset();
    this.resetButtonClicked = true;
  }

  disableReset() {
    return (
      !this.form.controls['date_range_after'].value &&
      !this.form.controls['date_range_before'].value &&
      !this.form.controls['file_type'].value &&
      !this.form.controls['industry'].value &&
      !this.form.controls['document_type'].value &&
      !this.form.controls['tags']?.value &&
      this.disableFilterButton
    );
  }

  private _subscribeFormChange() {
    this.form.valueChanges
      .pipe(
        takeUntil(this._componentDistroyed),
        startWith({}),
        debounceTime(200),
        distinctUntilChanged((pre: any, current: any) => {
          if (
            pre.date_range_after == current.date_range_after &&
            pre.date_range_before == current.date_range_before &&
            pre.file_type == current.file_type &&
            pre.industry == current.industry &&
            pre.document_type == current.document_type &&
            pre.date == current.date &&
            pre.tags == current.tags &&
            !this.resetButtonClicked
          ) {
            return true;
          }

          return false;
        })
      )
      .subscribe((value) => {
        this.enableReset.next(false);
        this.resetButtonClicked = false;
        if (value.date == 'Custom') {
          this.showCalander = true;
          this.cdr.detectChanges();
          this.picker.open();
        } else if (this.form.valid && Object.keys(value).length > 0) {
          const { date, industryDisplay, ...filterData } = value;
          filterData.date_range_before?.setHours(new Date().getHours());
          filterData.date_range_before?.setMinutes(new Date().getMinutes());
          filterData.date_range_before?.setSeconds(new Date().getSeconds());
          filterData.date_range_after?.setHours(new Date().getHours());
          filterData.date_range_after?.setMinutes(new Date().getMinutes());
          filterData.date_range_after?.setSeconds(new Date().getSeconds());
          filterData.date_range_before = filterData.date_range_before
            ?.toISOString()
            .split('T')[0];
          filterData.date_range_after = filterData.date_range_after
            ?.toISOString()
            .split('T')[0];

          this.formAction.emit(filterData);
        }
      });
  }
}
