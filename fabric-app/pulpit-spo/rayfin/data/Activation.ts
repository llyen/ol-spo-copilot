import { entity, role, text, boolean, decimal, date, uuid } from '@microsoft/rayfin-core';

/**
 * Uruchomienie procedury SPO (Ekran 2).
 *
 * Odpowiednik zdarzenia `activation` w Eventhouse. Aplikacja zapisuje kontekst
 * dyżuru w chwili uruchomienia — poziom, województwo, zdarzenie i uzasadnienie —
 * bo po zdarzeniu nikt już tego nie odtworzy wiarygodnie.
 */
@entity()
@role('authenticated', ['create', 'read'])
export class Activation {
  @uuid() id!: string;
  @text({ min: 3, max: 40 }) activation_id!: string;
  @text({ min: 3, max: 20 }) procedure_code!: string;
  @text({ max: 250 }) procedure_name!: string;
  @text({ max: 160 }) event_name!: string;
  @text({ max: 10 }) hazard_code!: string;
  /** 'gminny' | 'powiatowy' | 'wojewódzki' | 'krajowy'. */
  @text({ min: 3, max: 20 }) level!: string;
  @text({ max: 4 }) voivodeship_code!: string;
  @text({ max: 60 }) voivodeship_name!: string;
  /** Uzasadnienie uruchomienia — trafia też jako pierwszy wpis do dziennika decyzji. */
  @text({ min: 30, max: 1000 }) trigger_text!: string;
  /** Pewność routingu asystenta w chwili uruchomienia (0–1); 0 przy wyborze ręcznym. */
  @decimal() confidence!: number;
  @text({ max: 400 }) source_question!: string;
  @boolean() from_assistant!: boolean;
  @text({ max: 20 }) status!: string;
  @text({ max: 120 }) author_id!: string;
  @text({ max: 160 }) author_name!: string;
  @text({ min: 3, max: 60 }) author_role!: string;
  @date() created_at!: Date;
}
