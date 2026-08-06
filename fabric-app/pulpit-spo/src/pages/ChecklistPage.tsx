import { useMemo, useState } from 'react';

import {
  activationProgress,
  formatOffset,
  formatNumber,
  minutesLabel,
  relativeLabel,
  statusTone,
  stepClock,
  type LiveActivation,
  type LiveStep,
  type StepStatus,
} from '@/data/model';
import { useScenario } from '@/hooks/ScenarioContext';
import {
  Badge,
  Button,
  EmptyState,
  Field,
  KpiCard,
  Modal,
  Panel,
  Toast,
  inputClass,
} from '@/components/ui';
import {
  OWNER_ROLES,
  STEP_STATUSES,
  canWrite,
  saveDecision,
  saveStepExecution,
} from '@/services/workflow';

/**
 * Ekran 2 — „Checklista uruchomienia".
 *
 * Każda zmiana statusu to zdarzenie zapisywane w bazie aplikacji, a nie
 * nadpisanie wiersza. Dzięki temu pulpit RCB widzi postęp bez raportowania,
 * a po zdarzeniu da się odtworzyć, kiedy krok ruszył i na czym utknął.
 */
export function ChecklistPage() {
  const { activations, currentId, setCurrentId, actor, patchStep, addDecision, index, tick } =
    useScenario();
  void tick;
  const [toast, setToast] = useState<string | null>(null);
  const [editing, setEditing] = useState<LiveStep | null>(null);

  const activation = useMemo(
    () => activations.find((a) => a.activationId === currentId) ?? activations[0] ?? null,
    [activations, currentId],
  );

  if (!activation)
    return <EmptyState text={'Brak uruchomień. Uruchom procedurę na ekranie „Zapytaj o procedurę”.'} />;

  const progress = activationProgress(activation);
  const blockers = index?.scene.analytics.blockers ?? [];

  return (
    <div className="space-y-4">
      <Panel
        title={`${activation.activationId} · ${activation.procedureCode}`}
        subtitle={`${activation.procedureName} — ${activation.eventName}`}
        tone="accent"
        right={
          <select
            value={activation.activationId}
            onChange={(e) => setCurrentId(e.target.value)}
            className="max-w-[320px] rounded-lg bg-slate-50 px-2 py-1 text-xs text-slate-900 ring-1 ring-slate-300"
            aria-label="Wybór uruchomienia"
          >
            {activations.map((a) => (
              <option key={a.activationId} value={a.activationId}>
                {a.activationId} · {a.procedureCode} · {a.eventName}
              </option>
            ))}
          </select>
        }
      >
        <div className="grid gap-3 lg:grid-cols-4">
          <KpiCard
            label="Postęp"
            value={Math.round(progress.pct)}
            unit="%"
            higherIsWorse={false}
            emphasis
            hint={`${progress.done} z ${progress.total} kroków zamkniętych`}
          />
          <KpiCard
            label="Kroki po normie"
            value={progress.breached}
            hint="zegar przekroczył czas normatywny"
          />
          <KpiCard label="Zablokowane" value={progress.blocked} hint="czekają na usunięcie przeszkody" />
          <KpiCard
            label="Uruchomiono"
            value={Math.round(Math.abs(activation.startedOffsetMin) / 6) / 10}
            unit=" h temu"
            hint={formatOffset(activation.startedOffsetMin)}
          />
        </div>
        <div className="mt-3 grid gap-2 text-xs text-slate-600 md:grid-cols-3">
          <div>
            <span className="text-slate-400">Poziom: </span>
            {activation.level}
            {activation.voivodeshipName ? ` · ${activation.voivodeshipName}` : ''}
          </div>
          <div>
            <span className="text-slate-400">Uruchomił: </span>
            {activation.initiatedByInstitution}
          </div>
          <div>
            <span className="text-slate-400">Zagrożenie: </span>
            {activation.hazardCode}
          </div>
        </div>
        <p className="mt-2 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-700 ring-1 ring-slate-200">
          {activation.triggerText}
        </p>
      </Panel>

      <Panel
        title="Kroki"
        subtitle="Zegar odlicza do czasu normatywnego; po przekroczeniu kolor czerwony"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-[11px] uppercase tracking-wider text-slate-500">
                <th className="py-2 pr-2">#</th>
                <th className="py-2 pr-2">Krok</th>
                <th className="py-2 pr-2">Odpowiedzialny</th>
                <th className="py-2 pr-2 text-right">Norma</th>
                <th className="py-2 pr-2 text-right">Zegar</th>
                <th className="py-2 pr-2">Status</th>
                <th className="py-2" />
              </tr>
            </thead>
            <tbody>
              {activation.steps.map((s) => {
                const clock = stepClock(s);
                return (
                  <tr key={s.stepId} className="border-b border-slate-100 align-top">
                    <td className="py-2 pr-2 tabular-nums text-slate-500">{s.stepNo}</td>
                    <td className="py-2 pr-2">
                      <div className="text-slate-900">{s.title}</div>
                      <div className="mt-0.5 flex flex-wrap gap-1">
                        {s.critical && (
                          <Badge className="bg-red-50 text-red-700 ring-red-600/30">krytyczny</Badge>
                        )}
                        {s.blockerReason && (
                          <Badge className="bg-amber-50 text-amber-800 ring-amber-600/30">
                            {s.blockerReason}
                          </Badge>
                        )}
                      </div>
                    </td>
                    <td className="py-2 pr-2 text-xs text-slate-600">
                      {s.roleName}
                      <div className="text-slate-400">{s.institution}</div>
                    </td>
                    <td className="py-2 pr-2 text-right tabular-nums text-slate-600">
                      {minutesLabel(s.slaMinutes)}
                    </td>
                    <td className="py-2 pr-2 text-right tabular-nums">
                      {clock ? (
                        <span
                          className={
                            clock.breached
                              ? 'font-semibold text-red-700'
                              : clock.warning
                                ? 'font-semibold text-amber-700'
                                : 'text-slate-700'
                          }
                        >
                          {clock.breached
                            ? `po normie ${minutesLabel(-clock.remainingMin)}`
                            : relativeLabel(clock.remainingMin)}
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="py-2 pr-2">
                      <Badge className={statusTone(s.status)}>{s.status}</Badge>
                    </td>
                    <td className="py-2 text-right">
                      <Button
                        variant="ghost"
                        onClick={() => setEditing(s)}
                        disabled={!canWrite(actor.role)}
                      >
                        Zmień
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Panel>

      {editing && (
        <StepModal
          step={editing}
          activation={activation}
          blockerOptions={blockers.map((b) => b.reason)}
          onClose={() => setEditing(null)}
          onSubmit={async (patch, waiverJustification) => {
            const clock = stepClock({ ...editing, ...patch });
            try {
              await saveStepExecution(
                {
                  activation_id: activation.activationId,
                  procedure_code: activation.procedureCode,
                  step_id: editing.stepId,
                  step_no: editing.stepNo,
                  step_title: editing.title,
                  role_code: editing.roleCode,
                  institution: editing.institution,
                  status: patch.status ?? editing.status,
                  sla_minutes: editing.slaMinutes,
                  elapsed_minutes: clock?.elapsedMin ?? 0,
                  sla_met: clock ? !clock.breached : true,
                  is_critical: editing.critical,
                  blocker_reason: patch.blockerReason ?? '',
                  note: '',
                  output_document: editing.outputDocument,
                  waived: patch.status === 'pominięty',
                  waiver_justification: waiverJustification,
                },
                actor,
              );
              patchStep(activation.activationId, editing.stepNo, patch);
              // Odstąpienie od kroku jest decyzją, nie zmianą techniczną — musi
              // zostawić ślad w dzienniku, inaczej po zdarzeniu nikt go nie obroni.
              if (patch.status === 'pominięty') {
                await saveDecision(
                  {
                    activation_id: activation.activationId,
                    procedure_code: activation.procedureCode,
                    step_no: editing.stepNo,
                    decision_type: 'odstąpienie od kroku',
                    decided_by_role: actor.roleCode,
                    decided_by_name: actor.name,
                    subject: `Odstąpienie od kroku ${editing.stepNo}: ${editing.title}`,
                    rationale: waiverJustification,
                    classification: 'jawne',
                    corrects_decision_id: '',
                  },
                  actor,
                );
                addDecision(activation.activationId, {
                  decisionId: `${activation.activationId}-W${editing.stepNo}`,
                  offsetMin: 0,
                  stepNo: editing.stepNo,
                  decisionType: 'odstąpienie od kroku',
                  decidedByRole: actor.roleCode,
                  decidedByName: actor.name,
                  subject: `Odstąpienie od kroku ${editing.stepNo}: ${editing.title}`,
                  rationale: waiverJustification,
                  classification: 'jawne',
                });
              }
              setEditing(null);
              setToast(`Krok ${editing.stepNo}: ${patch.status ?? editing.status}`);
            } catch (e: unknown) {
              setToast(e instanceof Error ? e.message : String(e));
            }
          }}
        />
      )}

      <Toast message={toast} onDone={() => setToast(null)} />
    </div>
  );
}

function StepModal({
  step,
  activation,
  blockerOptions,
  onClose,
  onSubmit,
}: {
  step: LiveStep;
  activation: LiveActivation;
  blockerOptions: string[];
  onClose: () => void;
  onSubmit: (patch: Partial<LiveStep>, waiverJustification: string) => void;
}) {
  const { actor } = useScenario();
  const [status, setStatus] = useState<StepStatus>(step.status);
  const [blocker, setBlocker] = useState(step.blockerReason);
  const [justification, setJustification] = useState('');
  const isWaiver = status === 'pominięty';
  const canWaive = OWNER_ROLES.includes(actor.role);

  return (
    <Modal open title={`Krok ${step.stepNo} — ${activation.procedureCode}`} onClose={onClose} wide>
      <p className="mb-3 text-sm text-slate-800">{step.title}</p>
      <p className="mb-4 text-xs text-slate-500">
        {step.roleName} · {step.institution} · norma {minutesLabel(step.slaMinutes)} · dokument:{' '}
        {step.outputDocument}
      </p>

      <div className="grid gap-3 md:grid-cols-2">
        <Field label="Status">
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as StepStatus)}
            className={inputClass}
          >
            {STEP_STATUSES.map((s) => (
              <option key={s} value={s} disabled={s === 'pominięty' && !canWaive}>
                {s}
                {s === 'pominięty' && !canWaive ? ' (wymaga właściciela procedury)' : ''}
              </option>
            ))}
          </select>
        </Field>
        {status === 'zablokowany' && (
          <Field label="Przyczyna blokady" hint="Lista zasilona z historii blokad">
            <select value={blocker} onChange={(e) => setBlocker(e.target.value)} className={inputClass}>
              <option value="">— wskaż —</option>
              {blockerOptions.map((b) => (
                <option key={b} value={b}>
                  {b}
                </option>
              ))}
            </select>
          </Field>
        )}
        {isWaiver && (
          <div className="md:col-span-2">
            <Field
              label="Uzasadnienie odstąpienia"
              hint="Minimum 30 znaków; wpis trafia do dziennika decyzji"
            >
              <textarea
                value={justification}
                onChange={(e) => setJustification(e.target.value)}
                rows={3}
                className={inputClass}
              />
            </Field>
          </div>
        )}
      </div>

      <div className="mt-4 flex justify-end gap-2">
        <Button variant="ghost" onClick={onClose}>
          Anuluj
        </Button>
        <Button
          variant="primary"
          onClick={() => {
            const patch: Partial<LiveStep> = { status, blockerReason: status === 'zablokowany' ? blocker : '' };
            if (status === 'w toku' && step.startedOffsetMin === null) patch.startedOffsetMin = 0;
            if (status === 'wykonany') {
              if (step.startedOffsetMin === null) patch.startedOffsetMin = 0;
              patch.completedOffsetMin = 0;
            }
            onSubmit(patch, justification);
          }}
        >
          Zapisz zmianę
        </Button>
      </div>
      <p className="mt-3 text-[11px] text-slate-500">
        Zmiana tworzy zdarzenie w tabeli realizacji kroków — {formatNumber(activation.steps.length)}{' '}
        kroków tego uruchomienia widzi pulpit RCB w czasie rzeczywistym.
      </p>
    </Modal>
  );
}
