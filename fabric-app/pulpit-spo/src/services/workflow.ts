import { getRayfinClient, isLocalBackend } from './rayfinClient';

/**
 * Zapis zwrotny pulpitu „Asystent SPO".
 *
 * Zasady z `fabric-app/APP_SPEC.md`:
 * 1. **Wpisu dziennika nie da się zmienić ani usunąć.** Korekta to nowy wpis
 *    wskazujący poprzedni. Dziennik edytowalny po fakcie nie jest dowodem.
 * 2. **Odstąpienie od kroku wymaga właściciela procedury i uzasadnienia.**
 *    Dyżurny może zgłosić blokadę, ale nie może samodzielnie wykreślić kroku.
 * 3. **Analityk nie widzi treści decyzji niejawnych.** Widzi, że zapadły i kiedy,
 *    ale nie ich przedmiot i uzasadnienie — to odpowiednik RLS w modelu semantycznym.
 *
 * Bez skonfigurowanego backendu zapisy trafiają do pamięci, żeby aplikację dało
 * się zademonstrować bez połączenia z Fabric.
 */

export type UserRole =
  | 'oficer dyżurny'
  | 'właściciel procedury'
  | 'kierownictwo RCB'
  | 'analityk';

export const USER_ROLES: UserRole[] = [
  'oficer dyżurny',
  'właściciel procedury',
  'kierownictwo RCB',
  'analityk',
];

/** Role, które mogą cokolwiek zapisać. Analityk ma wyłącznie odczyt. */
export function canWrite(role: UserRole): boolean {
  return role !== 'analityk';
}

/** Uruchomienie procedury i zmiana statusu kroku. */
export const OPERATIONAL_ROLES: UserRole[] = ['oficer dyżurny', 'właściciel procedury'];

/** Zamknięcie procedury, odstąpienie od kroku, zatwierdzenie wniosków. */
export const OWNER_ROLES: UserRole[] = ['właściciel procedury', 'kierownictwo RCB'];

/** Kto widzi przedmiot i uzasadnienie decyzji niejawnych. */
export function canSeeClassified(role: UserRole): boolean {
  return role !== 'analityk';
}

export interface Actor {
  id: string;
  name: string;
  role: UserRole;
  /** Kod roli w procedurze (np. `R_DYZ_RCB`) — filtruje ekran „Moje zadania". */
  roleCode: string;
  institution: string;
}

export interface ValidationResult {
  ok: boolean;
  errors: string[];
}

/* ------------------------------------------------------------------ */
/* Słowniki                                                            */
/* ------------------------------------------------------------------ */

export const LEVELS = ['gminny', 'powiatowy', 'wojewódzki', 'krajowy'] as const;

export const DECISION_TYPES = [
  'uruchomienie procedury',
  'eskalacja poziomu',
  'zatwierdzenie komunikatu',
  'uruchomienie środków',
  'skierowanie sił i środków',
  'wprowadzenie ograniczeń',
  'odstąpienie od kroku',
  'zamknięcie procedury',
] as const;
export type DecisionType = (typeof DECISION_TYPES)[number];

export const CLASSIFICATIONS = ['jawne', 'zastrzeżone', 'poufne'] as const;
export type Classification = (typeof CLASSIFICATIONS)[number];

export const STEP_STATUSES = [
  'oczekuje',
  'w toku',
  'wykonany',
  'zablokowany',
  'pominięty',
] as const;

export const VERDICTS = ['pomocne', 'niepomocne', 'zła procedura'] as const;

export const FINDING_KINDS = [
  'przekroczenie normy',
  'blokada',
  'brak danych',
  'poprawka procedury',
] as const;

/* ------------------------------------------------------------------ */
/* Rekordy                                                             */
/* ------------------------------------------------------------------ */

interface Authored {
  id: string;
  author_id: string;
  author_name: string;
  author_role: string;
  created_at: Date;
}

export interface ActivationDraft {
  procedure_code: string;
  procedure_name: string;
  event_name: string;
  hazard_code: string;
  level: string;
  voivodeship_code: string;
  voivodeship_name: string;
  trigger_text: string;
  confidence: number;
  source_question: string;
  from_assistant: boolean;
  status: string;
}
export type ActivationRecord = ActivationDraft & Authored & { activation_id: string };

export interface StepExecutionDraft {
  activation_id: string;
  procedure_code: string;
  step_id: string;
  step_no: number;
  step_title: string;
  role_code: string;
  institution: string;
  status: string;
  sla_minutes: number;
  elapsed_minutes: number;
  sla_met: boolean;
  is_critical: boolean;
  blocker_reason: string;
  note: string;
  output_document: string;
  waived: boolean;
  waiver_justification: string;
}
export type StepExecutionRecord = StepExecutionDraft & Authored & { execution_id: string };

export interface DecisionLogDraft {
  activation_id: string;
  procedure_code: string;
  step_no: number;
  decision_type: string;
  decided_by_role: string;
  decided_by_name: string;
  subject: string;
  rationale: string;
  classification: string;
  corrects_decision_id: string;
}
export type DecisionLogRecord = DecisionLogDraft & Authored & { decision_id: string };

export interface AssistantFeedbackDraft {
  question: string;
  top_procedure: string;
  confidence: number;
  corrected_procedure: string;
  verdict: string;
  ambiguous: boolean;
  cited_chunk_ids: string;
  latency_ms: number;
  comment: string;
}
export type AssistantFeedbackRecord = AssistantFeedbackDraft & Authored & { feedback_id: string };

export interface LessonLearnedDraft {
  activation_id: string;
  procedure_code: string;
  finding_kind: string;
  step_no: number;
  finding: string;
  historical_occurrences: number;
  recommendation: string;
  owner_role: string;
  due_date: string;
  accepted: boolean;
}
export type LessonLearnedRecord = LessonLearnedDraft & Authored & { lesson_id: string };

/* ------------------------------------------------------------------ */
/* Walidacje                                                           */
/* ------------------------------------------------------------------ */

export const MIN_RATIONALE = 30;

export function validateActivation(draft: ActivationDraft, actor: Actor): ValidationResult {
  const errors: string[] = [];
  if (!OPERATIONAL_ROLES.includes(actor.role)) {
    errors.push(`Rola „${actor.role}" nie uruchamia procedur.`);
  }
  if (!draft.procedure_code) errors.push('Wskaż procedurę.');
  if (draft.event_name.trim().length < 5) {
    errors.push('Nazwa zdarzenia musi mieć co najmniej 5 znaków.');
  }
  if (draft.trigger_text.trim().length < MIN_RATIONALE) {
    errors.push(`Uzasadnienie uruchomienia musi mieć co najmniej ${MIN_RATIONALE} znaków.`);
  }
  if (!LEVELS.includes(draft.level as (typeof LEVELS)[number])) {
    errors.push('Wskaż poziom uruchomienia.');
  }
  // Uruchomienie na poziomie wojewódzkim bez wskazania województwa jest
  // bezużyteczne przy kierowaniu sił i przy raportowaniu.
  if ((draft.level === 'wojewódzki' || draft.level === 'powiatowy') && !draft.voivodeship_code) {
    errors.push('Dla poziomu wojewódzkiego i powiatowego wskaż województwo.');
  }
  return { ok: errors.length === 0, errors };
}

export function validateStepExecution(
  draft: StepExecutionDraft,
  actor: Actor,
): ValidationResult {
  const errors: string[] = [];
  if (!canWrite(actor.role)) {
    errors.push(`Rola „${actor.role}" ma wyłącznie dostęp do odczytu.`);
  }
  if (!STEP_STATUSES.includes(draft.status as (typeof STEP_STATUSES)[number])) {
    errors.push('Wskaż status kroku.');
  }
  if (draft.status === 'zablokowany' && !draft.blocker_reason) {
    errors.push('Podaj przyczynę blokady.');
  }
  if (draft.waived) {
    if (!OWNER_ROLES.includes(actor.role)) {
      errors.push('Odstąpienie od kroku wymaga roli właściciela procedury.');
    }
    if (draft.waiver_justification.trim().length < MIN_RATIONALE) {
      errors.push(`Uzasadnienie odstąpienia musi mieć co najmniej ${MIN_RATIONALE} znaków.`);
    }
  }
  return { ok: errors.length === 0, errors };
}

export function validateDecision(draft: DecisionLogDraft, actor: Actor): ValidationResult {
  const errors: string[] = [];
  if (!canWrite(actor.role)) {
    errors.push(`Rola „${actor.role}" ma wyłącznie dostęp do odczytu.`);
  }
  if (!draft.activation_id) errors.push('Wskaż uruchomienie, którego dotyczy decyzja.');
  if (!DECISION_TYPES.includes(draft.decision_type as DecisionType)) {
    errors.push('Wskaż typ decyzji.');
  }
  if (draft.subject.trim().length < 5) errors.push('Podaj przedmiot decyzji.');
  if (draft.rationale.trim().length < MIN_RATIONALE) {
    errors.push(`Uzasadnienie musi mieć co najmniej ${MIN_RATIONALE} znaków.`);
  }
  if (!CLASSIFICATIONS.includes(draft.classification as Classification)) {
    errors.push('Wskaż klauzulę.');
  }
  if (draft.decision_type === 'zamknięcie procedury' && !OWNER_ROLES.includes(actor.role)) {
    errors.push('Procedurę zamyka właściciel procedury lub kierownictwo.');
  }
  if (draft.decision_type === 'odstąpienie od kroku' && !OWNER_ROLES.includes(actor.role)) {
    errors.push('Odstąpienie od kroku zatwierdza właściciel procedury.');
  }
  return { ok: errors.length === 0, errors };
}

export function validateFeedback(
  draft: AssistantFeedbackDraft,
  actor: Actor,
): ValidationResult {
  const errors: string[] = [];
  if (!canWrite(actor.role)) {
    errors.push(`Rola „${actor.role}" ma wyłącznie dostęp do odczytu.`);
  }
  if (!draft.question.trim()) errors.push('Brak pytania.');
  if (!VERDICTS.includes(draft.verdict as (typeof VERDICTS)[number])) {
    errors.push('Wskaż ocenę odpowiedzi.');
  }
  if (draft.verdict === 'zła procedura' && !draft.corrected_procedure) {
    errors.push('Wskaż procedurę, która powinna zostać zaproponowana.');
  }
  return { ok: errors.length === 0, errors };
}

export function validateLesson(draft: LessonLearnedDraft, actor: Actor): ValidationResult {
  const errors: string[] = [];
  if (!OWNER_ROLES.includes(actor.role)) {
    errors.push('Wnioski po zdarzeniu zatwierdza właściciel procedury lub kierownictwo.');
  }
  if (!draft.activation_id) errors.push('Wskaż uruchomienie.');
  if (draft.finding.trim().length < 5) errors.push('Opisz ustalenie.');
  if (draft.recommendation.trim().length < MIN_RATIONALE) {
    errors.push(`Rekomendacja musi mieć co najmniej ${MIN_RATIONALE} znaków.`);
  }
  return { ok: errors.length === 0, errors };
}

/* ------------------------------------------------------------------ */
/* Widoczność treści niejawnych                                        */
/* ------------------------------------------------------------------ */

/**
 * Maskuje treść wpisu dziennika dla roli bez dostępu do klauzul.
 *
 * Wpis nie znika z listy — analityk ma widzieć, że decyzja zapadła i kiedy,
 * bo bez tego liczba decyzji w raporcie byłaby nieprawdziwa. Znika treść.
 */
export function maskDecision<
  T extends { classification: string; subject: string; rationale: string },
>(decision: T, role: UserRole): T {
  if (decision.classification === 'jawne' || canSeeClassified(role)) return decision;
  return {
    ...decision,
    subject: `[treść zastrzeżona — klauzula: ${decision.classification}]`,
    rationale: '[treść niedostępna dla roli analityk]',
  };
}

/* ------------------------------------------------------------------ */
/* Zapis                                                               */
/* ------------------------------------------------------------------ */

const memory = {
  activations: [] as ActivationRecord[],
  executions: [] as StepExecutionRecord[],
  decisions: [] as DecisionLogRecord[],
  feedback: [] as AssistantFeedbackRecord[],
  lessons: [] as LessonLearnedRecord[],
};

const AUTHOR_COLS = ['author_id', 'author_name', 'author_role', 'created_at'] as const;

const ACTIVATION_COLS = [
  'id', 'activation_id', 'procedure_code', 'procedure_name', 'event_name', 'hazard_code',
  'level', 'voivodeship_code', 'voivodeship_name', 'trigger_text', 'confidence',
  'source_question', 'from_assistant', 'status', ...AUTHOR_COLS,
] as const;

const EXECUTION_COLS = [
  'id', 'execution_id', 'activation_id', 'procedure_code', 'step_id', 'step_no', 'step_title',
  'role_code', 'institution', 'status', 'sla_minutes', 'elapsed_minutes', 'sla_met',
  'is_critical', 'blocker_reason', 'note', 'output_document', 'waived',
  'waiver_justification', ...AUTHOR_COLS,
] as const;

const DECISION_COLS = [
  'id', 'decision_id', 'activation_id', 'procedure_code', 'step_no', 'decision_type',
  'decided_by_role', 'decided_by_name', 'subject', 'rationale', 'classification',
  'corrects_decision_id', ...AUTHOR_COLS,
] as const;

const FEEDBACK_COLS = [
  'id', 'feedback_id', 'question', 'top_procedure', 'confidence', 'corrected_procedure',
  'verdict', 'ambiguous', 'cited_chunk_ids', 'latency_ms', 'comment', ...AUTHOR_COLS,
] as const;

const LESSON_COLS = [
  'id', 'lesson_id', 'activation_id', 'procedure_code', 'finding_kind', 'step_no', 'finding',
  'historical_occurrences', 'recommendation', 'owner_role', 'due_date', 'accepted',
  ...AUTHOR_COLS,
] as const;

/* eslint-disable @typescript-eslint/no-explicit-any */
async function readAll<T>(
  entityName: string,
  cols: readonly string[],
  fallback: T[],
): Promise<T[]> {
  if (isLocalBackend()) return [...fallback];
  const client = getRayfinClient() as any;
  const rows = await client.data[entityName]
    .select([...cols])
    .orderBy({ created_at: 'desc' })
    .execute();
  return rows as T[];
}

async function writeOne<T extends { id: string }>(
  entityName: string,
  record: T,
  fallback: T[],
): Promise<T> {
  if (isLocalBackend()) {
    fallback.unshift(record);
    return record;
  }
  const client = getRayfinClient() as any;
  const { id: _ignored, ...payload } = record;
  void _ignored;
  const saved = await client.data[entityName].create(payload);
  return saved as T;
}
/* eslint-enable @typescript-eslint/no-explicit-any */

let counter = 0;

function newId(prefix: string): string {
  counter += 1;
  const stamp = new Date().toISOString().replace(/[^0-9]/g, '').slice(2, 12);
  return `${prefix}-${stamp}-${String(counter).padStart(3, '0')}`;
}

function authored(actor: Actor): Omit<Authored, 'id'> {
  return {
    author_id: actor.id,
    author_name: actor.name,
    author_role: actor.role,
    created_at: new Date(),
  };
}

export const listActivations = () =>
  readAll<ActivationRecord>('Activation', ACTIVATION_COLS, memory.activations);
export const listStepExecutions = () =>
  readAll<StepExecutionRecord>('StepExecution', EXECUTION_COLS, memory.executions);
export const listDecisions = () =>
  readAll<DecisionLogRecord>('DecisionLog', DECISION_COLS, memory.decisions);
export const listFeedback = () =>
  readAll<AssistantFeedbackRecord>('AssistantFeedback', FEEDBACK_COLS, memory.feedback);
export const listLessons = () =>
  readAll<LessonLearnedRecord>('LessonLearned', LESSON_COLS, memory.lessons);

export async function saveActivation(
  draft: ActivationDraft,
  actor: Actor,
): Promise<ActivationRecord> {
  const v = validateActivation(draft, actor);
  if (!v.ok) throw new Error(v.errors.join(' '));
  const record: ActivationRecord = {
    ...draft,
    event_name: draft.event_name.trim(),
    trigger_text: draft.trigger_text.trim(),
    id: crypto.randomUUID(),
    activation_id: newId('ACT'),
    ...authored(actor),
  };
  return writeOne('Activation', record, memory.activations);
}

export async function saveStepExecution(
  draft: StepExecutionDraft,
  actor: Actor,
): Promise<StepExecutionRecord> {
  const v = validateStepExecution(draft, actor);
  if (!v.ok) throw new Error(v.errors.join(' '));
  const record: StepExecutionRecord = {
    ...draft,
    note: draft.note.trim(),
    waiver_justification: draft.waiver_justification.trim(),
    id: crypto.randomUUID(),
    execution_id: newId('EXE'),
    ...authored(actor),
  };
  return writeOne('StepExecution', record, memory.executions);
}

export async function saveDecision(
  draft: DecisionLogDraft,
  actor: Actor,
): Promise<DecisionLogRecord> {
  const v = validateDecision(draft, actor);
  if (!v.ok) throw new Error(v.errors.join(' '));
  const record: DecisionLogRecord = {
    ...draft,
    subject: draft.subject.trim(),
    rationale: draft.rationale.trim(),
    id: crypto.randomUUID(),
    decision_id: newId('DEC'),
    ...authored(actor),
  };
  return writeOne('DecisionLog', record, memory.decisions);
}

export async function saveFeedback(
  draft: AssistantFeedbackDraft,
  actor: Actor,
): Promise<AssistantFeedbackRecord> {
  const v = validateFeedback(draft, actor);
  if (!v.ok) throw new Error(v.errors.join(' '));
  const record: AssistantFeedbackRecord = {
    ...draft,
    comment: draft.comment.trim(),
    id: crypto.randomUUID(),
    feedback_id: newId('FB'),
    ...authored(actor),
  };
  return writeOne('AssistantFeedback', record, memory.feedback);
}

export async function saveLesson(
  draft: LessonLearnedDraft,
  actor: Actor,
): Promise<LessonLearnedRecord> {
  const v = validateLesson(draft, actor);
  if (!v.ok) throw new Error(v.errors.join(' '));
  const record: LessonLearnedRecord = {
    ...draft,
    finding: draft.finding.trim(),
    recommendation: draft.recommendation.trim(),
    id: crypto.randomUUID(),
    lesson_id: newId('WNI'),
    ...authored(actor),
  };
  return writeOne('LessonLearned', record, memory.lessons);
}
