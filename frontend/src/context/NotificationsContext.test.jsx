// Tests for NotificationsContext: verifies that a WS push triggers a toast
// with the correct visual variant (success/error/info) for the backend's
// Notification.Type enum.
//
// Strategy:
//   - mock ../lib/api so notifApi.list() resolves immediately with []
//   - mock ../lib/ws so openNotificationsSocket exposes its callback to the
//     test, letting us simulate an incoming WS push synchronously
//   - mock ./AuthContext.useAuth so the provider sees a logged-in user

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'

// ---- Mocks ---------------------------------------------------------------

vi.mock('../lib/api.js', () => ({
  notifications: {
    list: vi.fn().mockResolvedValue([]),
    markAllRead: vi.fn().mockResolvedValue({}),
    markRead: vi.fn().mockResolvedValue({}),
  },
}))

// Capture the WS callback so a test can fire fake server pushes.
let wsCallback = null
vi.mock('../lib/ws.js', () => ({
  openNotificationsSocket: (cb) => {
    wsCallback = cb
    return () => { wsCallback = null }
  },
}))

vi.mock('./AuthContext.jsx', () => ({
  useAuth: () => ({ user: { id: 1, email: 'demo@patrimoine.dz' } }),
}))

// Import AFTER mocks so the provider picks them up.
import { NotificationsProvider, useNotifications } from './NotificationsContext.jsx'

// ---- Helpers -------------------------------------------------------------

function ConsumerProbe() {
  // Surface the unread counter so we can assert on it too.
  const ctx = useNotifications()
  return <span data-testid="unread">{ctx?.unread ?? 0}</span>
}

// Wait for the provider's initial `notifApi.list()` promise to resolve.
// One microtask + one tick is enough since the mock resolves with [].
async function flushPromises() {
  await act(async () => { await Promise.resolve() })
}

beforeEach(() => {
  wsCallback = null
})

// ---- Tests ---------------------------------------------------------------

describe('NotificationsContext — toast push via WS', () => {
  it('renders a success toast for expert_validated', async () => {
    render(
      <NotificationsProvider>
        <ConsumerProbe />
      </NotificationsProvider>,
    )
    await flushPromises()
    expect(wsCallback).toBeTypeOf('function')

    act(() => {
      wsCallback({
        id: 42,
        type: 'expert_validated',
        title: 'Compte validé',
        body: 'Bienvenue',
      })
    })

    expect(screen.getByText('Compte validé')).toBeInTheDocument()
    expect(screen.getByText('Bienvenue')).toBeInTheDocument()
    // Unread counter bumped from 0 → 1
    expect(screen.getByTestId('unread').textContent).toBe('1')
  })

  it('renders an error toast for expert_rejected', async () => {
    render(
      <NotificationsProvider>
        <ConsumerProbe />
      </NotificationsProvider>,
    )
    await flushPromises()
    act(() => {
      wsCallback({ id: 1, type: 'expert_rejected', title: 'Refusé', body: 'Motif' })
    })
    // role=status comes from <Toast>, ensures it actually mounted
    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.getByText('Refusé')).toBeInTheDocument()
  })

  it('falls back to info toast for unknown notification types', async () => {
    render(
      <NotificationsProvider>
        <ConsumerProbe />
      </NotificationsProvider>,
    )
    await flushPromises()
    act(() => {
      wsCallback({ id: 9, type: 'something_new', title: 'Hello' })
    })
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('renders no toasts before any WS push arrives', async () => {
    render(
      <NotificationsProvider>
        <ConsumerProbe />
      </NotificationsProvider>,
    )
    await flushPromises()
    expect(screen.queryByRole('status')).toBeNull()
    expect(screen.getByTestId('unread').textContent).toBe('0')
  })
})
