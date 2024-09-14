import { Directive, ElementRef, Input, OnDestroy, OnInit } from '@angular/core';
import { fromEvent, Subscription } from 'rxjs';

@Directive({
  selector: '[appTagColumn]',
  standalone: true,
})
export class TagColumnDirective implements OnInit, OnDestroy {
  constructor(private elRef: ElementRef) {}

  nativeElement!: HTMLElement;
  reSizeSubscription!: Subscription;
  @Input({ required: true }) tags!: string[];

  ngOnInit(): void {
    this.nativeElement = this.elRef.nativeElement;
    this.reSizeSubscription = fromEvent(window, 'resize').subscribe(() => {
      this.setTags();
    });
    setTimeout(() => {
      this.setTags();
    }, 0);
  }

  ngOnDestroy(): void {
    this.reSizeSubscription.unsubscribe();
  }

  setTags() {
    this.nativeElement.replaceChildren();
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
  }
}
