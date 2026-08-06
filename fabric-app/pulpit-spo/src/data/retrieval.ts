/**
 * Wyszukiwarka procedur — port `corpus/retriever.py` na TypeScript.
 *
 * Ten sam indeks TF-IDF, ta sama tokenizacja i to samo agregowanie wyników
 * fragmentów do poziomu procedury. Zgodność jest sprawdzana testem wobec
 * `datasets/derived/retrieval_eval.json` — jeśli port zacznie odpowiadać
 * inaczej niż wersja pythonowa, test to wyłapie.
 *
 * W docelowym wdrożeniu miejsce tego modułu zajmują embeddingi liczone
 * przez AI Functions w Fabric; logika routingu pozostaje ta sama.
 */

import type { Chunk, Procedure, SceneIndexData } from '@/data/model';

const STOPWORDS = new Set([
  'i', 'w', 'z', 'na', 'do', 'o', 'sie', 'nie', 'the', 'oraz', 'lub', 'ktore', 'ktora', 'ktory',
  'jest', 'sa', 'byc', 'za', 'od', 'po', 'przy', 'przez', 'dla', 'jako', 'tez', 'ale', 'co', 'to',
  'ten', 'ta', 'te', 'tym', 'tego', 'jej', 'jego', 'ich', 'my', 'wy', 'on', 'ona', 'ono', 'gdy',
  'jesli', 'czy', 'ze', 'juz', 'tak', 'ma', 'mamy', 'moze', 'mozna', 'sposob', 'raz', 'bez',
]);

const SPO_PATTERN = /SPO-\d+/g;

/**
 * Normalizacja tekstu pytania.
 *
 * `ł` nie jest literą rozkładalną w NFKD, więc bez jawnej podmiany znikałaby
 * przy odsiewaniu znaków spoza ASCII: „zakłócenie" dałoby token `zakocenie`,
 * a pytanie napisane bez ogonków nie trafiłoby w korpus.
 */
export function normalize(text: string): string {
  return text
    .replace(/ł/g, 'l')
    .replace(/Ł/g, 'L')
    .normalize('NFKD')
    .replace(/[^\x20-\x7E]/g, '')
    .toLowerCase();
}

/** Tokenizacja dwupoziomowa: pełny wyraz + prefiks 5-znakowy (odporność na fleksję). */
export function tokenize(text: string): string[] {
  const out: string[] = [];
  for (const token of normalize(text).match(/[a-z0-9]+/g) ?? []) {
    if (token.length <= 2 || STOPWORDS.has(token)) continue;
    out.push(token);
    if (token.length > 5) out.push(token.slice(0, 5));
  }
  return out;
}

export interface Hit {
  chunk: Chunk;
  score: number;
}

export interface RouteResult {
  code: string;
  score: number;
}

export interface AnswerCard {
  question: string;
  procedure: Procedure | null;
  /** Udział wyniku najlepszej procedury w sumie wyników — zakres 0–1. */
  confidence: number;
  /** Poniżej progu aplikacja pokazuje kandydatki zamiast jednej procedury. */
  ambiguous: boolean;
  alternatives: { procedure: Procedure; score: number; confidence: number }[];
  citations: Hit[];
  firstCriticalStep: Procedure['steps'][number] | null;
  latencyMs: number;
}

export class Retriever {
  private readonly termIndex: Map<string, number>;
  private readonly mentions: string[][];

  constructor(
    private readonly chunks: Chunk[],
    private readonly index: SceneIndexData,
  ) {
    this.termIndex = new Map(index.terms.map((t, i) => [t, i]));
    this.mentions = chunks.map((c) => [...new Set(c.text.match(SPO_PATTERN) ?? [])].sort());
  }

  /** Wektor pytania: log-TF przemnożony przez IDF, znormalizowany do długości 1. */
  embed(text: string): Map<number, number> {
    const counts = new Map<number, number>();
    for (const token of tokenize(text)) {
      const j = this.termIndex.get(token);
      if (j === undefined) continue;
      counts.set(j, (counts.get(j) ?? 0) + 1);
    }
    const vec = new Map<number, number>();
    let sumSq = 0;
    for (const [j, c] of counts) {
      const w = (1 + Math.log(c)) * this.index.idf[j];
      vec.set(j, w);
      sumSq += w * w;
    }
    const norm = Math.sqrt(sumSq);
    if (norm > 0) for (const [j, w] of vec) vec.set(j, w / norm);
    return vec;
  }

  /**
   * Podobieństwo kosinusowe do każdego fragmentu.
   *
   * Wiersze macierzy są już znormalizowane przy budowie indeksu, a wektor
   * pytania normalizujemy w `embed`, więc iloczyn skalarny to wprost kosinus.
   */
  scoreAll(question: string): Float32Array {
    const q = this.embed(question);
    const scores = new Float32Array(this.chunks.length);
    if (q.size === 0) return scores;
    for (let i = 0; i < this.index.rows.length; i += 1) {
      let s = 0;
      for (const [j, w] of this.index.rows[i]) {
        const qw = q.get(j);
        if (qw !== undefined) s += w * qw;
      }
      scores[i] = s;
    }
    return scores;
  }

  private topIndices(scores: Float32Array, k: number): number[] {
    return Array.from(scores.keys())
      .sort((a, b) => scores[b] - scores[a])
      .slice(0, k);
  }

  search(question: string, k = 6): Hit[] {
    const scores = this.scoreAll(question);
    return this.topIndices(scores, k).map((i) => ({
      chunk: this.chunks[i],
      score: Math.round(scores[i] * 10_000) / 10_000,
    }));
  }

  /**
   * Agreguje wyniki fragmentów do poziomu procedury.
   *
   * Fragment przypisany do SPO wnosi swój wynik wprost; fragment KPZK lub planu,
   * który wymienia kod SPO, wnosi 45% wyniku — działa jak odsyłacz.
   */
  route(question: string, k = 12): RouteResult[] {
    const scores = this.scoreAll(question);
    const agg = new Map<string, number>();
    this.topIndices(scores, k).forEach((i, rank) => {
      const s = scores[i];
      if (s <= 0) return;
      const decay = 1 / (1 + 0.25 * rank);
      const code = this.chunks[i].procedureCode;
      if (code) agg.set(code, (agg.get(code) ?? 0) + s * decay);
      for (const mentioned of this.mentions[i]) {
        agg.set(mentioned, (agg.get(mentioned) ?? 0) + s * decay * 0.45);
      }
    });
    return [...agg.entries()]
      .map(([code, score]) => ({ code, score }))
      .sort((a, b) => b.score - a.score);
  }
}

/**
 * Buduje kartę odpowiedzi zgodną z ekranem 1 specyfikacji.
 *
 * Zasada „żadna treść bez cytowania" jest tu wymuszona strukturalnie: karta
 * zawsze niesie fragmenty korpusu, na których oparto wskazanie, a przy pewności
 * poniżej progu w ogóle nie wskazuje jednej procedury.
 */
export function buildAnswer(
  retriever: Retriever,
  question: string,
  procedureByCode: Map<string, Procedure>,
  threshold: number,
  alternativesCount = 2,
): AnswerCard {
  const t0 = performance.now();
  const routing = retriever.route(question);
  const citations = retriever.search(question, 4);
  const total = routing.reduce((sum, r) => sum + r.score, 0) || 1;

  const ranked = routing
    .map((r) => ({
      procedure: procedureByCode.get(r.code) ?? null,
      score: r.score,
      confidence: r.score / total,
    }))
    .filter((r): r is { procedure: Procedure; score: number; confidence: number } =>
      r.procedure !== null,
    );

  const best = ranked[0] ?? null;
  const confidence = best ? Math.round(best.confidence * 1000) / 1000 : 0;
  const procedure = best?.procedure ?? null;
  const firstCritical = procedure?.steps.find((s) => s.critical) ?? null;

  return {
    question,
    procedure,
    confidence,
    ambiguous: confidence < threshold,
    alternatives: ranked.slice(1, 1 + (confidence < threshold ? 2 : alternativesCount)),
    citations,
    firstCriticalStep: firstCritical,
    latencyMs: Math.round(performance.now() - t0),
  };
}
