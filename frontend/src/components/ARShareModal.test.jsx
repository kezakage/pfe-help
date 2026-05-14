// Smoke tests for the AR share modal: ensures the QR encodes the right URL,
// the dialog is dismissable, and it stays hidden when `open=false`.

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ARShareModal from './ARShareModal.jsx'

describe('ARShareModal', () => {
  it('renders nothing when closed', () => {
    render(<ARShareModal open={false} mediaId={1} onClose={() => {}} />)
    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('renders QR with absolute /ar/model/:id URL', () => {
    render(<ARShareModal open mediaId={42} caption="Maison Bardo" onClose={() => {}} />)
    const dialog = screen.getByRole('dialog')
    expect(dialog).toBeInTheDocument()

    const expectedUrl = `${window.location.origin}/ar/model/42`
    // The URL is shown verbatim in a <code> tag — easier to assert than
    // poking into the SVG QR.
    expect(screen.getByText(expectedUrl)).toBeInTheDocument()
    expect(screen.getByText('Maison Bardo')).toBeInTheDocument()
  })

  it('closes on backdrop click', () => {
    const onClose = vi.fn()
    render(<ARShareModal open mediaId={1} onClose={onClose} />)
    // The backdrop is the dialog element itself — inner card stops propagation.
    fireEvent.click(screen.getByRole('dialog'))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('closes on ESC key', () => {
    const onClose = vi.fn()
    render(<ARShareModal open mediaId={1} onClose={onClose} />)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalled()
  })
})
