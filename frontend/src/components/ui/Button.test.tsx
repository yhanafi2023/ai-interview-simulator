import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import Button from './Button'

describe('Button', () => {
  it('renders its children', () => {
    render(<Button>Submit answer</Button>)
    expect(screen.getByRole('button', { name: 'Submit answer' })).toBeInTheDocument()
  })

  it('calls onClick when clicked', async () => {
    const onClick = vi.fn()
    render(<Button onClick={onClick}>Click me</Button>)

    await userEvent.click(screen.getByRole('button'))

    expect(onClick).toHaveBeenCalledOnce()
  })

  it('does not call onClick when disabled', async () => {
    const onClick = vi.fn()
    render(
      <Button onClick={onClick} disabled>
        Click me
      </Button>,
    )

    await userEvent.click(screen.getByRole('button'))

    expect(onClick).not.toHaveBeenCalled()
  })

  it('lets a caller override the background color', () => {
    render(<Button className="bg-emerald-600">Go</Button>)
    const button = screen.getByRole('button')

    expect(button.className).toContain('bg-emerald-600')
    expect(button.className).not.toContain('bg-indigo-600')
  })
})
