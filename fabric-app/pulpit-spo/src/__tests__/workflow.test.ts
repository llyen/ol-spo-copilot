import { describe, expect, it } from 'vitest';

import {
  MIN_RATIONALE,
  canWrite,
  maskDecision,
  validateActivation,
  validateDecision,
  validateLesson,
  validateStepExecution,
  type Actor,
  type ActivationDraft,
  type DecisionLogDraft,
  type LessonLearnedDraft,
  type StepExecutionDraft,
  type UserRole,
} from '@/services/workflow';

function actor(role: UserRole): Actor {
  return {
    id: 'u1',
    name: 'Testowy Użytkownik',
    role,
    roleCode: 'R_DYZ_RCB',
    institution: 'RCB',
  };
}

const LONG = 'x'.repeat(MIN_RATIONALE);

const activation: ActivationDraft = {
  procedure_code: 'SPO-01',
  procedure_name: 'Procedura',
  event_name: 'Zdarzenie testowe',
  hazard_code: 'H1',
  level: 'krajowy',
  voivodeship_code: 'PL',
  voivodeship_name: 'kraj',
  trigger_text: LONG,
  confidence: 0.8,
  source_question: 'pytanie',
  from_assistant: true,
  status: 'w toku',
};

const decision: DecisionLogDraft = {
  activation_id: 'A1',
  procedure_code: 'SPO-01',
  step_no: 1,
  decision_type: 'zatwierdzenie komunikatu',
  decided_by_role: 'R_DYZ_RCB',
  decided_by_name: 'Testowy Użytkownik',
  subject: 'Komunikat ostrzegawczy',
  rationale: LONG,
  classification: 'jawne',
  corrects_decision_id: '',
};

describe('uprawnienia zapisu', () => {
  it('analityk czyta, ale nie pisze', () => {
    expect(canWrite('analityk')).toBe(false);
    expect(canWrite('oficer dyżurny')).toBe(true);
  });

  it('analityk nie uruchamia procedur', () => {
    expect(validateActivation(activation, actor('analityk')).ok).toBe(false);
    expect(validateActivation(activation, actor('oficer dyżurny')).ok).toBe(true);
  });
});

describe('dziennik decyzji', () => {
  it('przyjmuje kompletny wpis', () => {
    expect(validateDecision(decision, actor('oficer dyżurny')).ok).toBe(true);
  });

  it('wymaga uzasadnienia o sensownej długości', () => {
    const r = validateDecision({ ...decision, rationale: 'bo tak' }, actor('oficer dyżurny'));
    expect(r.ok).toBe(false);
    expect(r.errors.join(' ')).toContain(String(MIN_RATIONALE));
  });

  it('zamknięcie procedury i odstąpienie od kroku są zastrzeżone dla właściciela', () => {
    for (const type of ['zamknięcie procedury', 'odstąpienie od kroku']) {
      expect(validateDecision({ ...decision, decision_type: type }, actor('oficer dyżurny')).ok).toBe(
        false,
      );
      expect(
        validateDecision({ ...decision, decision_type: type }, actor('właściciel procedury')).ok,
      ).toBe(true);
    }
  });

  it('odrzuca typ decyzji spoza słownika', () => {
    expect(validateDecision({ ...decision, decision_type: 'cokolwiek' }, actor('oficer dyżurny')).ok).toBe(
      false,
    );
  });
});

describe('wykonanie kroku', () => {
  const base: StepExecutionDraft = {
    activation_id: 'A1',
    procedure_code: 'SPO-01',
    step_id: 'S1',
    step_no: 1,
    step_title: 'krok',
    role_code: 'R_DYZ_RCB',
    institution: 'RCB',
    status: 'wykonany',
    sla_minutes: 60,
    elapsed_minutes: 30,
    sla_met: true,
    is_critical: false,
    blocker_reason: '',
    note: '',
    output_document: '',
    waived: false,
    waiver_justification: '',
  };

  it('blokada bez przyczyny jest bezużyteczna dla wniosków po zdarzeniu', () => {
    expect(validateStepExecution({ ...base, status: 'zablokowany' }, actor('oficer dyżurny')).ok).toBe(
      false,
    );
    expect(
      validateStepExecution(
        { ...base, status: 'zablokowany', blocker_reason: 'brak łączności' },
        actor('oficer dyżurny'),
      ).ok,
    ).toBe(true);
  });

  it('odstąpienie wymaga roli właściciela i uzasadnienia', () => {
    expect(
      validateStepExecution(
        { ...base, waived: true, waiver_justification: LONG },
        actor('oficer dyżurny'),
      ).ok,
    ).toBe(false);
    expect(
      validateStepExecution(
        { ...base, waived: true, waiver_justification: 'bo tak' },
        actor('właściciel procedury'),
      ).ok,
    ).toBe(false);
    expect(
      validateStepExecution(
        { ...base, waived: true, waiver_justification: LONG },
        actor('właściciel procedury'),
      ).ok,
    ).toBe(true);
  });
});

describe('wnioski po zdarzeniu', () => {
  const lesson: LessonLearnedDraft = {
    activation_id: 'A1',
    procedure_code: 'SPO-01',
    finding_kind: 'przekroczenie normy',
    step_no: 4,
    finding: 'Krok 4 przekroczył normę o 35 min.',
    historical_occurrences: 18,
    recommendation: LONG,
    owner_role: 'R_DYZ_RCB',
    due_date: '',
    accepted: true,
  };

  it('przyjmuje wniosek od właściciela procedury', () => {
    expect(validateLesson(lesson, actor('właściciel procedury')).ok).toBe(true);
  });

  it('nie pozwala dyżurnemu zamykać wniosków po zdarzeniu', () => {
    expect(validateLesson(lesson, actor('oficer dyżurny')).ok).toBe(false);
  });
});

describe('maskowanie treści niejawnych', () => {
  it('nie rusza wpisów jawnych', () => {
    const d = { classification: 'jawne', subject: 'A', rationale: 'B' };
    expect(maskDecision(d, 'analityk')).toBe(d);
  });

  it('ukrywa treść przed analitykiem, ale zostawia sam fakt decyzji', () => {
    const d = { classification: 'poufne', subject: 'Tajny przedmiot', rationale: 'Tajne powody' };
    const masked = maskDecision(d, 'analityk');
    expect(masked.subject).not.toContain('Tajny');
    expect(masked.subject).toContain('poufne');
    expect(masked.rationale).not.toContain('Tajne');
    expect(masked.classification).toBe('poufne');
  });

  it('pokazuje pełną treść rolom operacyjnym', () => {
    const d = { classification: 'zastrzeżone', subject: 'Przedmiot', rationale: 'Powody' };
    expect(maskDecision(d, 'oficer dyżurny').subject).toBe('Przedmiot');
    expect(maskDecision(d, 'kierownictwo RCB').rationale).toBe('Powody');
  });
});
