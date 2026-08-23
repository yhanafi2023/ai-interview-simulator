import type { components, paths } from './api'

type Schemas = components['schemas']

export type User = Schemas['User']
export type Question = Schemas['Question']
export type AuthResponse = Schemas['AuthResponse']
export type LoginRequest = Schemas['LoginRequest']
export type RegisterRequest = Schemas['RegisterRequest']
export type ApiError = Schemas['ApiError']
export type InterviewType = Schemas['InterviewType']
export type Difficulty = Schemas['Difficulty']
export type QuestionListResponse =
  paths['/questions']['get']['responses'][200]['content']['application/json']
export type Session = Schemas['Session']
export type SessionStatus = Schemas['SessionStatus']
export type CreateSessionRequest = Schemas['CreateSessionRequest']
export type SubmitAnswerRequest = Schemas['SubmitAnswerRequest']
export type Feedback = Schemas['Feedback']
export type Score = Schemas['Score']
export type ScoreDimension = Schemas['ScoreDimension']
