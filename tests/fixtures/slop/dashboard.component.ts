import { Component } from '@angular/core';

@Component({
  selector: 'app-dashboard',
  template: `
    <div class="grid grid-cols-3 gap-6">
      <div class="rounded-2xl bg-white p-6 shadow-lg" *ngFor="let k of kpis">
        <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-violet-100">📈</div>
        <p class="text-sm text-slate-400">{{ k.label }}</p>
      </div>
    </div>
    <button [ngClass]="'rounded-xl bg-violet-600 outline-none'">Export</button>
  `,
  styles: [`
    .kpi { font-family: "Poppins", sans-serif; padding: 14px; margin: 18px; gap: 10px; }
    .kpi-label { padding: 6px 10px; margin-bottom: 7px; }
  `],
})
export class DashboardComponent {
  kpis = [{ label: 'Revenue' }];
}
