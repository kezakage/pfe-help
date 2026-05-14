// Tests for the Toast component: render, manual dismiss, auto-dismiss,
// and variant→icon mapping. Auto-dismiss uses vitest fake timers so the
// 5-second wait doesn't slow the suite.

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act, fireEvent } from '@testing-library/react'
import { Toast, ToastContainer } from './Toast.jsx'

describe('Toast', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })
  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders title and body', () => {
    render(<Toast id="1" title="Validé" body="Projet publié" type="success" />)
    expect(screen.getByText('Validé')).toBeInTheDocument()
    expect(screen.getByText('Projet publié')).toBeInTheDocument()
    // role=status so screen readers announce it
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('calls onDismiss when the close button is clicked', () => {
    const onDismiss = vi.fn()
    // fireEvent (vs userEvent) plays nicer with fake timers — no async
    // pointer-move animation frames to advance.
    render(<Toast id="abc" title="x" onDismiss={onDismiss} />)
    fireEvent.click(screen.getByRole('button', { name: /fermer/i }))
    expect(onDismiss).toHaveBeenCalledWith('abc')
  })

  it('auto-dismisses after 5 seconds', () => {
    const onDismiss = vi.fn()
    render(<Toast id="auto" title="x" onDismiss={onDismiss} />)
    expect(onDismiss).not.toHaveBeenCalled()
    act(() => { vi.advanceTimersByTime(4999) })
    expect(onDismiss).not.toHaveBeenCalled()
    act(() => { vi.advanceTimersByTime(2) })
    expect(onDismiss).toHaveBeenCalledWith('auto')
  })

  it('falls back to info variant when type is unknown', () => {
    render(<Toast id="1" title="hi" type="not-a-real-variant" />)
    // The status container should still render — no crash on unknown variant.
    expect(screen.getByRole('status')).toBeInTheDocument()
  })
})

describe('ToastContainer', () => {
  it('renders nothing when the toasts array is empty', () => {
    render(<ToastContainer toasts={[]} onDismiss={() => {}} />)
    // No toast => no status role anywhere
    expect(screen.queryByRole('status')).toBeNull()
  })

  it('renders one Toast per entry', () => {
    render(
      <ToastContainer
        toasts={[
          { id: 'a', title: 'A', type: 'success' },
          { id: 'b', title: 'B', type: 'error' },
        ]}
        onDismiss={() => {}}
      />,
    )
    expect(screen.getByText('A')).toBeInTheDocument()
    expect(screen.getByText('B')).toBeInTheDocument()
    expect(screen.getAllByRole('status')).toHaveLength(2)
  })
})
