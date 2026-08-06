import { useMemo, useState } from 'react';

import {
  activationProgress,
  formatNumber,
  formatOffset,
  minutesLabel,
  statusTone,
  stepClock,
  type LiveActivation,
} from '@/data/model';
import { useScenario } from '@/hooks/ScenarioContext';
import {
  Badge,
  Button,
  EmptyState,
  KpiCard,
  Panel,
  Toast,
  downloadCsv,
} from '@/components/ui';
import { OWNER_ROLES, maskDecision, saveDecision, saveLesson } from '@/services/workflow';

interface Finding {
  kind: string;
  stepNo: number;
  finding: string;
  historical: number;
  recommendation: string;
  ownerRole: string;
}

/**
 * Ekran 5 — „Po zdarzeniu".
 *
 * Wnioski nie są pisane od zera: powstają z porównania przebiegu z historią
 * 986 uruchomień. Zdanie „krok 4 przekroczył normę — to 18. taki przypadek
 * w tej procedurze" broni się samo, a „warto się przyjrzeć" nie broni się wcale.
 */
export function AfterActionPage() {
  const { activations, currentId, setCurrentId, actor, index, closedIds, closeActivation, tick } =
    useScenario();
  void tick;
  const [toast, setToast] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const activation = useMemo(
    () => activations.find((a) => a.activationId === currentId) ?? activations[0] ?? null,
    [activations, currentId],
  );

  const findings = useMemo<Finding[]>(() => {
    if (!activation || !index) return [];
    const worst = index.worstByCode.get(activation.procedureCode) ?? [];
    const blockers = index.scene.analytics.blockers;
    const out: Finding[] = [];

    for (const s of activation.steps) {
      const clock = stepClock(s);
      if (clock?.breached) {
        const hist = worst.find((w) => w.stepNo === s.stepNo);
        out.push({
          kind: 'przekroczenie normy',
          stepNo: s.stepNo,
          finding: `Krok ${s.stepNo} „${s.title}" przekroczył normę o ${minutesLabel(
            -clock.remainingMin,
          )}.`,
          historical: hist ? Math.round((hist.breachPct / 100) * hist.executions) : 0,
          recommendation: hist
            ? `Krok przekracza normę w ${formatNumber(hist.breachPct)}% wykonań historycznych ` +
              `(mediana ${minutesLabel(hist.medianMinutes)} przy normie ${minutesLabel(
                hist.slaMinutes,
              )}). Norma jest nierealna albo brakuje zasobu — wymaga rozstrzygnięcia przed kolejną aktualizacją procedury.`
            : 'Zweryfikować przyczynę opóźnienia i zasadność normy czasu dla tego kroku.',
          ownerRole: s.roleCode,
        });
      }
      if (s.status === 'zablokowany' && s.blockerReason) {
        const hist = blockers.find((b) => b.reason === s.blockerReason);
        out.push({
          kind: 'blokada',
          stepNo: s.stepNo,
          finding: `Krok ${s.stepNo} zablokowany: ${s.blockerReason}.`,
          historical: hist?.occurrences ?? 0,
          recommendation: hist
            ? `Ta sama przyczyna wystąpiła ${formatNumber(hist.occurrences)} razy w ${
                hist.procedures
              } procedurach na przestrzeni ${hist.years} lat. To nie jest incydent, tylko brak systemowy — wymaga właściciela i terminu usunięcia.`
            : 'Ustalić właściciela przeszkody i termin jej usunięcia.',
          ownerRole: s.roleCode,
        });
      }
      if (s.status === 'pominięty') {
        out.push({
          kind: 'poprawka procedury',
          stepNo: s.stepNo,
          finding: `Odstąpiono od kroku ${s.stepNo} „${s.title}".`,
          historical: 0,
          recommendation:
            'Sprawdzić, czy krok jest potrzebny w tej klasie zdarzeń, czy odstąpienie było wymuszone brakiem zasobu. Jeśli powtarza się — zmienić procedurę zamiast odstępować za każdym razem.',
          ownerRole: s.roleCode,
        });
      }
    }
    return out;
  }, [activation, index]);

  if (!activation || !index) return <EmptyState text="Brak uruchomień do rozliczenia." />;

  const progress = activationProgress(activation);
  const closed = closedIds.includes(activation.activationId);
  const canClose = OWNER_ROLES.includes(actor.role);
  const decisions = activation.decisions.map((d) => maskDecision(d, actor.role));

  const exportReport = () => {
    const lines = [
      'sekcja;pozycja;wartosc',
      ...activation.steps.map(
        (s) =>
          `kroki;${s.stepNo}. ${s.title.replace(/;/g, ',')};${s.status} / norma ${minutesLabel(
            s.slaMinutes,
          )}`,
      ),
      ...decisions.map(
        (d) => `decyzje;${d.decisionType};${d.subject.replace(/;/g, ',')} [${d.classification}]`,
      ),
      ...findings.map((f) => `wnioski;${f.kind};${f.finding.replace(/;/g, ',')}`),
    ];
    downloadCsv(`raport-${activation.activationId}.csv`, lines.join('\n'));
  };

  return (
    <div className="space-y-4">
      <Panel
        title={`Raport zamknięcia · ${activation.activationId}`}
        subtitle={`${activation.procedureCode} — ${activation.eventName}`}
        tone="accent"
        right={
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={activation.activationId}
              onChange={(e) => setCurrentId(e.target.value)}
              className="max-w-[280px] rounded-lg bg-slate-50 px-2 py-1 text-xs text-slate-900 ring-1 ring-slate-300"
              aria-label="Wybór uruchomienia"
            >
              {activations.map((a) => (
                <option key={a.activationId} value={a.activationId}>
                  {a.activationId} · {a.procedureCode}
                </option>
              ))}
            </select>
            <Button onClick={exportReport}>Pobierz raport</Button>
            <Button
              variant="primary"
              disabled={!canClose || closed || saving}
              title={canClose ? undefined : 'Procedurę zamyka właściciel procedury lub kierownictwo'}
              onClick={async () => {
                setSaving(true);
                try {
                  await saveDecision(
                    {
                      activation_id: activation.activationId,
                      procedure_code: activation.procedureCode,
                      step_no: 0,
                      decision_type: 'zamknięcie procedury',
                      decided_by_role: actor.roleCode,
                      decided_by_name: actor.name,
                      subject: `Zamknięcie uruchomienia ${activation.activationId}`,
                      rationale: `Zamknięto po realizacji ${progress.done} z ${progress.total} kroków. Ustalenia i wnioski zapisane w raporcie zamknięcia.`,
                      classification: 'jawne',
                      corrects_decision_id: '',
                    },
                    actor,
                  );
                  closeActivation(activation.activationId);
                  setToast('Uruchomienie zamknięte.');
                } catch (e: unknown) {
                  setToast(e instanceof Error ? e.message : String(e));
                } finally {
                  setSaving(false);
                }
              }}
            >
              {closed ? 'Zamknięte' : 'Zamknij uruchomienie'}
            </Button>
          </div>
        }
      >
        <div className="grid gap-3 lg:grid-cols-4">
          <KpiCard
            label="Kroki zamknięte"
            value={progress.done}
            higherIsWorse={false}
            hint={`z ${progress.total} w procedurze`}
            emphasis
          />
          <KpiCard label="Przekroczenia normy" value={progress.breached} />
          <KpiCard label="Blokady" value={progress.blocked} />
          <KpiCard
            label="Wpisy w dzienniku"
            value={decisions.length}
            higherIsWorse={false}
            hint={`${decisions.filter((d) => d.classification !== 'jawne').length} z klauzulą`}
          />
        </div>
      </Panel>

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title="Przebieg kroków" subtitle="Stan na chwilę zamknięcia">
          <div className="space-y-1.5">
            {activation.steps.map((s) => {
              const clock = stepClock(s);
              return (
                <div
                  key={s.stepId}
                  className="flex items-start justify-between gap-2 border-b border-slate-100 pb-1.5"
                >
                  <div className="min-w-0">
                    <div className="truncate text-sm text-slate-900">
                      {s.stepNo}. {s.title}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      {s.roleName} · norma {minutesLabel(s.slaMinutes)}
                      {clock ? ` · wykonanie ${minutesLabel(clock.elapsedMin)}` : ''}
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-1.5">
                    {clock?.breached && (
                      <Badge className="bg-red-50 text-red-700 ring-red-600/30">po normie</Badge>
                    )}
                    <Badge className={statusTone(s.status)}>{s.status}</Badge>
                  </div>
                </div>
              );
            })}
          </div>
        </Panel>

        <Panel title="Dziennik decyzji" subtitle="Pełny ślad audytowy uruchomienia">
          <div className="space-y-2">
            {decisions.map((d) => (
              <div key={d.decisionId} className="rounded-lg bg-slate-50 p-3 ring-1 ring-slate-200">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[11px] font-semibold tabular-nums text-gov">
                    {formatOffset(d.offsetMin)}
                  </span>
                  <Badge className="bg-gov/10 text-gov ring-gov/30">{d.decisionType}</Badge>
                  <Badge className="bg-slate-100 text-slate-600 ring-slate-300">
                    {d.classification}
                  </Badge>
                </div>
                <div className="mt-1 text-sm text-slate-900">{d.subject}</div>
                <p className="mt-0.5 line-clamp-2 text-xs text-slate-600">{d.rationale}</p>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <Panel
        title="Propozycje wniosków"
        subtitle="Powstają z porównania przebiegu z historią — liczba powtórzeń jest argumentem"
        tone={findings.length ? 'alert' : 'default'}
      >
        {findings.length === 0 ? (
          <EmptyState text="Przebieg bez przekroczeń i blokad — brak materiału na wnioski." />
        ) : (
          <div className="space-y-2">
            {findings.map((f, i) => (
              <div
                key={`${f.kind}-${f.stepNo}-${i}`}
                className="rounded-lg bg-white p-3 ring-1 ring-slate-300"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <Badge className="bg-amber-50 text-amber-800 ring-amber-600/30">{f.kind}</Badge>
                  {f.historical > 0 && (
                    <span className="text-[11px] tabular-nums text-slate-500">
                      w historii: {formatNumber(f.historical)} przypadków
                    </span>
                  )}
                </div>
                <div className="mt-1 text-sm font-medium text-slate-900">{f.finding}</div>
                <p className="mt-1 text-xs leading-relaxed text-slate-600">{f.recommendation}</p>
                <div className="mt-2 flex justify-end">
                  <Button
                    disabled={!OWNER_ROLES.includes(actor.role)}
                    onClick={async () => {
                      try {
                        await saveLesson(
                          {
                            activation_id: activation.activationId,
                            procedure_code: activation.procedureCode,
                            finding_kind: f.kind,
                            step_no: f.stepNo,
                            finding: f.finding,
                            historical_occurrences: f.historical,
                            recommendation: f.recommendation,
                            owner_role: f.ownerRole,
                            due_date: '',
                            accepted: true,
                          },
                          actor,
                        );
                        setToast('Wniosek zapisany w rejestrze.');
                      } catch (e: unknown) {
                        setToast(e instanceof Error ? e.message : String(e));
                      }
                    }}
                  >
                    Przyjmij wniosek
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Panel>

      <ClosedNote activation={activation} closed={closed} />
      <Toast message={toast} onDone={() => setToast(null)} />
    </div>
  );
}

function ClosedNote({ activation, closed }: { activation: LiveActivation; closed: boolean }) {
  if (!closed) return null;
  return (
    <div className="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-900 ring-1 ring-emerald-600/30">
      Uruchomienie {activation.activationId} zostało zamknięte. Wpisy dziennika pozostają dostępne
      do odczytu — zamknięcie nie usuwa ani nie modyfikuje żadnego z nich.
    </div>
  );
}
