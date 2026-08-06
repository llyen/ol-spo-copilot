import { entity, role, text, boolean, decimal, date, uuid } from '@microsoft/rayfin-core';

/**
 * Wniosek z raportu zamknięcia uruchomienia (Ekran 5).
 *
 * Wniosek powstaje z porównania przebiegu z historią, więc niesie liczbę
 * powtórzeń tego samego problemu. Wniosek, przy którym widać „to 18. taki
 * przypadek", broni się sam na posiedzeniu — inaczej niż zdanie „warto poprawić".
 */
@entity()
@role('authenticated', ['create', 'read'])
export class LessonLearned {
  @uuid() id!: string;
  @text({ min: 3, max: 40 }) lesson_id!: string;
  @text({ min: 3, max: 40 }) activation_id!: string;
  @text({ min: 3, max: 20 }) procedure_code!: string;
  /** 'przekroczenie normy' | 'blokada' | 'brak danych' | 'poprawka procedury'. */
  @text({ min: 3, max: 40 }) finding_kind!: string;
  @decimal() step_no!: number;
  @text({ min: 3, max: 300 }) finding!: string;
  /** Ile razy ten sam problem wystąpił w historii — argument, nie ozdoba. */
  @decimal() historical_occurrences!: number;
  @text({ min: 30, max: 2000 }) recommendation!: string;
  @text({ max: 60 }) owner_role!: string;
  @text({ max: 30 }) due_date!: string;
  @boolean() accepted!: boolean;
  @text({ max: 120 }) author_id!: string;
  @text({ max: 160 }) author_name!: string;
  @text({ min: 3, max: 60 }) author_role!: string;
  @date() created_at!: Date;
}
