import { entity, role, text, boolean, decimal, date, uuid } from '@microsoft/rayfin-core';

/**
 * Zwrotna ocena odpowiedzi asystenta (Ekran 1, przycisk „To nie ta procedura").
 *
 * Zapisujemy pytanie, wskazanie routera i procedurę wskazaną przez człowieka.
 * To jest jedyne wiarygodne źródło poprawek korpusu: pytania zadawane w kryzysie
 * brzmią inaczej niż zdania z dokumentów, na których zbudowano indeks.
 */
@entity()
@role('authenticated', ['create', 'read'])
export class AssistantFeedback {
  @uuid() id!: string;
  @text({ min: 3, max: 40 }) feedback_id!: string;
  @text({ min: 3, max: 400 }) question!: string;
  @text({ max: 20 }) top_procedure!: string;
  @decimal() confidence!: number;
  @text({ max: 20 }) corrected_procedure!: string;
  /** 'pomocne' | 'niepomocne' | 'zla procedura'. */
  @text({ min: 3, max: 30 }) verdict!: string;
  @boolean() ambiguous!: boolean;
  @text({ max: 200 }) cited_chunk_ids!: string;
  @decimal() latency_ms!: number;
  @text({ max: 1000 }) comment!: string;
  @text({ max: 120 }) author_id!: string;
  @text({ max: 160 }) author_name!: string;
  @text({ min: 3, max: 60 }) author_role!: string;
  @date() created_at!: Date;
}
