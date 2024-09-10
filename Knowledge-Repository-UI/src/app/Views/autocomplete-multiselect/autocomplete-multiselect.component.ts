import { CommonModule } from '@angular/common';
import {
  ChangeDetectorRef,
  Component,
  Input,
  input,
  OnInit,
} from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import {
  MatCheckboxChange,
  MatCheckboxModule,
} from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { displayErrorMsg } from '../../../constant/constant';
import { Observable, Subject, takeUntil } from 'rxjs';

@Component({
  selector: 'app-autocomplete-multiselect',
  standalone: true,
  imports: [
    CommonModule,
    MatAutocompleteModule,
    MatCheckboxModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
  ],
  templateUrl: './autocomplete-multiselect.component.html',
  styleUrl: './autocomplete-multiselect.component.scss',
})
export class AutocompleteMultiselectComponent implements OnInit {
  @Input({ required: true }) formGroup!: FormGroup;

  @Input({ required: true }) list!: string[];
  @Input({ required: true }) displayControlName!: string;
  @Input({ required: true }) actualControlName!: string;
  @Input({ required: true }) placeHolder!: string;
  @Input() label!: string;
  @Input() selection: { required: boolean; limit: number } = {
    required: false,
    limit: 0,
  };
  @Input() required: boolean = false; //to show the * sign
  @Input() showLabel: boolean = true;
  @Input() showError: boolean = true;
  @Input() updateDisplay?: Observable<void>;
  displayControl!: FormControl;
  actualControl!: FormControl;
  filteredList: string[] = [];
  private _componentDistroyed = new Subject<void>();

  ngOnInit(): void {
    this.displayControl = this.formGroup.controls[
      this.displayControlName
    ] as FormControl;
    this.actualControl = this.formGroup.controls[
      this.actualControlName
    ] as FormControl;

    this.updateDisplay?.subscribe(() => {
      this.autocompleteClose('blur');
    });
  }

  ngOnDestroy(): void {
    this._componentDistroyed.next();
    this._componentDistroyed.complete();
  }
  hasError(): boolean {
    if (this.displayControl.touched && this.displayControl.errors) {
      return true;
    }
    return false;
  }
  errorMsg(): string {
    return displayErrorMsg(
      this.formGroup,
      this.displayControlName,
      this.label!
    );
  }

  toggleIndustrySelection(value: string, event: MatCheckboxChange) {
    if (event.checked) {
      this.actualControl.setValue([
        ...((this.actualControl.value as string[])?.length
          ? (this.actualControl.value as string[])
          : []),
        value,
      ]);
    } else {
      this.actualControl.setValue(
        (this.actualControl.value as string[])?.filter((val) => val != value)
      );
    }
  }
  industryFilter(type: string) {
    if (type == 'focus' && !this.filteredList.length) {
      this.displayControl.setValue('');
    }

    const value = this.displayControl.value?.toLocaleLowerCase() || '';
    this.filteredList = this.list.filter((val) =>
      val.toLowerCase().includes(value)
    );
  }

  isChecked(value: string): boolean {
    if ((this.actualControl.value as string[])?.includes(value)) {
      return true;
    }
    return false;
  }

  autocompleteClose(type: 'blur' | 'close') {
    if (
      (type == 'close' && this.filteredList.length) ||
      (type == 'blur' && !this.filteredList.length)
    ) {
      this.displayControl.setValue(
        (this.actualControl.value as string[])?.join(', ')
      );
      this.filteredList = [];
    }
  }
}
