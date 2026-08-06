/**
 * Model sceny „Asystent SPO".
 *
 * Scena jest migawką Lakehouse: procedury, kroki, korpus, indeks TF-IDF
 * i analityka SLA policzona z historii 986 uruchomień. Aplikacja liczy
 * wszystko lokalnie, więc odpowiedź asystenta pojawia się bez zapytania
 * do backendu — to jest warunek pracy przy ograniczonej łączności
 * z `fabric-app/APP_SPEC.md`.
 */

export interface SceneStep {
  stepId: string;
  stepNo: number;
  title: string;
  roleCode: string;
  roleName: string;
  institution: string;
  slaMinutes: number;
  outputDocument: string;
  critical: boolean;
}

export interface ProcedureHistory {
  activations: number;
  stepExecutions: number;
  slaCompliancePct: number;
  medianMinutes: number;
  blocked: number;
  timeToFirstCriticalMin: number;
}

export interface Procedure {
  id: string;
  code: string;
  name: string;
  ownerRole: string;
  ownerInstitution: string;
  phase: string;
  legalBasis: string;
  hazards: { code: string; name: string }[];
  keywords: string[];
  totalSlaMinutes: number;
  criticalStepCount: number;
  history: ProcedureHistory | null;
  steps: SceneStep[];
}

export interface Chunk {
  id: string;
  documentId: string;
  docType: string;
  docTitle: string;
  procedureCode: string;
  section: string;
  title: string;
  text: string;
}

export interface SceneIndexData {
  terms: string[];
  idf: number[];
  rows: [number, number][][];
  nonZero: number;
}

export type StepStatus = 'oczekuje' | 'w toku' | 'wykonany' | 'zablokowany' | 'pominięty';

export interface LiveStep extends SceneStep {
  status: StepStatus;
  startedOffsetMin: number | null;
  completedOffsetMin: number | null;
  blockerReason: string;
}

export interface LiveDecision {
  decisionId: string;
  offsetMin: number;
  stepNo: number;
  decisionType: string;
  decidedByRole: string;
  decidedByName: string;
  subject: string;
  rationale: string;
  classification: string;
}

export interface LiveActivation {
  activationId: string;
  procedureCode: string;
  procedureName: string;
  eventName: string;
  hazardCode: string;
  level: string;
  voivodeshipCode: string;
  voivodeshipName: string;
  initiatedByRole: string;
  initiatedByInstitution: string;
  triggerText: string;
  startedOffsetMin: number;
  ownerRoleCode: string;
  firstStepRole: string;
  steps: LiveStep[];
  decisions: LiveDecision[];
}

export interface SlaRow {
  procedureCode: string;
  procedureName: string;
  phase: string;
  activations: number;
  stepExecutions: number;
  slaCompliancePct: number;
  medianMinutes: number;
  blocked: number;
}

export interface WorstStep {
  procedureCode: string;
  stepNo: number;
  title: string;
  roleCode: string;
  executions: number;
  slaCompliancePct: number;
  medianMinutes: number;
  slaMinutes: number;
  breachPct: number;
  ratioToNorm: number;
}

export interface Blocker {
  reason: string;
  occurrences: number;
  procedures: number;
  years: number;
  first: string;
  last: string;
}

export interface Scene {
  meta: {
    scenario: string;
    title: string;
    confidenceThreshold: number;
    seed: number;
    counts: Record<string, number>;
    summary: Record<string, string | number>;
    retrieval: {
      questions: number;
      top1_accuracy: number;
      top3_accuracy: number;
      mrr: number;
      misses: { question: string; expected_procedure: string; predicted_procedure: string }[];
    };
    index: Record<string, string | number>;
  };
  procedures: Procedure[];
  roles: { code: string; name: string; institution: string; level: string }[];
  hazards: { code: string; name: string; risk: string }[];
  chunks: Chunk[];
  index: SceneIndexData;
  analytics: {
    slaByProcedure: SlaRow[];
    worstSteps: WorstStep[];
    blockers: Blocker[];
    usageByRole: {
      role: string;
      questions: number;
      accuracy: number;
      medianLatencyMs: number;
      meanConfidence: number;
    }[];
  };
  sampleQuestions: { id: string; question: string; expected: string }[];
  liveActivations: LiveActivation[];
}

export interface SceneIndex {
  scene: Scene;
  procedureByCode: Map<string, Procedure>;
  chunkById: Map<string, Chunk>;
  roleByCode: Map<string, { code: string; name: string; institution: string; level: string }>;
  slaByCode: Map<string, SlaRow>;
  worstByCode: Map<string, WorstStep[]>;
}

export function indexScene(scene: Scene): SceneIndex {
  const worstByCode = new Map<string, WorstStep[]>();
  for (const w of scene.analytics.worstSteps) {
    const list = worstByCode.get(w.procedureCode) ?? [];
    list.push(w);
    worstByCode.set(w.procedureCode, list);
  }
  return {
    scene,
    procedureByCode: new Map(scene.procedures.map((p) => [p.code, p])),
    chunkById: new Map(scene.chunks.map((c) => [c.id, c])),
    roleByCode: new Map(scene.roles.map((r) => [r.code, r])),
    slaByCode: new Map(scene.analytics.slaByProcedure.map((s) => [s.procedureCode, s])),
    worstByCode,
  };
}

/* ------------------------------------------------------------------ */
/* Formatowanie                                                        */
/* ------------------------------------------------------------------ */

const numberFormat = new Intl.NumberFormat('pl-PL', { maximumFractionDigits: 1 });

export function formatNumber(value: number): string {
  return numberFormat.format(value);
}

/** Czas normatywny opisany tak, jak mówi o nim dyżurny: minuty, godziny, doby. */
export function minutesLabel(minutes: number): string {
  if (minutes < 60) return `${Math.round(minutes)} min`;
  if (minutes < 1440) return `${formatNumber(Math.round((minutes / 60) * 10) / 10)} h`;
  return `${formatNumber(Math.round((minutes / 1440) * 10) / 10)} doby`;
}

/** Podpisany czas względem teraz: „za 40 min" / „35 min temu". */
export function relativeLabel(minutes: number): string {
  const abs = Math.abs(minutes);
  const label = minutesLabel(abs);
  if (Math.round(minutes) === 0) return 'teraz';
  return minutes > 0 ? `za ${label}` : `${label} temu`;
}

const dateTimeFormat = new Intl.DateTimeFormat('pl-PL', {
  day: '2-digit',
  month: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
});

export function offsetToDate(offsetMin: number, now = Date.now()): Date {
  return new Date(now + offsetMin * 60_000);
}

export function formatOffset(offsetMin: number, now = Date.now()): string {
  return dateTimeFormat.format(offsetToDate(offsetMin, now));
}

/* ------------------------------------------------------------------ */
/* Zegar kroku                                                         */
/* ------------------------------------------------------------------ */

export type StepClock = {
  /** Minuty pozostałe do czasu normatywnego; ujemne = norma przekroczona. */
  remainingMin: number;
  elapsedMin: number;
  breached: boolean;
  /** Ostrzeżenie od 75% wykorzystania normy. */
  warning: boolean;
};

export function stepClock(step: LiveStep, nowMin = 0): StepClock | null {
  if (step.startedOffsetMin === null) return null;
  const end = step.completedOffsetMin ?? nowMin;
  const elapsed = end - step.startedOffsetMin;
  const remaining = step.slaMinutes - elapsed;
  return {
    elapsedMin: elapsed,
    remainingMin: remaining,
    breached: remaining < 0,
    warning: remaining >= 0 && elapsed >= step.slaMinutes * 0.75,
  };
}

export const STATUS_ORDER: StepStatus[] = [
  'zablokowany',
  'w toku',
  'oczekuje',
  'wykonany',
  'pominięty',
];

export function statusTone(status: StepStatus): string {
  switch (status) {
    case 'wykonany':
      return 'bg-emerald-50 text-emerald-800 ring-emerald-600/30';
    case 'w toku':
      return 'bg-gov/10 text-gov-dark ring-gov/40';
    case 'zablokowany':
      return 'bg-red-50 text-red-800 ring-red-600/30';
    case 'pominięty':
      return 'bg-slate-100 text-slate-600 ring-slate-400/40';
    default:
      return 'bg-slate-50 text-slate-700 ring-slate-300';
  }
}

/** Postęp uruchomienia liczony krokami zamkniętymi (wykonane i pominięte). */
export function activationProgress(activation: { steps: LiveStep[] }): {
  done: number;
  total: number;
  blocked: number;
  breached: number;
  pct: number;
} {
  const total = activation.steps.length;
  let done = 0;
  let blocked = 0;
  let breached = 0;
  for (const s of activation.steps) {
    if (s.status === 'wykonany' || s.status === 'pominięty') done += 1;
    if (s.status === 'zablokowany') blocked += 1;
    const clock = stepClock(s);
    if (clock?.breached) breached += 1;
  }
  return { done, total, blocked, breached, pct: total ? (done / total) * 100 : 0 };
}
