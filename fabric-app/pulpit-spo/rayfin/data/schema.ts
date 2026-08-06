import { Activation } from './Activation.js';
import { StepExecution } from './StepExecution.js';
import { DecisionLog } from './DecisionLog.js';
import { AssistantFeedback } from './AssistantFeedback.js';
import { LessonLearned } from './LessonLearned.js';

export type AppSchema = {
  Activation: Activation;
  StepExecution: StepExecution;
  DecisionLog: DecisionLog;
  AssistantFeedback: AssistantFeedback;
  LessonLearned: LessonLearned;
};

export const schema = [
  Activation,
  StepExecution,
  DecisionLog,
  AssistantFeedback,
  LessonLearned,
];
