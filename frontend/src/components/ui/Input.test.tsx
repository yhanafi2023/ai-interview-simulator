import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import Input from './Input'

describe('Input', () => {
  it('connects the label to the input', async () => {
    render(<Input label="Email" />)

    const input = screen.getByLabelText('Email')
    await userEvent.type(input, 'jack@example.com')

    expect(input).toHaveValue('jack@example.com')
  })

  it('gives each instance a unique id', () => {
    render(
      <>
        <Input label="Email" />
        <Input label="Password" />
      </>,
    )

    expect(screen.getByLabelText('Email').id).not.toBe(screen.getByLabelText('Password').id)
  })

  it('marks the input invalid and shows the message when there is an error', () => {
    render(<Input label="Email" error="Enter a valid email address" />)

    const input = screen.getByLabelText('Email')
    expect(input).toHaveAttribute('aria-invalid', 'true')
    expect(input).toHaveAccessibleDescription('Enter a valid email address')
  })
})
