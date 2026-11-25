import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CatalogItem, Skill } from '../models/domain';

@Component({
  selector: 'app-skills',
  template: ` <fieldset class="my-3">
    <legend class="h6">{{ requiredMode ? 'Habilidades solicitadas' : 'Mis habilidades' }}</legend>
    <p class="small text-secondary">Selecciona las habilidades y su nivel.</p>
    <div class="row g-2">
      @for (skill of catalog; track skill.id_habilidad) {
        <div class="col-12 col-md-6">
          <div class="border rounded p-3">
            <label class="form-check"
              ><input
                type="checkbox"
                class="form-check-input"
                [checked]="selected(skill.id_habilidad!)"
                (change)="toggle(skill.id_habilidad!, $event)"
              /><span class="form-check-label">{{ skill.nombre }}</span></label
            >
            @if (selected(skill.id_habilidad!)) {
              <label class="small"
                >Nivel<select
                  class="form-select form-select-sm"
                  [value]="level(skill.id_habilidad!)"
                  (change)="setLevel(skill.id_habilidad!, $event)"
                >
                  <option value="basico">Básico</option>
                  <option value="intermedio">Intermedio</option>
                  <option value="avanzado">Avanzado</option>
                </select></label
              >
              @if (requiredMode) {
                <label class="form-check mt-2"
                  ><input
                    class="form-check-input"
                    type="checkbox"
                    [checked]="mandatory(skill.id_habilidad!)"
                    (change)="setMandatory(skill.id_habilidad!, $event)"
                  />Obligatoria</label
                >
              }
            }
          </div>
        </div>
      }
    </div>
  </fieldset>`,
})
export class SkillsEditor {
  @Input() catalog: CatalogItem[] = [];
  @Input() skills: Skill[] = [];
  @Input() requiredMode = false;
  @Output() skillsChange = new EventEmitter<Skill[]>();
  selected(id: number) {
    return this.skills.some((s) => s.id_habilidad === id);
  }
  level(id: number) {
    const s = this.skills.find((s) => s.id_habilidad === id);
    return s?.nivel ?? s?.nivel_requerido ?? 'basico';
  }
  mandatory(id: number) {
    return this.skills.find((s) => s.id_habilidad === id)?.obligatoria ?? true;
  }
  toggle(id: number, e: Event) {
    const checked = (e.target as HTMLInputElement).checked;
    this.skills = checked
      ? [
          ...this.skills,
          {
            id_habilidad: id,
            ...(this.requiredMode
              ? { nivel_requerido: 'basico', obligatoria: true }
              : { nivel: 'basico' }),
          },
        ]
      : this.skills.filter((s) => s.id_habilidad !== id);
    this.skillsChange.emit(this.skills);
  }
  setLevel(id: number, e: Event) {
    const level = (e.target as HTMLSelectElement).value;
    this.skills = this.skills.map((s) =>
      s.id_habilidad === id
        ? { ...s, ...(this.requiredMode ? { nivel_requerido: level } : { nivel: level }) }
        : s,
    );
    this.skillsChange.emit(this.skills);
  }
  setMandatory(id: number, e: Event) {
    this.skills = this.skills.map((s) =>
      s.id_habilidad === id ? { ...s, obligatoria: (e.target as HTMLInputElement).checked } : s,
    );
    this.skillsChange.emit(this.skills);
  }
}
