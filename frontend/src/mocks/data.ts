import type { Question, User } from '../types'

export const mockUser: User = {
  id: 'usr_1',
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
    type: 'technical',
    difficulty: 'medium',
    prompt:
      'Given a list of user events with timestamps, find the busiest one-hour window. Discuss time and space complexity.',
  },
  {
    id: 'q_4',
    type: 'technical',
    difficulty: 'hard',
    prompt:
      'Implement an LRU cache with O(1) get and put. Explain which data structures you need and why each one is required.',
  },
  {
    id: 'q_5',
    type: 'technical',
    difficulty: 'easy',
    prompt:
      'What is the difference between an index on one column and a composite index on two? When would a composite index not help?',
  },
  {
    id: 'q_6',
    type: 'behavioral',
    difficulty: 'easy',
    prompt: 'Tell me about a time you disagreed with a teammate. How did you resolve it?',
  },
  {
    id: 'q_7',
    type: 'behavioral',
    difficulty: 'medium',
    prompt:
      'Describe a project that did not go the way you planned. What did you do, and what would you do differently?',
  },
  {
    id: 'q_8',
    type: 'behavioral',
    difficulty: 'medium',
    prompt:
      'Tell me about a time you received critical feedback on your work. How did you react to it?',
  },
  {
    id: 'q_9',
    type: 'behavioral',
    difficulty: 'hard',
    prompt:
      'Describe a situation where you had to make a technical decision without enough information. How did you decide, and how did it turn out?',
  },
  {
    id: 'q_10',
    type: 'system_design',
    difficulty: 'medium',
    prompt: 'Design a URL shortener that handles 100M redirects per day.',
  },
  {
    id: 'q_11',
    type: 'system_design',
    difficulty: 'medium',
    prompt:
      'Design the backend for a notification system that sends email, SMS, and push. How do you handle a provider going down?',
  },
  {
    id: 'q_12',
    type: 'system_design',
    difficulty: 'hard',
    prompt:
      'Design a system that grades AI interview answers. Grading takes 5-15 seconds per answer. How do you keep the API responsive?',
  },
]
