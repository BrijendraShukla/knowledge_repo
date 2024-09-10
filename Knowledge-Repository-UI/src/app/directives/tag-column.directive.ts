import {
  AfterViewInit,
  Directive,
  ElementRef,
  Input,
  OnInit,
} from '@angular/core';

@Directive({
  selector: '[appTagColumn]',
  standalone: true,
})
export class TagColumnDirective implements OnInit {
  constructor(private elRef: ElementRef) {}

  nativeElement!: HTMLElement;
  @Input({ required: true }) tags!: string[];

  ngOnInit(): void {
    this.nativeElement = this.elRef.nativeElement;
    setTimeout(() => {
      for (let i = 0; i < this.tags.length; i++) {
        const div = document.createElement('div');
        div.textContent = this.tags[i];
        div.setAttribute('class', 'tag');
        this.nativeElement.appendChild(div);
        if (this.nativeElement.scrollWidth > this.nativeElement.clientWidth) {
          const overflowDiv = document.createElement('div');
          overflowDiv.setAttribute('class', 'more');
          overflowDiv.textContent = '...';
          this.nativeElement.removeChild(div);
          this.nativeElement.appendChild(overflowDiv);

          break;
        }
      }
    }, 0);
  }
}
