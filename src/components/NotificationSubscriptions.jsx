import { useState } from 'react'
import Button from './Button'
import Input from './Input'
import {
  subscribeToNotifications,
  unsubscribeFromNotifications,
} from '../services/api'

export default function NotificationSubscriptions() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')
  const [actionLoading, setActionLoading] = useState(null)

  function validateEmail() {
    if (!email.trim()) {
      return 'Email address is required.'
    }

    if (!/^\S+@\S+\.\S+$/.test(email)) {
      return 'Enter a valid email address.'
    }

    return ''
  }

  async function handleSubscribe(event) {
    event.preventDefault()
    const validationError = validateEmail()
    setError(validationError)
    setStatus('')

    if (validationError) {
      return
    }

    const normalizedEmail = email.trim()
    setActionLoading('subscribe')

    try {
      const response = await subscribeToNotifications(normalizedEmail)
      setStatus(
        typeof response === 'object' && response?.message
          ? response.message
          : `Notifications enabled for ${normalizedEmail}.`,
      )
    } catch (requestError) {
      setError(requestError.message || 'Unable to subscribe to notifications.')
    } finally {
      setActionLoading(null)
    }
  }

  async function handleUnsubscribe() {
    const validationError = validateEmail()
    setError(validationError)
    setStatus('')

    if (validationError) {
      return
    }

    const normalizedEmail = email.trim()
    setActionLoading('unsubscribe')

    try {
      const response = await unsubscribeFromNotifications(normalizedEmail)
      setStatus(
        typeof response === 'object' && response?.message
          ? response.message
          : `Notifications disabled for ${normalizedEmail}.`,
      )
    } catch (requestError) {
      setError(requestError.message || 'Unable to unsubscribe from notifications.')
    } finally {
      setActionLoading(null)
    }
  }

  function handleEmailChange(event) {
    setEmail(event.target.value)
    setError('')
    setStatus('')
  }

  return (
    <section className="w-full max-w-xl rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-7">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-orange-50 text-orange-500" aria-hidden="true">
          <svg viewBox="0 0 24 24" className="h-5 w-5 fill-none stroke-current" strokeWidth="1.8">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 17H9m9-2V10a6 6 0 1 0-12 0v5l-1.5 2h15L18 15Zm-5 5h-2" />
          </svg>
        </div>
        <div>
          <h2 className="text-base font-semibold text-slate-900">Notification subscriptions</h2>
          <p className="mt-0.5 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">Amazon SNS</p>
        </div>
      </div>

      <p className="mt-5 text-sm leading-6 text-slate-600">
        Get notified whenever an order is created or changed.
      </p>

      <form className="mt-5" onSubmit={handleSubscribe} noValidate>
        <Input
          id="notification-email"
          label="Email address"
          name="email"
          type="email"
          value={email}
          onChange={handleEmailChange}
          placeholder="user@example.com"
          autoComplete="email"
          error={error}
        />

        <div className="mt-4 flex flex-wrap gap-2">
          <Button type="submit" disabled={actionLoading !== null}>
            <span aria-hidden="true">+</span>
            {actionLoading === 'subscribe' ? 'Subscribing...' : 'Subscribe'}
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={handleUnsubscribe}
            disabled={actionLoading !== null}
          >
            <span aria-hidden="true">-</span>
            {actionLoading === 'unsubscribe' ? 'Unsubscribing...' : 'Unsubscribe'}
          </Button>
        </div>
      </form>

      {status && (
        <p className="mt-4 rounded-md bg-slate-50 px-3 py-2 text-xs font-medium text-slate-600" role="status">
          {status}
        </p>
      )}
    </section>
  )
}
