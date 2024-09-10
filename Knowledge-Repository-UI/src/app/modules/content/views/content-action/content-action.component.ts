import {
  AfterViewInit,
  ChangeDetectorRef,
  Component,
  ElementRef,
  Inject,
  OnDestroy,
  OnInit,
  ViewChild,
} from '@angular/core';
import {
  AbstractControl,
  FormArray,
  FormBuilder,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  ValidationErrors,
  ValidatorFn,
  Validators,
} from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { displayErrorMsg } from '../../../../../constant/constant';
import { CommonModule } from '@angular/common';
import {
  MatDialogRef,
  MAT_DIALOG_DATA,
  MatDialogModule,
} from '@angular/material/dialog';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { TagComponent } from '../../../../Views/tag/tag.component';
import { ContentApiService } from '../../agents/content-api.service';
import { finalize, Observable, Subject, take, takeUntil } from 'rxjs';
import { MatSelectModule } from '@angular/material/select';
import { LoaderService } from '../../../../state/loader.service';
import { MasterStore } from '../../../../state/master.store';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { AutocompleteMultiselectComponent } from '../../../../Views/autocomplete-multiselect/autocomplete-multiselect.component';

@Component({
  selector: 'app-content-action',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    FormsModule,
    MatDialogModule,
    TagComponent,
    MatSelectModule,
    MatProgressSpinnerModule,
    MatAutocompleteModule,
    MatCheckboxModule,
    AutocompleteMultiselectComponent,
  ],
  templateUrl: './content-action.component.html',
  styleUrl: './content-action.component.scss',
})
export class ContentActionComponent
  implements OnInit, OnDestroy, AfterViewInit
{
  constructor(
    private fb: FormBuilder,
    private contentApi: ContentApiService,
    @Inject(MAT_DIALOG_DATA)
    public data: {
      file: File[] | undefined;
      type: 'add' | 'edit';
      onAction: Function;
      id: number;
      formData: any;
    },
    private dialogRef: MatDialogRef<ContentActionComponent>,
    private cdr: ChangeDetectorRef,
    private masterStore: MasterStore,
    private loaderService: LoaderService
  ) {}
  form!: FormGroup;
  private _componentDistroyed = new Subject<void>();
  private trackId: number = 0;
  @ViewChild('textarea')
  summaryElement!: ElementRef;
  fileControlMap: Map<string, File> = new Map();
  industries: string[] = [];
  filteredIndustry: string[] = [];
  documentType$!: Observable<string[]>;
  showLoader: boolean = false;
  updateDisplayIndustry$ = new Subject<void>();

  ngOnInit(): void {
    console.log(this.data.file?.forEach((file) => console.log(file.name)));
    this._setupForm();
    this.documentType$ = this.masterStore.getDocumentType();
    this.masterStore
      .getindustries()
      .pipe(takeUntil(this._componentDistroyed))
      .subscribe((industries: string[]) => {
        this.industries = industries;
      });
    if (this.data.file) {
      this.data.file.forEach((file, index: number) => {
        (this.formArray.controls[index] as FormGroup).controls['file'].setValue(
          file.name
        );
        this._uploadFile(file, index);
      });
    }
    if (this.data.type == 'edit') {
      this._getContributionDetail();
    }
    this._subscribeLoader();
  }

  ngAfterViewInit(): void {
    if (this.data.type == 'edit') {
      this.updateDisplayIndustry$.next();
    }
  }
  ngOnDestroy(): void {
    this._componentDistroyed.next();
    this._componentDistroyed.complete();
  }

  get formArray(): FormArray {
    return this.form.controls['data'] as FormArray;
  }
  getTags(index: number) {
    return <FormArray>this.getFormGroup(index).controls['tags'];
  }

  getFormGroup(groupIndex: number): FormGroup {
    return this.formArray.controls[groupIndex] as FormGroup;
  }
  /**
   * @description this function checks for error and help to make label red
   * @param control
   * @returns
   * @memberof ContentActionComponent
   */
  hasError(control: any, index: number): boolean {
    const formControl = (this.formArray.controls[index] as FormArray).controls[
      control
    ];
    if (formControl.touched && formControl.errors) {
      return true;
    }
    return false;
  }
  errorMsg(formControlName: string, label: string, groupIndex: number): string {
    return displayErrorMsg(
      this.getFormGroup(groupIndex),
      formControlName,
      label
    );
  }

  onFileInput(event: any, groupIndex: number) {
    this.getFormGroup(groupIndex).controls['file'].markAsTouched();
    this.form.updateValueAndValidity();
    if (event.target?.files?.length > 0) {
      if (
        event.target.files[0].type == 'application/pdf' ||
        event.target.files[0].type ==
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      ) {
        this.getFormGroup(groupIndex).controls['file'].setValue(
          event.target.files[0].name
        );
        this.fileControlMap.set(
          this.getFormGroup(groupIndex).controls['id'].value,
          event.target.files[0]
        );
        this._uploadFile(event.target.files[0], groupIndex);
      } else {
        this.getFormGroup(groupIndex).controls['file'].setValue('');
        this.getFormGroup(groupIndex).controls['file'].setErrors({
          extension: ['pdf', 'docx'],
        });
      }
    }
  }
  addTag(input: HTMLInputElement, groupIndex: number) {
    this.getTags(groupIndex).push(this.fb.group({ name: input.value }));
    input.value = '';
  }
  /**
   * @description this function runs when user remove the tag by close button
   * @param id
   * @returns void
   * @memberof ContentActionComponent
   */
  onTagClose(tag: { tag: string; id: number }, groupIndex: number): void {
    this.getTags(groupIndex).removeAt(tag.id);
    this.getFormGroup(groupIndex).controls['tags'].markAsTouched();
    this.getFormGroup(groupIndex).controls['tag'].markAsTouched();
  }

  createCard() {
    this.formArray.push(this._createSubgroup());
  }
  closeCard(cardIndex: number) {
    this.fileControlMap.delete(
      this.getFormGroup(cardIndex).controls['id'].value
    );

    this.formArray.removeAt(cardIndex);
    this.form.updateValueAndValidity();
    this.cdr.detectChanges();
  }

  submit() {
    this.loaderService.showLoader();
    this.contentApi
      .uploadFileDetails(this.form.value, this.fileControlMap)
      .pipe(
        take(1),
        finalize(() => {
          this.loaderService.hideLoader();
        })
      )
      .subscribe({
        next: (Response) => {
          this.data.onAction();
          this.dialogRef.close();
        },
        error: (err) => {
          console.log(err);
        },
      });
  }

  update() {
    this.loaderService.showLoader();
    this.contentApi
      .updateContribution(this.getFormGroup(0).value)
      .pipe(
        take(1),
        finalize(() => {
          this.loaderService.hideLoader();
        })
      )
      .subscribe({
        next: (Response) => {
          this.data.onAction();
          this.dialogRef.close();
        },
        error: (err) => {
          console.log(err);
        },
      });
  }
  close() {
    this.dialogRef.close();
  }

  private _createSubgroup() {
    this.trackId++;
    return this.fb.group(
      {
        id: [this.trackId],
        showSpinner: [0],
        file: ['', [Validators.required]],
        fileName: ['', [Validators.required, Validators.maxLength(200)]],
        fileCategory: [''],
        industry: [new Array()],
        industryDisplay: [''],
        tags: this.fb.array([]),
        documentType: ['', [Validators.required]],
        tag: ['', [Validators.pattern('[\\w\\s]*')]],
        summary: ['', [Validators.required, Validators.maxLength(400)]],
      },
      {
        validators: [this._tagsValidation(), this._industryValidation()],
      }
    );
  }

  private _tagsValidation(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const tagsFormArray = (<FormGroup>control).controls['tags'] as FormArray;
      const tagFormControl = (<FormGroup>control).controls['tag'];
      if (tagFormControl.errors && !tagFormControl.hasError('required')) {
        return null;
      }
      if (!tagsFormArray.controls.length) {
        tagsFormArray.setErrors({ required: true });
        tagFormControl.setErrors({ required: true });
      } else {
        tagsFormArray.setErrors(null);
        tagFormControl.setErrors(null);
      }
      return null;
    };
  }

  private _industryValidation(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      const industryControl = (<FormGroup>control).controls['industry'];
      const industryDisplayControl = (<FormGroup>control).controls[
        'industryDisplay'
      ];
      if (
        industryDisplayControl.errors &&
        !industryDisplayControl.hasError('required')
      ) {
        return null;
      }
      if (!industryControl.value.length) {
        industryControl.setErrors({ required: true });
        industryDisplayControl.setErrors({ required: true });
      } else {
        industryControl.setErrors(null);
        industryDisplayControl.setErrors(null);
      }
      return null;
    };
  }

  private _setupForm() {
    let formArray: FormArray = this.fb.array([this._createSubgroup()]);

    for (let i = 1; i < (this.data.file?.length ?? 0); i++) {
      formArray.push(this._createSubgroup());
    }
    this.form = this.fb.group({
      data: formArray,
    });
    this.formArray.controls.forEach((group) => {
      this.data.file?.length &&
        this.fileControlMap.set(
          group.get('id')?.value,
          this.data.file[Number(group.get('id')?.value) - 1]
        );
    });
  }

  private _uploadFile(file: File, groupIndex: number) {
    this.getFormGroup(groupIndex).controls['showSpinner'].setValue(1);
    this.contentApi
      .uploadFile(file)
      .pipe(take(1))
      .subscribe({
        next: (response) => {
          const fileCategory = file.name.slice(file.name.lastIndexOf('.') + 1);
          const fileName = file.name.slice(0, file.name.lastIndexOf('.'));
          while (this.getTags(groupIndex).length !== 0) {
            this.getTags(groupIndex).removeAt(0);
          }
          response.documents[0].tags.forEach((tag: string) => {
            this.getTags(groupIndex).push(this.fb.group({ name: tag }));
          });

          this.getFormGroup(groupIndex).controls['fileCategory'].setValue(
            fileCategory
          );
          this.getFormGroup(groupIndex).controls['summary'].setValue(
            response.documents[0].summary
          );
          this.getFormGroup(groupIndex).controls['fileName'].setValue(fileName);
          response.documents[0].industry_type.forEach((industry) => {
            if (this.industries.includes(industry)) {
              this.getFormGroup(groupIndex).controls['industry'].setValue([
                ...this.getFormGroup(groupIndex).controls['industry'].value,
                industry,
              ]);
            }
          });

          this.updateDisplayIndustry$.next();
          this.getFormGroup(groupIndex).controls['showSpinner'].setValue(0);
          this.getFormGroup(groupIndex).markAllAsTouched();
        },
        error: (err) => {
          this.getFormGroup(groupIndex).controls['showSpinner'].setValue(0);
          console.log(err);
        },
      });
  }

  private _getContributionDetail() {
    const actualFileName = this.data.formData.name
      .split(' ')
      .filter((val: string) => val.length != 0)
      .join('_');
    console.log(actualFileName);
    this.getFormGroup(0).controls['file'].setValue(
      actualFileName.concat('.', this.data.formData.file_type)
    );
    this.getFormGroup(0).controls['id'].setValue(this.data.formData.id);
    this.getFormGroup(0).controls['fileName'].setValue(this.data.formData.name);
    this.getFormGroup(0).controls['industry'].setValue(
      this.data.formData.industry_output.map(
        (industry: { industry: string }) => industry.industry
      )
    );
    this.getFormGroup(0).controls['fileCategory'].setValue(
      this.data.formData.file_type
    );
    this.getFormGroup(0).controls['documentType'].setValue(
      this.data.formData.document_type_output.document_type
    );
    this.data.formData.tags_output.forEach((tag: any) => {
      this.getTags(0).push(this.fb.group(tag));
    });
    this.getFormGroup(0).controls['summary'].setValue(
      this.data.formData.summary
    );
    this.getFormGroup(0).controls['file'].disable();
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
