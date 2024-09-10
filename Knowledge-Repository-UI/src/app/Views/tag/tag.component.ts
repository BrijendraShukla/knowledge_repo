import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-tag',
  standalone: true,
  imports: [MatIconModule, MatButtonModule],
  templateUrl: './tag.component.html',
  styleUrl: './tag.component.scss',
})
export class TagComponent {
  @Input() name!: string;
  @Input() id!: number;
  @Output() close: EventEmitter<{ tag: string; id: number }> =
    new EventEmitter();
  closeHost() {
    this.close.emit({ tag: this.name, id: this.id });
  }
}
