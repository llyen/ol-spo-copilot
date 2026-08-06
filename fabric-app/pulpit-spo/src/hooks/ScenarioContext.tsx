import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import {
  indexScene,
  type LiveActivation,
  type LiveDecision,
  type LiveStep,
  type Scene,
  type SceneIndex,
} from '@/data/model';
import { Retriever } from '@/data/retrieval';
import { useAuth } from '@/hooks/AuthContext';
import {
  listActivations,
  listDecisions,
  listFeedback,
  listLessons,
  listStepExecutions,
  type Actor,
  type ActivationRecord,
  type AssistantFeedbackRecord,
  type DecisionLogRecord,
  type LessonLearnedRecord,
  type StepExecutionRecord,
  type UserRole,
} from '@/services/workflow';

interface ScenarioValue {
  index: SceneIndex | null;
  retriever: Retriever | null;
  loading: boolean;
  error: string | null;
  /** Rośnie co minutę — wymusza przeliczenie zegarów kroków. */
  tick: number;
  actor: Actor;
  setRole: (role: UserRole) => void;
  setRoleCode: (code: string) => void;
  /** Uruchomienia w toku: te ze sceny plus utworzone w tej sesji. */
  activations: LiveActivation[];
  /** Uruchomienie wybrane na ekranie checklisty i dziennika. */
  currentId: string;
  setCurrentId: (id: string) => void;
  addActivation: (activation: LiveActivation) => void;
  patchStep: (activationId: string, stepNo: number, patch: Partial<LiveStep>) => void;
  addDecision: (activationId: string, decision: LiveDecision) => void;
  closeActivation: (activationId: string) => void;
  closedIds: string[];
  savedActivations: ActivationRecord[];
  savedExecutions: StepExecutionRecord[];
  savedDecisions: DecisionLogRecord[];
  savedFeedback: AssistantFeedbackRecord[];
  savedLessons: LessonLearnedRecord[];
  refresh: () => Promise<void>;
  writebackError: string | null;
}

const ScenarioContext = createContext<ScenarioValue | undefined>(undefined);

const ROLE_KEY = 'spo.role';
const ROLE_CODE_KEY = 'spo.roleCode';

export function ScenarioProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [index, setIndex] = useState<SceneIndex | null>(null);
  const [retriever, setRetriever] = useState<Retriever | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const [role, setRoleState] = useState<UserRole>(
    () => (localStorage.getItem(ROLE_KEY) as UserRole) || 'oficer dyżurny',
  );
  const [roleCode, setRoleCodeState] = useState(
    () => localStorage.getItem(ROLE_CODE_KEY) || 'R_DYZ_RCB',
  );
  const [extraActivations, setExtraActivations] = useState<LiveActivation[]>([]);
  const [stepPatches, setStepPatches] = useState<Record<string, Partial<LiveStep>>>({});
  const [extraDecisions, setExtraDecisions] = useState<Record<string, LiveDecision[]>>({});
  const [closedIds, setClosedIds] = useState<string[]>([]);
  const [currentId, setCurrentId] = useState('');
  const [savedActivations, setSavedActivations] = useState<ActivationRecord[]>([]);
  const [savedExecutions, setSavedExecutions] = useState<StepExecutionRecord[]>([]);
  const [savedDecisions, setSavedDecisions] = useState<DecisionLogRecord[]>([]);
  const [savedFeedback, setSavedFeedback] = useState<AssistantFeedbackRecord[]>([]);
  const [savedLessons, setSavedLessons] = useState<LessonLearnedRecord[]>([]);
  const [writebackError, setWritebackError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`${import.meta.env.BASE_URL}data/scene.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`Nie udało się wczytać sceny (HTTP ${r.status}).`);
        return r.json() as Promise<Scene>;
      })
      .then((scene) => {
        if (cancelled) return;
        const idx = indexScene(scene);
        setIndex(idx);
        setRetriever(new Retriever(scene.chunks, scene.index));
        setCurrentId(scene.liveActivations[0]?.activationId ?? '');
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  /**
   * Zegar aplikacji.
   *
   * Czasy kroków są zapisane względem chwili wejścia, więc bez tego licznika
   * zegary stałyby w miejscu. Minutowy takt wystarcza — normy są liczone
   * w minutach, a częstsze odświeżanie tylko obciążałoby przeglądarkę.
   */
  useEffect(() => {
    const id = window.setInterval(() => setTick((t) => t + 1), 60_000);
    return () => window.clearInterval(id);
  }, []);

  const refresh = useCallback(async () => {
    try {
      const [a, e, d, f, l] = await Promise.all([
        listActivations(),
        listStepExecutions(),
        listDecisions(),
        listFeedback(),
        listLessons(),
      ]);
      setSavedActivations(a);
      setSavedExecutions(e);
      setSavedDecisions(d);
      setSavedFeedback(f);
      setSavedLessons(l);
      setWritebackError(null);
    } catch (e: unknown) {
      setWritebackError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const setRole = useCallback((r: UserRole) => {
    setRoleState(r);
    localStorage.setItem(ROLE_KEY, r);
  }, []);

  const setRoleCode = useCallback((code: string) => {
    setRoleCodeState(code);
    localStorage.setItem(ROLE_CODE_KEY, code);
  }, []);

  const addActivation = useCallback((activation: LiveActivation) => {
    setExtraActivations((prev) => [activation, ...prev]);
    setCurrentId(activation.activationId);
  }, []);

  const patchStep = useCallback(
    (activationId: string, stepNo: number, patch: Partial<LiveStep>) => {
      setStepPatches((prev) => {
        const key = `${activationId}#${stepNo}`;
        return { ...prev, [key]: { ...prev[key], ...patch } };
      });
    },
    [],
  );

  const addDecision = useCallback((activationId: string, decision: LiveDecision) => {
    setExtraDecisions((prev) => ({
      ...prev,
      [activationId]: [...(prev[activationId] ?? []), decision],
    }));
  }, []);

  const closeActivation = useCallback((activationId: string) => {
    setClosedIds((prev) => (prev.includes(activationId) ? prev : [...prev, activationId]));
  }, []);

  /** Scena plus zmiany z bieżącej sesji — jedno źródło dla wszystkich ekranów. */
  const activations = useMemo<LiveActivation[]>(() => {
    const base = [...extraActivations, ...(index?.scene.liveActivations ?? [])];
    return base.map((a) => ({
      ...a,
      steps: a.steps.map((s) => {
        const patch = stepPatches[`${a.activationId}#${s.stepNo}`];
        return patch ? ({ ...s, ...patch } as LiveStep) : s;
      }),
      decisions: [...a.decisions, ...(extraDecisions[a.activationId] ?? [])].sort(
        (x, y) => x.offsetMin - y.offsetMin,
      ),
    }));
  }, [index, extraActivations, stepPatches, extraDecisions]);

  const actor: Actor = useMemo(() => {
    const roleEntry = index?.roleByCode.get(roleCode);
    return {
      id: user?.id ?? 'local-user',
      name: user?.name ?? user?.email ?? 'Użytkownik demonstracyjny',
      role,
      roleCode,
      institution: roleEntry?.institution ?? '',
    };
  }, [user, role, roleCode, index]);

  const value: ScenarioValue = useMemo(
    () => ({
      index,
      retriever,
      loading,
      error,
      tick,
      actor,
      setRole,
      setRoleCode,
      activations,
      currentId,
      setCurrentId,
      addActivation,
      patchStep,
      addDecision,
      closeActivation,
      closedIds,
      savedActivations,
      savedExecutions,
      savedDecisions,
      savedFeedback,
      savedLessons,
      refresh,
      writebackError,
    }),
    [
      index,
      retriever,
      loading,
      error,
      tick,
      actor,
      setRole,
      setRoleCode,
      activations,
      currentId,
      addActivation,
      patchStep,
      addDecision,
      closeActivation,
      closedIds,
      savedActivations,
      savedExecutions,
      savedDecisions,
      savedFeedback,
      savedLessons,
      refresh,
      writebackError,
    ],
  );

  return <ScenarioContext.Provider value={value}>{children}</ScenarioContext.Provider>;
}

export function useScenario(): ScenarioValue {
  const ctx = useContext(ScenarioContext);
  if (!ctx) throw new Error('useScenario musi być użyte wewnątrz ScenarioProvider');
  return ctx;
}
