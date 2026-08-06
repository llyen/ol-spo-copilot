import { useMemo, useState } from 'react';

import { formatOffset, type LiveDecision } from '@/data/model';
import { useScenario } from '@/hooks/ScenarioContext';
import {
  Badge,
  Button,
  EmptyState,
  Field,
  Modal,
  Panel,
  Toast,
  inputClass,
} from '@/components/ui';
import {
  CLASSIFICATIONS,
  DECISION_TYPES,
  canWrite,
  maskDecision,
  saveDecision,
} from '@/services/workflow';

const CLASSIFICATION_TONE: Record<string, string> = {
  jawne: 'bg-slate-50 text-slate-700 ring-slate-300',
  zastrzeżone: 'bg-amber-50 text-amber-800 ring-amber-600/30',
  poufne: 'bg-red-50 text-red-800 ring-red-600/30',
};

/**
 * Ekran 3 — „Dziennik decyzji".
 *
 * Wpisu nie da się zmienić ani usunąć — korekta powstaje jako nowy wpis
 * odsyłający do poprzedniego. Interfejs nie ma przycisku „edytuj" nie z
 * niedopatrzenia: to jedyny sposób, żeby dziennik był dowodem, a nie notatnikiem.
 */
export function DecisionLogPage() {
  const { activations, currentId, setCurrentId, actor, addDecision } = useScenario();
  const [toast, setToast] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [correcting, setCorrecting] = useState<LiveDecision | null>(null);

  const activation = useMemo(
    () => activations.find((a) => a.activationId === currentId) ?? activations[0] ?? null,
    [activations, currentId],
  );

  if (!activation) return <EmptyState text="Brak uruchomień do udokumentowania." />;

  const entries = activation.decisions.map((d) => maskDecision(d, actor.role));

  return (
    <div className="space-y-4">
      <Panel
        title={`Dziennik decyzji · ${activation.activationId}`}
        subtitle={`${activation.procedureCode} — ${activation.eventName}`}
        tone="accent"
        right={
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={activation.activationId}
              onChange={(e) => setCurrentId(e.target.value)}
              className="max-w-[300px] rounded-lg bg-slate-50 px-2 py-1 text-xs text-slate-900 ring-1 ring-slate-300"
              aria-label="Wybór uruchomienia"
            >
              {activations.map((a) => (
                <option key={a.activationId} value={a.activationId}>
                  {a.activationId} · {a.procedureCode}
                </option>
              ))}
            </select>
            <Button
              variant="primary"
              onClick={() => {
                setCorrecting(null);
                setFormOpen(true);
              }}
              disabled={!canWrite(actor.role)}
            >
              Nowy wpis
            </Button>
          </div>
        }
      >
        <p className="text-xs text-slate-600">
          {entries.length} wpisów. Wpisy są nieusuwalne i nieedytowalne — korekta to nowy wpis
          wskazujący poprzedni.
        </p>
      </Panel>

      <div className="space-y-2">
        {entries.map((d) => (
          <div
            key={d.decisionId}
            className="rounded-xl bg-white p-4 ring-1 ring-slate-300 shadow-sm"
          >
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-semibold tabular-nums text-gov">
                  {formatOffset(d.offsetMin)}
                </span>
                <Badge className="bg-gov/10 text-gov ring-gov/30">{d.decisionType}</Badge>
                <Badge className={CLASSIFICATION_TONE[d.classification] ?? CLASSIFICATION_TONE.jawne}>
                  {d.classification}
                </Badge>
                {d.stepNo > 0 && (
                  <span className="text-[11px] text-slate-500">krok {d.stepNo}</span>
                )}
              </div>
              <Button
                variant="ghost"
                onClick={() => {
                  setCorrecting(d);
                  setFormOpen(true);
                }}
                disabled={!canWrite(actor.role)}
                title="Korekta powstaje jako nowy wpis odsyłający do tego"
              >
                Skoryguj
              </Button>
            </div>
            <div className="mt-2 text-sm font-medium text-slate-900">{d.subject}</div>
            <p className="mt-1 text-sm leading-relaxed text-slate-700">{d.rationale}</p>
            <div className="mt-2 text-[11px] text-slate-500">
              {d.decidedByName} · {d.decidedByRole} · {d.decisionId}
            </div>
          </div>
        ))}
      </div>

      <DecisionModal
        open={formOpen}
        correcting={correcting}
        stepNumbers={activation.steps.map((s) => ({ no: s.stepNo, title: s.title }))}
        onClose={() => setFormOpen(false)}
        onSubmit={async (draft) => {
          try {
            const saved = await saveDecision(
              {
                ...draft,
                activation_id: activation.activationId,
                procedure_code: activation.procedureCode,
                decided_by_role: actor.roleCode,
                decided_by_name: actor.name,
              },
              actor,
            );
            addDecision(activation.activationId, {
              decisionId: saved.decision_id,
              offsetMin: 0,
              stepNo: draft.step_no,
              decisionType: draft.decision_type,
              decidedByRole: actor.roleCode,
              decidedByName: actor.name,
              subject: draft.subject,
              rationale: draft.rationale,
              classification: draft.classification,
            });
            setFormOpen(false);
            setToast(`Zapisano wpis ${saved.decision_id}`);
          } catch (e: unknown) {
            setToast(e instanceof Error ? e.message : String(e));
          }
        }}
      />

      <Toast message={toast} onDone={() => setToast(null)} />
    </div>
  );
}

function DecisionModal({
  open,
  correcting,
  stepNumbers,
  onClose,
  onSubmit,
}: {
  open: boolean;
  correcting: LiveDecision | null;
  stepNumbers: { no: number; title: string }[];
  onClose: () => void;
  onSubmit: (draft: {
    step_no: number;
    decision_type: string;
    subject: string;
    rationale: string;
    classification: string;
    corrects_decision_id: string;
  }) => void;
}) {
  const [type, setType] = useState<string>(DECISION_TYPES[2]);
  const [stepNo, setStepNo] = useState(0);
  const [subject, setSubject] = useState('');
  const [rationale, setRationale] = useState('');
  const [classification, setClassification] = useState<string>('jawne');

  return (
    <Modal
      open={open}
      title={correcting ? `Korekta wpisu ${correcting.decisionId}` : 'Nowy wpis do dziennika'}
      onClose={onClose}
      wide
    >
      {correcting && (
        <p className="mb-3 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800 ring-1 ring-amber-600/30">
          Pierwotny wpis pozostaje w dzienniku bez zmian. Ten wpis odeśle do niego przez pole
          korekty — tak wygląda poprawka w dokumencie, który ma wartość dowodową.
        </p>
      )}
      <div className="grid gap-3 md:grid-cols-2">
        <Field label="Typ decyzji">
          <select value={type} onChange={(e) => setType(e.target.value)} className={inputClass}>
            {DECISION_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Powiązany krok">
          <select
            value={stepNo}
            onChange={(e) => setStepNo(Number(e.target.value))}
            className={inputClass}
          >
            <option value={0}>— bez powiązania —</option>
            {stepNumbers.map((s) => (
              <option key={s.no} value={s.no}>
                {s.no}. {s.title}
              </option>
            ))}
          </select>
        </Field>
        <div className="md:col-span-2">
          <Field label="Przedmiot">
            <input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className={inputClass}
              placeholder="czego dotyczy decyzja"
            />
          </Field>
        </div>
        <div className="md:col-span-2">
          <Field label="Uzasadnienie" hint="Pole obowiązkowe — minimum 30 znaków">
            <textarea
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              rows={4}
              className={inputClass}
            />
          </Field>
        </div>
        <Field label="Klauzula">
          <select
            value={classification}
            onChange={(e) => setClassification(e.target.value)}
            className={inputClass}
          >
            {CLASSIFICATIONS.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </Field>
      </div>
      <div className="mt-4 flex justify-end gap-2">
        <Button variant="ghost" onClick={onClose}>
          Anuluj
        </Button>
        <Button
          variant="primary"
          onClick={() =>
            onSubmit({
              step_no: stepNo,
              decision_type: type,
              subject,
              rationale,
              classification,
              corrects_decision_id: correcting?.decisionId ?? '',
            })
          }
        >
          Zapisz wpis
        </Button>
      </div>
    </Modal>
  );
}
