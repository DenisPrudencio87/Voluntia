import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnChanges,
  SimpleChanges,
  inject,
} from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators, FormGroup } from '@angular/forms';

export type FormValue = Record<string, string | number | boolean | null>;
export interface Field {
  key: string;
  label: string;
  type?: string;
  required?: boolean;
  min?: number;
  max?: number;
  options?: { value: string | number; label: string }[];
  hint?: string;
}

@Component({
  selector: 'app-record-form',
  imports: [ReactiveFormsModule],
  template: ` <form [formGroup]="form" (ngSubmit)="submit()" class="row g-3" novalidate>
    @for (field of fields; track field.key) {
      <div [class]="field.type === 'textarea' ? 'col-12' : 'col-12 col-md-6'">
        <label [for]="id + '-' + field.key" class="form-label">{{ field.label }}</label>
        @if (field.required) { <span aria-hidden="true" class="ms-1">*</span> }
        @if (field.type === 'select') {
          <select
            class="form-select"
            [id]="id + '-' + field.key"
            [formControlName]="field.key"
            [attr.aria-required]="field.required || null"
            [attr.aria-invalid]="invalid(field.key)"
          >
            <option value="">Selecciona una opción</option>
            @for (option of field.options; track option.value) {
              <option [value]="option.value">{{ option.label }}</option>
            }
          </select>
        } @else if (field.type === 'textarea') {
          <textarea
            class="form-control"
            rows="4"
            [id]="id + '-' + field.key"
            [formControlName]="field.key"
            [attr.aria-required]="field.required || null"
            [attr.aria-invalid]="invalid(field.key)"
          ></textarea>
        } @else if (field.type === 'checkbox') {
          <div class="form-check">
            <input
              type="checkbox"
              class="form-check-input"
              [id]="id + '-' + field.key"
              [formControlName]="field.key"
            />
          </div>
        } @else {
          <input
            class="form-control"
            [type]="field.type || 'text'"
            [id]="id + '-' + field.key"
            [formControlName]="field.key"
            [attr.min]="field.type === 'number' ? field.min : null"
            [attr.max]="field.type === 'number' ? field.max : null"
            [attr.minlength]="field.type !== 'number' ? field.min : null"
            [attr.maxlength]="field.type !== 'number' ? field.max : null"
            [attr.autocomplete]="
              field.type === 'password' ? 'new-password' : field.type === 'email' ? 'email' : 'off'
            "
            [attr.aria-invalid]="invalid(field.key)"
          />
        }
        @if (field.hint) {
          <div class="form-text">{{ field.hint }}</div>
        }
        @if (invalid(field.key)) {
          <div class="text-danger small" role="alert">Revisa {{ field.label.toLowerCase() }}.</div>
        }
      </div>
    }
    @if (mismatch) {
      <p class="text-danger mb-0" role="alert">Las contraseñas no coinciden.</p>
    }
    <div class="col-12">
      <button class="btn btn-primary" type="submit" [disabled]="busy">
        {{ busy ? 'Guardando…' : label }}
      </button>
    </div>
  </form>`,
})
export class RecordForm implements OnChanges {
  private fb = inject(FormBuilder);
  private static sequence = 0;
  id = 'form-' + ++RecordForm.sequence;
  @Input() fields: Field[] = [];
  @Input() initial: object | null = null;
  @Input() label = 'Guardar';
  @Input() busy = false;
  @Output() saved = new EventEmitter<FormValue>();
  form: FormGroup = this.fb.group({});
  mismatch = false;
  ngOnChanges(changes: SimpleChanges) {
    if (!changes['fields'] && !changes['initial']) return;
    const values = (this.initial ?? {}) as FormValue;
    const group: Record<string, unknown> = {};
    for (const field of this.fields) {
      const validators = [];
      if (field.required) validators.push(Validators.required);
      if (field.type === 'email') validators.push(Validators.email);
      if (field.min !== undefined)
        validators.push(
          field.type === 'number' ? Validators.min(field.min) : Validators.minLength(field.min),
        );
      if (field.max !== undefined)
        validators.push(
          field.type === 'number' ? Validators.max(field.max) : Validators.maxLength(field.max),
        );
      group[field.key] = [
        values[field.key] ?? (field.type === 'checkbox' ? false : ''),
        validators,
      ];
    }
    this.form = this.fb.group(group);
  }
  invalid(key: string) {
    const c = this.form.get(key);
    return !!(c?.invalid && c.touched);
  }
  submit() {
    this.form.markAllAsTouched();
    this.mismatch =
      this.form.contains('confirmacion') && this.form.value.clave !== this.form.value.confirmacion;
    if (this.form.valid && !this.mismatch && !this.busy) this.saved.emit(this.form.getRawValue());
  }
}
