import { Component } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'app-upload-template',
  standalone: true,
  imports: [],
  templateUrl: './upload-template.component.html',
  styleUrl: './upload-template.component.scss'
})
export class UploadTemplateComponent {
  constructor(public dialogRef: MatDialogRef<UploadTemplateComponent>) {

  }
  closeDialog() {
    this.dialogRef.close(true);
  }
}
