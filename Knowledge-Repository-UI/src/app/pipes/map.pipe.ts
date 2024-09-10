import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'map',
  standalone: true,
})
export class MapPipe implements PipeTransform {
  transform(value: { [key: string]: string }[], arg: string): string[] {
    return value.map((value) => value[arg]);
  }
}
