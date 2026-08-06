import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import {
  formatNumber,
  minutesLabel,
  type LiveActivation,
  type LiveStep,
  type Procedure,
} from '@/data/model';
import { buildAnswer, type AnswerCard } from '@/data/retrieval';
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
  LEVELS,
  OPERATIONAL_ROLES,
  saveActivation,
  saveFeedback,
  VERDICTS,
} from '@/services/workflow';

/**
 * Ekran 1 — „Zapytaj o procedurę".
 *
 * Cały ciężar tego ekranu jest w pierwszej sekundzie: dyżurny ma zobaczyć kod
 * procedury i pierwszy krok krytyczny, zanim zacznie czytać cokolwiek innego.
 * Reszta karty — checklista, kontakty, cytowania, historia — jest po to, żeby
 * nie musiał otwierać żadnego dokumentu.
 */
export function AskPage() {
  const { index, retriever, actor, addActivation } = useScenario();
  const navigate = useNavigate();
  const [question, setQuestion] = useState('');
  const [card, setCard] = useState<AnswerCard | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [runOpen, setRunOpen] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  const scene = index?.scene ?? null;
  const threshold = scene?.meta.confidenceThreshold ?? 0.45;

  const ask = useCallback(
    (text: string) => {
      if (!retriever || !index || !text.trim()) return;
      setQuestion(text);
      setCard(buildAnswer(retriever, text, index.procedureByCode, threshold));
    },
    [retriever, index, threshold],
  );

  const pick = useCallback(
    (code: string) => {
      if (!index || !retriever) return;
      const procedure = index.procedureByCode.get(code);
      if (!procedure || !card) return;
      setCard({
        ...card,
        procedure,
        ambiguous: false,
        alternatives: card.alternatives.filter((a) => a.procedure.code !== code),
        firstCriticalStep: procedure.steps.find((s) => s.critical) ?? null,
      });
    },
    [index, retriever, card],
  );

  const roleContacts = useMemo(() => {
    if (!card?.procedure || !index) return [];
    const codes = [...new Set(card.procedure.steps.map((s) => s.roleCode))];
    return codes.map((c) => index.roleByCode.get(c)).filter((r) => r !== undefined);
  }, [card, index]);

  const worst = useMemo(() => {
    if (!card?.procedure || !index) return null;
    const rows = index.worstByCode.get(card.procedure.code) ?? [];
    return rows.length ? rows.reduce((a, b) => (a.breachPct > b.breachPct ? a : b)) : null;
  }, [card, index]);

  if (!scene || !retriever) {
    return <EmptyState text="Wczytywanie korpusu procedur…" />;
  }

  return (
    <div className="space-y-4">
      <Panel
        title="Pytanie oficera dyżurnego"
        subtitle={`Korpus: ${formatNumber(scene.meta.counts.chunks)} fragmentów z ${formatNumber(
          scene.meta.counts.documents,
        )} dokumentów · trafność wskazania procedury ${formatNumber(
          scene.meta.retrieval.top1_accuracy * 100,
        )}%`}
        tone="accent"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            ask(question);
          }}
          className="flex flex-wrap gap-2"
        >
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="np. mamy skażenie chemiczne w porcie, co robimy?"
            className={`${inputClass} min-w-[320px] flex-1 text-base`}
            aria-label="Pytanie o procedurę"
          />
          <Button type="submit" variant="primary" disabled={!question.trim()}>
            Znajdź procedurę
          </Button>
        </form>

        <div className="mt-3 flex flex-wrap gap-1.5">
          {scene.sampleQuestions.slice(0, 6).map((q) => (
            <button
              key={q.id}
              type="button"
              onClick={() => ask(q.question)}
              className="rounded-full bg-slate-50 px-3 py-1 text-[11px] text-slate-600 ring-1 ring-slate-300 transition-colors hover:bg-slate-200 hover:text-slate-900"
            >
              {q.question}
            </button>
          ))}
        </div>
      </Panel>

      {!card && (
        <EmptyState text="Zadaj pytanie albo kliknij jedną z podpowiedzi. Odpowiedź powstaje lokalnie, bez zapytania do usługi — aplikacja działa przy ograniczonej łączności." />
      )}

      {card && card.ambiguous && (
        <Panel
          title="Pewność poniżej progu — wskaż procedurę"
          subtitle={`Pewność dopasowania ${formatNumber(card.confidence * 100)}% przy progu ${formatNumber(
            threshold * 100,
          )}%. Asystent nie wskazuje jednej procedury.`}
          tone="alert"
        >
          <div className="grid gap-2 md:grid-cols-3">
            {[
              card.procedure ? { procedure: card.procedure, confidence: card.confidence } : null,
              ...card.alternatives,
            ]
              .filter((c) => c !== null)
              .map((c) => (
                <button
                  key={c.procedure.code}
                  type="button"
                  onClick={() => pick(c.procedure.code)}
                  className="rounded-lg bg-slate-50 p-3 text-left ring-1 ring-slate-300 transition-colors hover:bg-white hover:ring-gov/40"
                >
                  <div className="text-sm font-semibold text-gov">{c.procedure.code}</div>
                  <div className="mt-0.5 text-xs text-slate-700">{c.procedure.name}</div>
                  <div className="mt-1 text-[11px] tabular-nums text-slate-500">
                    dopasowanie {formatNumber(c.confidence * 100)}%
                  </div>
                </button>
              ))}
          </div>
          <p className="mt-3 text-xs text-slate-500">
            Doprecyzuj pytanie albo wybierz procedurę ręcznie. Wybór jest zapisywany razem
            z pytaniem — to materiał do poprawy korpusu.
          </p>
        </Panel>
      )}

      {card?.procedure && !card.ambiguous && (
        <AnswerCardView
          card={card}
          procedure={card.procedure}
          contacts={roleContacts}
          worst={worst}
          onRun={() => setRunOpen(true)}
          onWrong={() => setFeedbackOpen(true)}
          onAlternative={pick}
        />
      )}

      {card?.procedure && (
        <RunModal
          open={runOpen}
          onClose={() => setRunOpen(false)}
          card={card}
          procedure={card.procedure}
          busy={busy}
          onSubmit={async (draft) => {
            setBusy(true);
            try {
              const saved = await saveActivation(draft, actor);
              const activation = toLiveActivation(saved.activation_id, card.procedure!, draft);
              addActivation(activation);
              setRunOpen(false);
              setToast(`Uruchomiono ${draft.procedure_code} — ${saved.activation_id}`);
              navigate('/checklista');
            } catch (e: unknown) {
              setToast(e instanceof Error ? e.message : String(e));
            } finally {
              setBusy(false);
            }
          }}
        />
      )}

      {card && (
        <FeedbackModal
          open={feedbackOpen}
          onClose={() => setFeedbackOpen(false)}
          card={card}
          procedures={scene.procedures}
          onSubmit={async (verdict, corrected, comment) => {
            try {
              await saveFeedback(
                {
                  question: card.question,
                  top_procedure: card.procedure?.code ?? '',
                  confidence: card.confidence,
                  corrected_procedure: corrected,
                  verdict,
                  ambiguous: card.ambiguous,
                  cited_chunk_ids: card.citations.map((c) => c.chunk.id).join('|'),
                  latency_ms: card.latencyMs,
                  comment,
                },
                actor,
              );
              setFeedbackOpen(false);
              setToast('Zgłoszenie zapisane — trafi do przeglądu korpusu.');
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

/* ------------------------------------------------------------------ */

function AnswerCardView({
  card,
  procedure,
  contacts,
  worst,
  onRun,
  onWrong,
  onAlternative,
}: {
  card: AnswerCard;
  procedure: Procedure;
  contacts: { code: string; name: string; institution: string; level: string }[];
  worst: { stepNo: number; title: string; breachPct: number; executions: number } | null;
  onRun: () => void;
  onWrong: () => void;
  onAlternative: (code: string) => void;
}) {
  const { actor } = useScenario();
  return (
    <div className="space-y-4">
      <Panel
        title={`${procedure.code} — ${procedure.name}`}
        subtitle={`${procedure.ownerInstitution} · faza: ${procedure.phase} · ${procedure.legalBasis}`}
        tone="accent"
        right={
          <div className="flex gap-2">
            <Button variant="ghost" onClick={onWrong}>
              To nie ta procedura
            </Button>
            <Button
              variant="primary"
              onClick={onRun}
              disabled={!OPERATIONAL_ROLES.includes(actor.role)}
              title={
                OPERATIONAL_ROLES.includes(actor.role)
                  ? 'Utwórz uruchomienie i otwórz checklistę'
                  : 'Procedurę uruchamia oficer dyżurny lub właściciel procedury'
              }
            >
              Uruchom procedurę
            </Button>
          </div>
        }
      >
        <div className="grid gap-3 lg:grid-cols-4">
          <KpiCard
            label="Pewność dopasowania"
            value={Math.round(card.confidence * 1000) / 10}
            unit="%"
            higherIsWorse={false}
            emphasis
            hint={`Odpowiedź w ${card.latencyMs} ms, lokalnie w przeglądarce`}
          />
          <KpiCard
            label="Kroki procedury"
            value={procedure.steps.length}
            hint={`w tym ${procedure.criticalStepCount} krytycznych`}
            higherIsWorse={false}
          />
          <KpiCard
            label="Czas normatywny całości"
            value={Math.round((procedure.totalSlaMinutes / 1440) * 10) / 10}
            unit=" doby"
            hint={minutesLabel(procedure.totalSlaMinutes)}
          />
          <KpiCard
            label="Dotrzymanie norm w historii"
            value={procedure.history?.slaCompliancePct ?? 0}
            unit="%"
            higherIsWorse={false}
            hint={`${formatNumber(procedure.history?.activations ?? 0)} uruchomień w danych`}
          />
        </div>

        {card.firstCriticalStep && (
          <div className="mt-4 rounded-xl bg-gov/10 p-4 ring-1 ring-gov/30">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-gov">
              Pierwszy krok krytyczny
            </div>
            <div className="mt-1 text-base font-semibold text-slate-900">
              {card.firstCriticalStep.stepNo}. {card.firstCriticalStep.title}
            </div>
            <div className="mt-1 text-xs text-slate-600">
              {card.firstCriticalStep.roleName} · {card.firstCriticalStep.institution} · norma{' '}
              {minutesLabel(card.firstCriticalStep.slaMinutes)} · dokument:{' '}
              {card.firstCriticalStep.outputDocument}
            </div>
          </div>
        )}

        {card.alternatives.length > 0 && (
          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-500">
            <span>Alternatywy:</span>
            {card.alternatives.map((a) => (
              <button
                key={a.procedure.code}
                type="button"
                onClick={() => onAlternative(a.procedure.code)}
                className="rounded-full bg-slate-50 px-2.5 py-1 text-[11px] text-slate-700 ring-1 ring-slate-300 hover:bg-slate-200"
              >
                {a.procedure.code} · {formatNumber(a.confidence * 100)}%
              </button>
            ))}
          </div>
        )}
      </Panel>

      <div className="grid gap-4 xl:grid-cols-3">
        <Panel title="Checklista" subtitle="Kroki w kolejności, z odpowiedzialnym i normą czasu"
               className="xl:col-span-2">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-[11px] uppercase tracking-wider text-slate-500">
                  <th className="py-2 pr-2">#</th>
                  <th className="py-2 pr-2">Krok</th>
                  <th className="py-2 pr-2">Odpowiedzialny</th>
                  <th className="py-2 pr-2 text-right">Norma</th>
                  <th className="py-2">Dokument</th>
                </tr>
              </thead>
              <tbody>
                {procedure.steps.map((s) => (
                  <tr key={s.stepId} className="border-b border-slate-100 align-top">
                    <td className="py-2 pr-2 tabular-nums text-slate-500">{s.stepNo}</td>
                    <td className="py-2 pr-2">
                      <div className="text-slate-900">{s.title}</div>
                      {s.critical && (
                        <Badge className="mt-1 bg-red-50 text-red-700 ring-red-600/30">
                          krok krytyczny
                        </Badge>
                      )}
                    </td>
                    <td className="py-2 pr-2 text-xs text-slate-600">
                      {s.roleName}
                      <div className="text-slate-400">{s.institution}</div>
                    </td>
                    <td className="py-2 pr-2 text-right tabular-nums text-slate-700">
                      {minutesLabel(s.slaMinutes)}
                    </td>
                    <td className="py-2 text-xs text-slate-500">{s.outputDocument}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <div className="space-y-4">
          <Panel title="Lista telefoniczna" subtitle="Role i instytucje uczestniczące">
            <ul className="space-y-2">
              {contacts.map((r) => (
                <li
                  key={r.code}
                  className="flex items-start justify-between gap-2 rounded-lg bg-slate-50 px-3 py-2 ring-1 ring-slate-200"
                >
                  <div>
                    <div className="text-sm text-slate-900">{r.name}</div>
                    <div className="text-[11px] text-slate-500">
                      {r.institution} · poziom {r.level}
                    </div>
                  </div>
                  <Badge className="bg-gov/10 text-gov ring-gov/30">powiadom</Badge>
                </li>
              ))}
            </ul>
          </Panel>

          <Panel title="Jak nam szło" subtitle="Z historii uruchomień tej procedury">
            {procedure.history ? (
              <div className="space-y-2 text-sm">
                <Row label="Uruchomienia w danych" value={formatNumber(procedure.history.activations)} />
                <Row
                  label="Dotrzymanie norm"
                  value={`${formatNumber(procedure.history.slaCompliancePct)}%`}
                />
                <Row
                  label="Mediana czasu kroku"
                  value={minutesLabel(procedure.history.medianMinutes)}
                />
                <Row
                  label="Do pierwszego kroku krytycznego"
                  value={minutesLabel(procedure.history.timeToFirstCriticalMin)}
                />
                <Row label="Kroki zablokowane" value={formatNumber(procedure.history.blocked)} />
                {worst && (
                  <p className="mt-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800 ring-1 ring-amber-600/30">
                    Najczęściej przekraczany: krok {worst.stepNo} „{worst.title}" —{' '}
                    {formatNumber(worst.breachPct)}% przekroczeń na {formatNumber(worst.executions)}{' '}
                    wykonań.
                  </p>
                )}
              </div>
            ) : (
              <EmptyState text="Brak historii dla tej procedury." />
            )}
          </Panel>
        </div>
      </div>

      <Panel
        title="Cytowania"
        subtitle="Każde zdanie karty ma źródło — bez fragmentu korpusu nie ma odpowiedzi"
      >
        <div className="grid gap-2 lg:grid-cols-2">
          {card.citations.map((c) => (
            <div key={c.chunk.id} className="rounded-lg bg-slate-50 p-3 ring-1 ring-slate-200">
              <div className="flex items-baseline justify-between gap-2">
                <span className="text-xs font-semibold text-gov">
                  {c.chunk.id} · {c.chunk.procedureCode || c.chunk.docType}
                </span>
                <span className="text-[11px] tabular-nums text-slate-500">
                  dopasowanie {formatNumber(c.score * 100)}%
                </span>
              </div>
              <div className="mt-1 text-[11px] uppercase tracking-wide text-slate-500">
                {c.chunk.docTitle} · {c.chunk.section}
              </div>
              <p className="mt-1 line-clamp-4 text-xs leading-relaxed text-slate-700">
                {c.chunk.text}
              </p>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-2 border-b border-slate-100 pb-1">
      <span className="text-xs text-slate-500">{label}</span>
      <span className="tabular-nums text-slate-900">{value}</span>
    </div>
  );
}

/* ------------------------------------------------------------------ */

/** Buduje uruchomienie w toku z wybranej procedury — wszystkie kroki oczekują. */
function toLiveActivation(
  activationId: string,
  procedure: Procedure,
  draft: {
    event_name: string;
    hazard_code: string;
    level: string;
    voivodeship_code: string;
    voivodeship_name: string;
    trigger_text: string;
  },
): LiveActivation {
  const steps: LiveStep[] = procedure.steps.map((s) => ({
    ...s,
    status: 'oczekuje',
    startedOffsetMin: null,
    completedOffsetMin: null,
    blockerReason: '',
  }));
  return {
    activationId,
    procedureCode: procedure.code,
    procedureName: procedure.name,
    eventName: draft.event_name,
    hazardCode: draft.hazard_code,
    level: draft.level,
    voivodeshipCode: draft.voivodeship_code,
    voivodeshipName: draft.voivodeship_name,
    initiatedByRole: procedure.ownerRole,
    initiatedByInstitution: procedure.ownerInstitution,
    triggerText: draft.trigger_text,
    startedOffsetMin: 0,
    ownerRoleCode: procedure.ownerRole,
    firstStepRole: procedure.steps[0]?.roleCode ?? '',
    steps,
    decisions: [
      {
        decisionId: `${activationId}-D00`,
        offsetMin: 0,
        stepNo: 0,
        decisionType: 'uruchomienie procedury',
        decidedByRole: procedure.ownerRole,
        decidedByName: procedure.ownerInstitution,
        subject: `Uruchomienie ${procedure.code} — ${draft.event_name}`,
        rationale: draft.trigger_text,
        classification: 'jawne',
      },
    ],
  };
}

const VOIVODESHIPS: { code: string; name: string }[] = [
  { code: '02', name: 'dolnośląskie' },
  { code: '04', name: 'kujawsko-pomorskie' },
  { code: '06', name: 'lubelskie' },
  { code: '08', name: 'lubuskie' },
  { code: '10', name: 'łódzkie' },
  { code: '12', name: 'małopolskie' },
  { code: '14', name: 'mazowieckie' },
  { code: '16', name: 'opolskie' },
  { code: '18', name: 'podkarpackie' },
  { code: '20', name: 'podlaskie' },
  { code: '22', name: 'pomorskie' },
  { code: '24', name: 'śląskie' },
  { code: '26', name: 'świętokrzyskie' },
  { code: '28', name: 'warmińsko-mazurskie' },
  { code: '30', name: 'wielkopolskie' },
  { code: '32', name: 'zachodniopomorskie' },
];

function RunModal({
  open,
  onClose,
  card,
  procedure,
  busy,
  onSubmit,
}: {
  open: boolean;
  onClose: () => void;
  card: AnswerCard;
  procedure: Procedure;
  busy: boolean;
  onSubmit: (draft: {
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
  }) => void;
}) {
  const [eventName, setEventName] = useState('');
  const [level, setLevel] = useState<string>('krajowy');
  const [voiv, setVoiv] = useState('');
  const [hazard, setHazard] = useState(procedure.hazards[0]?.code ?? '');
  const [trigger, setTrigger] = useState(card.question);

  const voivName = VOIVODESHIPS.find((v) => v.code === voiv)?.name ?? '';

  return (
    <Modal open={open} title={`Uruchom ${procedure.code}`} onClose={onClose} wide>
      <div className="grid gap-3 md:grid-cols-2">
        <Field label="Zdarzenie" hint="Nazwa, pod którą uruchomienie będzie widoczne w raportach">
          <input
            value={eventName}
            onChange={(e) => setEventName(e.target.value)}
            className={inputClass}
            placeholder="np. Powódź wrześniowa — komunikacja z ludnością"
          />
        </Field>
        <Field label="Zagrożenie">
          <select value={hazard} onChange={(e) => setHazard(e.target.value)} className={inputClass}>
            {procedure.hazards.map((h) => (
              <option key={h.code} value={h.code}>
                {h.code} {h.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Poziom">
          <select value={level} onChange={(e) => setLevel(e.target.value)} className={inputClass}>
            {LEVELS.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
        </Field>
        <Field
          label="Województwo"
          hint="Wymagane dla poziomu wojewódzkiego i powiatowego"
        >
          <select value={voiv} onChange={(e) => setVoiv(e.target.value)} className={inputClass}>
            <option value="">— zakres krajowy —</option>
            {VOIVODESHIPS.map((v) => (
              <option key={v.code} value={v.code}>
                {v.name}
              </option>
            ))}
          </select>
        </Field>
        <div className="md:col-span-2">
          <Field
            label="Uzasadnienie uruchomienia"
            hint="Trafia do dziennika decyzji jako pierwszy wpis — minimum 30 znaków"
          >
            <textarea
              value={trigger}
              onChange={(e) => setTrigger(e.target.value)}
              rows={3}
              className={inputClass}
            />
          </Field>
        </div>
      </div>
      <div className="mt-4 flex justify-end gap-2">
        <Button variant="ghost" onClick={onClose}>
          Anuluj
        </Button>
        <Button
          variant="primary"
          disabled={busy}
          onClick={() =>
            onSubmit({
              procedure_code: procedure.code,
              procedure_name: procedure.name,
              event_name: eventName,
              hazard_code: hazard,
              level,
              voivodeship_code: voiv,
              voivodeship_name: voivName,
              trigger_text: trigger,
              confidence: card.confidence,
              source_question: card.question,
              from_assistant: true,
              status: 'otwarte',
            })
          }
        >
          {busy ? 'Zapisywanie…' : 'Uruchom i otwórz checklistę'}
        </Button>
      </div>
    </Modal>
  );
}

function FeedbackModal({
  open,
  onClose,
  card,
  procedures,
  onSubmit,
}: {
  open: boolean;
  onClose: () => void;
  card: AnswerCard;
  procedures: Procedure[];
  onSubmit: (verdict: string, corrected: string, comment: string) => void;
}) {
  const [verdict, setVerdict] = useState<string>('zła procedura');
  const [corrected, setCorrected] = useState('');
  const [comment, setComment] = useState('');
  return (
    <Modal open={open} title="Zgłoszenie do korpusu" onClose={onClose}>
      <p className="mb-3 text-xs text-slate-600">
        Pytanie: „{card.question}" · wskazanie: {card.procedure?.code ?? '—'} (
        {formatNumber(card.confidence * 100)}%)
      </p>
      <div className="grid gap-3">
        <Field label="Ocena odpowiedzi">
          <select value={verdict} onChange={(e) => setVerdict(e.target.value)} className={inputClass}>
            {VERDICTS.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        </Field>
        {verdict === 'zła procedura' && (
          <Field label="Właściwa procedura">
            <select
              value={corrected}
              onChange={(e) => setCorrected(e.target.value)}
              className={inputClass}
            >
              <option value="">— wskaż —</option>
              {procedures.map((p) => (
                <option key={p.code} value={p.code}>
                  {p.code} — {p.name}
                </option>
              ))}
            </select>
          </Field>
        )}
        <Field label="Komentarz" hint="Nieobowiązkowy">
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={3}
            className={inputClass}
          />
        </Field>
      </div>
      <div className="mt-4 flex justify-end gap-2">
        <Button variant="ghost" onClick={onClose}>
          Anuluj
        </Button>
        <Button variant="primary" onClick={() => onSubmit(verdict, corrected, comment)}>
          Zapisz zgłoszenie
        </Button>
      </div>
    </Modal>
  );
}
