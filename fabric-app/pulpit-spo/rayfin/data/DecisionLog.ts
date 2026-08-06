import { entity, role, text, decimal, date, uuid } from '@microsoft/rayfin-core';

/**
 * Wpis do dziennika decyzji (Ekran 3).
 *
 * Encja jest celowo tylko do zapisu i odczytu — bez aktualizacji i bez
 * usuwania. Korekta powstaje jako nowy wpis wskazujący poprzedni przez
 * `corrects_decision_id`. Dziennik, który da się poprawić po fakcie, nie jest
 * śladem audytowym, tylko notatnikiem.
 */
@entity()
@role('authenticated', ['create', 'read'])
export class DecisionLog {
  @uuid() id!: string;
  @text({ min: 3, max: 40 }) decision_id!: string;
  @text({ min: 3, max: 40 }) activation_id!: string;
  @text({ min: 3, max: 20 }) procedure_code!: string;
  @decimal() step_no!: number;
  @text({ min: 3, max: 60 }) decision_type!: string;
  @text({ max: 60 }) decided_by_role!: string;
  @text({ max: 160 }) decided_by_name!: string;
  @text({ min: 3, max: 300 }) subject!: string;
  /** Pole obowiązkowe — decyzja bez uzasadnienia nie jest rozliczalna. */
  @text({ min: 30, max: 2000 }) rationale!: string;
  /** 'jawne' | 'zastrzeżone' | 'poufne'. */
  @text({ min: 3, max: 20 }) classification!: string;
  @text({ max: 40 }) corrects_decision_id!: string;
  @text({ max: 120 }) author_id!: string;
  @text({ max: 160 }) author_name!: string;
  @text({ min: 3, max: 60 }) author_role!: string;
  @date() created_at!: Date;
}
