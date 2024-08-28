import { Component } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'app-grouping-modal',
  standalone: true,
  imports: [],
  templateUrl: './grouping-modal.component.html',
  styleUrl: './grouping-modal.component.scss'
})
export class GroupingModalComponent {
  constructor(public dialogRef: MatDialogRef<GroupingModalComponent>) {

  }
  closeDialog() {
    this.dialogRef.close();
  }
}
