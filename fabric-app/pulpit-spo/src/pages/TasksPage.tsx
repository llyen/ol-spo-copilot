import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import {
  formatNumber,
  minutesLabel,
  relativeLabel,
  statusTone,
  stepClock,
  type LiveActivation,
  type LiveStep,
} from '@/data/model';
import { useScenario } from '@/hooks/ScenarioContext';
import { Badge, Button, EmptyState, KpiCard, Panel } from '@/components/ui';

interface Task {
  activation: LiveActivation;
  step: LiveStep;
  remainingMin: number;
  breached: boolean;
  warning: boolean;
}

/**
 * Ekran 4 — „Moje zadania".
 *
 * Lista jest sortowana po czasie do przekroczenia normy, a nie po numerze kroku
 * czy dacie uruchomienia. Dyżurny ma na górze to, co zaraz przepadnie —
 * kolejność chronologiczna jest tu bezużyteczna.
 */
export function TasksPage() {
  const { activations, actor, closedIds, setCurrentId, index, tick } = useScenario();
  void tick;
  const navigate = useNavigate();

  const tasks = useMemo<Task[]>(() => {
    const open = activations.filter((a) => !closedIds.includes(a.activationId));
    const rows: Task[] = [];
    for (const a of open) {
      for (const s of a.steps) {
        if (s.roleCode !== actor.roleCode) continue;
        if (s.status === 'wykonany' || s.status === 'pominięty') continue;
        const clock = stepClock(s);
        // Krok jeszcze nierozpoczęty liczy się od normy — inaczej wszystkie
        // oczekujące zadania wyglądałyby na jednakowo pilne.
        const remaining = clock ? clock.remainingMin : s.slaMinutes;
        rows.push({
          activation: a,
          step: s,
          remainingMin: remaining,
          breached: remaining < 0,
          warning: !!clock?.warning,
        });
      }
    }
    return rows.sort((x, y) => x.remainingMin - y.remainingMin);
  }, [activations, actor.roleCode, closedIds]);

  const roleName = index?.roleByCode.get(actor.roleCode)?.name ?? actor.roleCode;
  const breached = tasks.filter((t) => t.breached).length;
  const blocked = tasks.filter((t) => t.step.status === 'zablokowany').length;

  return (
    <div className="space-y-4">
      <Panel
        title={`Zadania stanowiska: ${roleName}`}
        subtitle="Wszystkie otwarte uruchomienia, kolejność według czasu do przekroczenia normy"
        tone={breached > 0 ? 'alert' : 'accent'}
      >
        <div className="grid gap-3 md:grid-cols-4">
          <KpiCard label="Zadania otwarte" value={tasks.length} higherIsWorse={false} emphasis />
          <KpiCard label="Po normie" value={breached} hint="wymagają decyzji lub eskalacji" />
          <KpiCard label="Zablokowane" value={blocked} hint="czekają na usunięcie przeszkody" />
          <KpiCard
            label="Uruchomienia otwarte"
            value={new Set(tasks.map((t) => t.activation.activationId)).size}
            higherIsWorse={false}
          />
        </div>
      </Panel>

      {tasks.length === 0 ? (
        <EmptyState text="Brak zadań dla tego stanowiska. Zmień stanowisko w pasku u góry, żeby zobaczyć zadania innej roli." />
      ) : (
        <div className="space-y-2">
          {tasks.map((t) => (
            <div
              key={`${t.activation.activationId}-${t.step.stepId}`}
              className={`rounded-xl bg-white p-4 shadow-sm ring-1 ${
                t.breached
                  ? 'ring-red-600/40'
                  : t.warning
                    ? 'ring-amber-500/40'
                    : 'ring-slate-300'
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-[280px] flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-semibold text-gov">
                      {t.activation.procedureCode} · krok {t.step.stepNo}
                    </span>
                    <Badge className={statusTone(t.step.status)}>{t.step.status}</Badge>
                    {t.step.critical && (
                      <Badge className="bg-red-50 text-red-700 ring-red-600/30">krytyczny</Badge>
                    )}
                  </div>
                  <div className="mt-1 text-sm font-medium text-slate-900">{t.step.title}</div>
                  <div className="mt-1 text-[11px] text-slate-500">
                    {t.activation.activationId} · {t.activation.eventName} · norma{' '}
                    {minutesLabel(t.step.slaMinutes)} · dokument: {t.step.outputDocument}
                  </div>
                  {t.step.blockerReason && (
                    <div className="mt-1 text-xs text-amber-800">
                      Blokada: {t.step.blockerReason}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <div
                    className={`min-w-[130px] rounded-lg px-3 py-2 text-center text-sm font-semibold tabular-nums ${
                      t.breached
                        ? 'bg-red-50 text-red-700 ring-1 ring-red-600/30'
                        : t.warning
                          ? 'bg-amber-50 text-amber-800 ring-1 ring-amber-600/30'
                          : 'bg-emerald-50 text-emerald-800 ring-1 ring-emerald-600/30'
                    }`}
                  >
                    {t.breached
                      ? `po normie ${minutesLabel(-t.remainingMin)}`
                      : relativeLabel(t.remainingMin)}
                  </div>
                  <Button
                    onClick={() => {
                      setCurrentId(t.activation.activationId);
                      navigate('/checklista');
                    }}
                  >
                    Otwórz checklistę
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <Panel
        title="Skąd bierze się kolejność"
        subtitle="Reguła jest jawna, bo dyżurny musi rozumieć, dlaczego coś jest na górze"
      >
        <p className="text-sm leading-relaxed text-slate-700">
          Dla kroku rozpoczętego liczymy czas pozostały do normy od chwili rozpoczęcia. Dla kroku
          oczekującego przyjmujemy pełną normę — inaczej wszystkie oczekujące zadania miałyby ten
          sam priorytet i lista przestałaby cokolwiek podpowiadać. W danych historycznych mediana
          czasu do pierwszego kroku krytycznego wynosi{' '}
          {formatNumber(Number(index?.scene.meta.summary.median_time_to_first_critical_min ?? 0))}{' '}
          min — to jest wartość, którą ten ekran ma obniżać.
        </p>
      </Panel>
    </div>
  );
}
