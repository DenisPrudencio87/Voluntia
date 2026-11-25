import { TestBed } from '@angular/core/testing';
import { RecordForm } from './record-form';
describe('RecordForm', () => {
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
