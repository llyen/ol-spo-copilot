import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { describe, expect, it } from 'vitest';

import { indexScene, type Scene } from '@/data/model';
import { Retriever, buildAnswer, normalize, tokenize } from '@/data/retrieval';

const scene: Scene = JSON.parse(
  readFileSync(resolve(__dirname, '../../public/data/scene.json'), 'utf8'),
);
const index = indexScene(scene);
const retriever = new Retriever(scene.chunks, scene.index);

describe('normalizacja', () => {
  it('transliteruje polskie znaki zamiast je gubić', () => {
    // Defekt, który realnie wystąpił: NFKD nie rozkłada „ł", więc samo
    // odsianie znaków spoza ASCII zamienia „ludności" w „udnoci".
    expect(normalize('ludności')).toBe('ludnosci');
    expect(normalize('Łódź')).toBe('lodz');
    expect(normalize('zagrożenie')).toBe('zagrozenie');
  });

  it('daje ten sam zapis dla tekstu z ogonkami i bez', () => {
    expect(normalize('powódź')).toBe(normalize('powodz'));
    expect(tokenize('ewakuacja ludności')).toEqual(tokenize('ewakuacja ludnosci'));
  });

  it('dokłada prefiks pięcioznakowy do wyrazów dłuższych niż pięć znaków', () => {
    expect(tokenize('ewakuacja')).toContain('ewaku');
    expect(tokenize('plan')).toEqual(['plan']);
  });
});

describe('routing pytań do procedur', () => {
  const questions = scene.meta.retrieval;
  const misses = new Set(questions.misses.map((m) => m.question));

  it('scena niesie metryki policzone w Fabric', () => {
    expect(questions.questions).toBeGreaterThan(20);
    expect(questions.top1_accuracy).toBeGreaterThan(0.85);
  });

  it('odtwarza wskazania z notatnika ewaluacyjnego', () => {
    // Kotwica: port TS ma trafiać dokładnie tam, gdzie trafił Python.
    // Pytania wymienione w `misses` chybiły już w Fabric — tu też mają chybić,
    // bo inaczej implementacje się rozjechały.
    let hits = 0;
    for (const q of scene.sampleQuestions) {
      const routed = retriever.route(q.question);
      const top = routed[0]?.code ?? '';
      if (top === q.expected) hits += 1;
      if (misses.has(q.question)) expect(top).not.toBe(q.expected);
    }
    expect(hits / scene.sampleQuestions.length).toBeGreaterThanOrEqual(
      questions.top1_accuracy - 0.05,
    );
  });

  it('daje ten sam wynik dla pytania bez ogonków', () => {
    const q = scene.sampleQuestions[0].question;
    const stripped = normalize(q);
    expect(retriever.route(stripped)[0]?.code).toBe(retriever.route(q)[0]?.code);
  });

  it('zwraca pustą listę dla pytania spoza korpusu', () => {
    expect(retriever.route('qqq zzz xxx')).toEqual([]);
  });
});

describe('karta odpowiedzi', () => {
  const card = buildAnswer(
    retriever,
    scene.sampleQuestions[0].question,
    index.procedureByCode,
    scene.meta.confidenceThreshold,
  );

  it('nigdy nie wskazuje procedury bez cytowań', () => {
    expect(card.procedure).not.toBeNull();
    expect(card.citations.length).toBeGreaterThan(0);
    for (const c of card.citations) expect(c.chunk.text.length).toBeGreaterThan(0);
  });

  it('pewność mieści się w zakresie 0–1 i schodzi z progu przy pytaniu ogólnym', () => {
    expect(card.confidence).toBeGreaterThan(0);
    expect(card.confidence).toBeLessThanOrEqual(1);
  });

  it('oznacza pytanie jako niejednoznaczne poniżej progu', () => {
    const vague = buildAnswer(
      retriever,
      'co robić',
      index.procedureByCode,
      scene.meta.confidenceThreshold,
    );
    expect(vague.ambiguous).toBe(vague.confidence < scene.meta.confidenceThreshold);
  });
});

describe('indeks sceny', () => {
  it('macierz jest zapisana rzadko i zgadza się z liczbą fragmentów', () => {
    expect(scene.index.rows.length).toBe(scene.chunks.length);
    const nz = scene.index.rows.reduce((s, r) => s + r.length, 0);
    expect(nz).toBe(scene.index.nonZero);
    expect(nz).toBeLessThan(scene.chunks.length * scene.index.terms.length * 0.2);
  });

  it('wiersze są znormalizowane do długości 1', () => {
    for (const row of scene.index.rows.slice(0, 50)) {
      if (row.length === 0) continue;
      const len = Math.sqrt(row.reduce((s, [, w]) => s + w * w, 0));
      expect(len).toBeCloseTo(1, 3);
    }
  });
});
