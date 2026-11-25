import { TestBed } from '@angular/core/testing';
import { RecordForm } from './record-form';
describe('RecordForm', () => {
  it('rechaza fechas invertidas antes de llamar a la API', () => {
    const f = TestBed.createComponent(RecordForm);
    f.componentRef.setInput('fields', [
      { key: 'fecha_inicio', label: 'Inicio' },
      { key: 'fecha_fin', label: 'Fin' },
      { key: 'fecha_cierre_inscripcion', label: 'Cierre' },
      { key: 'modalidad', label: 'Modalidad' },
    ]);
    f.detectChanges();
    const spy = vi.fn();
    f.componentInstance.saved.subscribe(spy);
    f.componentInstance.form.setValue({
      fecha_inicio: '2026-11-27T10:00',
      fecha_fin: '2026-11-27T09:00',
      fecha_cierre_inscripcion: '2026-11-26T10:00',
      modalidad: 'virtual',
    });
    f.componentInstance.submit();
    expect(spy).not.toHaveBeenCalled();
    expect(f.componentInstance.validationMessage).toContain('cierre');
  });
  it('impide enviar campos inválidos y contraseñas diferentes', async () => {
    const f = TestBed.createComponent(RecordForm);
    f.componentRef.setInput('fields', [
      { key: 'correo', label: 'Correo', type: 'email', required: true },
      { key: 'clave', label: 'Clave', type: 'password', min: 12, required: true },
      { key: 'confirmacion', label: 'Confirmación', type: 'password', required: true },
    ]);
    f.detectChanges();
    const spy = vi.fn();
    f.componentInstance.saved.subscribe(spy);
    f.componentInstance.submit();
    expect(spy).not.toHaveBeenCalled();
    f.componentInstance.form.setValue({
      correo: 'invalido',
      clave: 'ClaveLargaSegura',
      confirmacion: 'otra',
    });
    f.componentInstance.submit();
    expect(spy).not.toHaveBeenCalled();
    f.componentInstance.form.setValue({
      correo: 'demo@example.org',
      clave: 'ClaveLargaSegura',
      confirmacion: 'ClaveLargaSegura',
    });
    f.componentInstance.submit();
    expect(spy).toHaveBeenCalledOnce();
  });
  it('conserva los valores al cambiar el estado de carga', () => {
    const f = TestBed.createComponent(RecordForm);
    f.componentRef.setInput('fields', [{ key: 'nombre', label: 'Nombre', required: true }]);
    f.detectChanges();
    f.componentInstance.form.patchValue({ nombre: 'Trabajo en curso' });
    f.componentRef.setInput('busy', true);
    f.detectChanges();
    expect(f.componentInstance.form.value.nombre).toBe('Trabajo en curso');
  });
});
