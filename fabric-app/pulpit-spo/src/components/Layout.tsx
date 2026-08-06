import { NavLink, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';

import { activationProgress, formatNumber } from '@/data/model';
import { useAuth } from '@/hooks/AuthContext';
import { useScenario } from '@/hooks/ScenarioContext';
import { USER_ROLES, canWrite, type UserRole } from '@/services/workflow';
import { Button } from '@/components/ui';

const NAV = [
  { to: '/', label: 'Zapytaj o procedurę' },
  { to: '/checklista', label: 'Checklista uruchomienia' },
  { to: '/dziennik', label: 'Dziennik decyzji' },
  { to: '/zadania', label: 'Moje zadania' },
  { to: '/po-zdarzeniu', label: 'Po zdarzeniu' },
];

/**
 * Pasek dyżuru.
 *
 * Zamiast suwaka czasu — bo tu nic się nie przewija — pokazuje to, co dyżurny
 * ma przed oczami: ile uruchomień jest otwartych i ile kroków przekroczyło normę.
 */
function DutyBar() {
  const { activations, closedIds, tick } = useScenario();
  void tick;
  const open = activations.filter((a) => !closedIds.includes(a.activationId));
  const totals = open.reduce(
    (acc, a) => {
      const p = activationProgress(a);
      return {
        breached: acc.breached + p.breached,
        blocked: acc.blocked + p.blocked,
        steps: acc.steps + p.total,
        done: acc.done + p.done,
      };
    },
    { breached: 0, blocked: 0, steps: 0, done: 0 },
  );
  const alarm = totals.breached > 0;

  return (
    <div className="flex flex-wrap items-center gap-3 border-b border-slate-200 bg-slate-100 px-5 py-2.5">
      <span className="flex w-32 items-center justify-center gap-2 rounded-lg bg-red-50 px-3 py-1.5 text-sm font-semibold text-red-700 ring-1 ring-red-600/40">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-red-500" />
        </span>
        DYŻUR
      </span>
      <span className="rounded-md bg-gov/15 px-2 py-1 text-xs font-semibold tabular-nums text-gov">
        {open.length} uruchomień otwartych
      </span>
      <span className="text-xs text-slate-600">
        kroki zamknięte {formatNumber(totals.done)} / {formatNumber(totals.steps)}
      </span>
      {totals.blocked > 0 && (
        <span className="rounded-md bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800 ring-1 ring-amber-600/30">
          {totals.blocked} zablokowanych
        </span>
      )}
      <span
        className={`rounded-md px-2 py-1 text-xs font-semibold tabular-nums ${
          alarm ? 'bg-red-50 text-red-700 ring-1 ring-red-600/30' : 'bg-slate-50 text-slate-600'
        }`}
      >
        {formatNumber(totals.breached)} kroków po normie
      </span>
    </div>
  );
}

function RolePicker() {
  const { actor, setRole, setRoleCode, index } = useScenario();
  const roles = index?.scene.roles ?? [];
  return (
    <div className="flex flex-wrap items-center gap-2">
      <select
        value={actor.role}
        onChange={(e) => setRole(e.target.value as UserRole)}
        className="rounded-lg bg-slate-50 px-2 py-1 text-xs text-slate-900 ring-1 ring-slate-300"
        aria-label="Rola użytkownika"
      >
        {USER_ROLES.map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
      </select>
      <select
        value={actor.roleCode}
        onChange={(e) => setRoleCode(e.target.value)}
        className="max-w-[260px] rounded-lg bg-slate-50 px-2 py-1 text-xs text-slate-900 ring-1 ring-slate-300"
        aria-label="Stanowisko w procedurze"
      >
        {roles.map((r) => (
          <option key={r.code} value={r.code}>
            {r.name}
          </option>
        ))}
      </select>
    </div>
  );
}

export function Layout({ children }: { children: ReactNode }) {
  const { signOut, user } = useAuth();
  const { writebackError, actor } = useScenario();
  const location = useLocation();
  const active = NAV.find((n) => n.to === location.pathname)?.label ?? '';

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <div className="h-1 w-full bg-gov" />
      <header className="border-b border-slate-200 bg-gradient-to-r from-white via-white to-slate-100">
        <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gov/15 text-gov ring-1 ring-gov/40">
              <span className="text-base font-bold">§</span>
            </div>
            <div>
              <h1 className="text-sm font-semibold tracking-wide text-slate-900">
                Asystent SPO · procedury i dziennik decyzji
              </h1>
              <p className="text-[11px] text-slate-500">
                Standardowe procedury operacyjne, checklisty i ślad audytowy · demonstracja
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <RolePicker />
            <span className="hidden text-xs text-slate-500 sm:inline">
              {user?.name ?? user?.email ?? ''}
            </span>
            <Button variant="ghost" onClick={() => void signOut()}>
              Wyloguj
            </Button>
          </div>
        </div>
        <nav className="flex gap-1 overflow-x-auto px-4">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              className={({ isActive }) =>
                `whitespace-nowrap border-b-2 px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? 'border-gov text-gov'
                    : 'border-transparent text-slate-500 hover:text-slate-900'
                }`
              }
            >
              {n.label}
            </NavLink>
          ))}
        </nav>
      </header>

      <DutyBar />

      {!canWrite(actor.role) && (
        <div className="border-b border-gov/30 bg-gov/10 px-5 py-2 text-xs text-gov-dark">
          Rola „analityk" ma wyłącznie dostęp do odczytu. Treść decyzji z klauzulą inną niż jawna
          jest zamaskowana — widoczny pozostaje sam fakt i czas decyzji.
        </div>
      )}

      {writebackError && (
        <div className="border-b border-amber-300 bg-amber-50 px-5 py-2 text-xs text-amber-700">
          Zapis do bazy aplikacji jest niedostępny ({writebackError}). Wpisy zapisują się lokalnie
          w sesji przeglądarki.
        </div>
      )}

      <main className="mx-auto max-w-[1500px] px-5 py-5">
        <p className="mb-3 text-[11px] uppercase tracking-widest text-slate-400">{active}</p>
        {children}
      </main>

      <footer className="border-t border-slate-200 px-5 py-3 text-[11px] text-slate-400">
        Dane są w całości syntetyczne. Procedury, kroki, role i dokumenty to konstrukcja
        demonstracyjna wzorowana na układzie standardowych procedur operacyjnych — żaden zapis nie
        odtwarza obowiązującego dokumentu. Historia 986 uruchomień została wygenerowana.
      </footer>
    </div>
  );
}
