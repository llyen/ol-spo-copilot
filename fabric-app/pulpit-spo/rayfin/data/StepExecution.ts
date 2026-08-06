import { entity, role, text, boolean, decimal, date, uuid } from '@microsoft/rayfin-core';

/**
 * Zmiana statusu kroku checklisty (Ekran 2).
 *
 * Każda zmiana to osobny rekord, a nie nadpisanie poprzedniego. Dashboard RCB
 * czyta strumień tych zdarzeń, więc postęp jest widoczny bez raportowania
 * „na piechotę", a po zdarzeniu widać, kiedy krok faktycznie ruszył i utknął.
 */
@entity()
@role('authenticated', ['create', 'read'])
export class StepExecution {
  @uuid() id!: string;
  @text({ min: 3, max: 40 }) execution_id!: string;
  @text({ min: 3, max: 40 }) activation_id!: string;
  @text({ min: 3, max: 20 }) procedure_code!: string;
  @text({ min: 3, max: 30 }) step_id!: string;
  @decimal() step_no!: number;
  @text({ max: 250 }) step_title!: string;
  @text({ max: 30 }) role_code!: string;
  @text({ max: 160 }) institution!: string;
  /** 'oczekuje' | 'w toku' | 'wykonany' | 'zablokowany' | 'pominięty'. */
  @text({ min: 3, max: 20 }) status!: string;
  @decimal() sla_minutes!: number;
  @decimal() elapsed_minutes!: number;
  @boolean() sla_met!: boolean;
  @boolean() is_critical!: boolean;
  @text({ max: 250 }) blocker_reason!: string;
  @text({ max: 500 }) note!: string;
  @text({ max: 250 }) output_document!: string;
  /** Odstąpienie od kroku wymaga roli właściciela procedury i uzasadnienia. */
  @boolean() waived!: boolean;
  @text({ max: 1000 }) waiver_justification!: string;
  @text({ max: 120 }) author_id!: string;
  @text({ max: 160 }) author_name!: string;
  @text({ min: 3, max: 60 }) author_role!: string;
  @date() created_at!: Date;
}
