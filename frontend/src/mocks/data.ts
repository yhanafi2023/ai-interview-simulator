import type { Question, User } from '../types'

export const mockUser: User = {
  id: 'user_1',
  email: 'jack@example.com',
  displayName: 'Jack',
}

export const mockQuestions: Question[] = [
  {
    id: 'q_1',
    type: 'technical',
    difficulty: 'easy',
    prompt: 'Reverse a linked list in place. Walk through your approach before writing code.',
  },
  {
    id: 'q_2',
    type: 'technical',
    difficulty: 'medium',
    prompt: 'Design a rate limiter for an API. What data structure would you use and why?',
  },
  {
    id: 'q_3',
    type: 'behavioral',
    difficulty: 'easy',
    prompt: 'Tell me about a time you disagreed with a teammate. How did you resolve it?',
  },
  {
    id: 'q_4',
    type: 'system_design',
    difficulty: 'hard',
    prompt: 'Design a URL shortener that handles 100M redirects per day.',
  },
]
