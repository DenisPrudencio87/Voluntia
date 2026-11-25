import { TestBed } from '@angular/core/testing';
import { Feedback } from './api';
describe('Feedback: regresiones de auditoría', () => {
  it('conserva la confirmación producida por el formulario de cuenta', async () => {
    const f = TestBed.inject(Feedback);
    await f.run(async () => {
      f.success.set('Recibirás un enlace de verificación.');
    });
    expect(f.success()).toBe('Recibirás un enlace de verificación.');
  });
  it('mantiene carga mientras quede una operación concurrente', async () => {
    const f = TestBed.inject(Feedback);
    let finish!: () => void;
    const pending = f.run(() => new Promise<void>((r) => (finish = r)));
    await f.run(async () => undefined);
    expect(f.busy()).toBe(true);
    finish();
    await pending;
    expect(f.busy()).toBe(false);
  });
});
