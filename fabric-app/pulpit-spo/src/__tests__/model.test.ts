import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { describe, expect, it } from 'vitest';

import {
  activationProgress,
  indexScene,
  minutesLabel,
  relativeLabel,
  stepClock,
  type LiveStep,
  type Scene,
} from '@/data/model';

const scene: Scene = JSON.parse(
  readFileSync(resolve(__dirname, '../../public/data/scene.json'), 'utf8'),
);
const index = indexScene(scene);

function step(patch: Partial<LiveStep>): LiveStep {
  return {
    stepId: 'S1',
    stepNo: 1,
    title: 'krok',
    roleCode: 'R',
    roleName: 'rola',
    institution: 'RCB',
    slaMinutes: 60,
    outputDocument: '',
    critical: false,
    status: 'w toku',
    startedOffsetMin: -30,
    completedOffsetMin: null,
    blockerReason: '',
    ...patch,
  };
}

describe('zegar kroku', () => {
  it('nie tyka, dopóki krok się nie rozpoczął', () => {
    expect(stepClock(step({ startedOffsetMin: null }))).toBeNull();
  });

  it('liczy czas do teraz dla kroku w toku', () => {
    const c = stepClock(step({ startedOffsetMin: -30 }))!;
    expect(c.elapsedMin).toBe(30);
    expect(c.remainingMin).toBe(30);
    expect(c.breached).toBe(false);
  });

  it('zatrzymuje się na chwili zamknięcia kroku', () => {
    const c = stepClock(step({ startedOffsetMin: -120, completedOffsetMin: -80 }))!;
    expect(c.elapsedMin).toBe(40);
    expect(c.breached).toBe(false);
  });

  it('oznacza przekroczenie normy', () => {
    const c = stepClock(step({ startedOffsetMin: -90 }))!;
    expect(c.breached).toBe(true);
    expect(c.remainingMin).toBe(-30);
  });

  it('ostrzega od 75% wykorzystania normy, ale nie po przekroczeniu', () => {
    expect(stepClock(step({ startedOffsetMin: -45 }))!.warning).toBe(true);
    expect(stepClock(step({ startedOffsetMin: -44 }))!.warning).toBe(false);
    expect(stepClock(step({ startedOffsetMin: -90 }))!.warning).toBe(false);
  });
});

describe('postęp uruchomienia', () => {
  it('zalicza do zamkniętych także kroki pominięte', () => {
    const p = activationProgress({
      steps: [
        step({ status: 'wykonany', completedOffsetMin: -20 }),
        step({ status: 'pominięty', startedOffsetMin: null }),
        step({ status: 'zablokowany', startedOffsetMin: -200, blockerReason: 'brak danych' }),
        step({ status: 'oczekuje', startedOffsetMin: null }),
      ],
    });
    expect(p).toMatchObject({ done: 2, total: 4, blocked: 1, breached: 1 });
    expect(p.pct).toBe(50);
  });
});

describe('opisy czasu', () => {
  it('dobiera jednostkę do wielkości', () => {
    expect(minutesLabel(45)).toBe('45 min');
    expect(minutesLabel(120)).toContain('h');
    expect(minutesLabel(2880)).toContain('doby');
  });

  it('rozróżnia przeszłość od przyszłości', () => {
    expect(relativeLabel(0)).toBe('teraz');
    expect(relativeLabel(40)).toBe('za 40 min');
    expect(relativeLabel(-35)).toBe('35 min temu');
  });
});

describe('scena', () => {
  it('niesie komplet słowników potrzebnych ekranom', () => {
    expect(scene.procedures.length).toBeGreaterThan(10);
    expect(scene.roles.length).toBeGreaterThan(10);
    expect(scene.liveActivations.length).toBeGreaterThan(0);
    expect(index.procedureByCode.size).toBe(scene.procedures.length);
  });

  it('każde uruchomienie w toku ma kroki i procedurę ze słownika', () => {
    for (const a of scene.liveActivations) {
      expect(index.procedureByCode.has(a.procedureCode)).toBe(true);
      expect(a.steps.length).toBeGreaterThan(0);
    }
  });

  it('czasy uruchomień są względne, więc scena nie starzeje się w kalendarzu', () => {
    // Ujemny offset = zdarzenie w przeszłości względem chwili wejścia do
    // aplikacji. Gdyby scena niosła daty bezwzględne, demo po tygodniu
    // pokazywałoby dyżur sprzed tygodnia.
    for (const a of scene.liveActivations) expect(a.startedOffsetMin).toBeLessThanOrEqual(0);
  });

  it('analityka SLA pokrywa procedury z historią', () => {
    for (const s of scene.analytics.slaByProcedure) {
      expect(index.procedureByCode.has(s.procedureCode)).toBe(true);
      expect(s.slaCompliancePct).toBeGreaterThanOrEqual(0);
      expect(s.slaCompliancePct).toBeLessThanOrEqual(100);
    }
  });
});
