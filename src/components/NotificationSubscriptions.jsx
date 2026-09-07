import { useState } from 'react'
import Button from './Button'
import Input from './Input'
import { subscribeEmail, unsubscribeEmail } from '../services/notificationsService'

export default function NotificationSubscriptions() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')
  const [isSubscribing, setIsSubscribing] = useState(false)
  const [isUnsubscribing, setIsUnsubscribing] = useState(false)

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
    setIsSubscribing(true)

    try {
      await subscribeEmail(normalizedEmail)
      setStatus('Confirmation email sent - please check your inbox to confirm.')
    } catch (requestError) {
      setError(requestError.message || 'Unable to subscribe to notifications.')
    } finally {
      setIsSubscribing(false)
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
    setIsUnsubscribing(true)

    try {
      await unsubscribeEmail(normalizedEmail)
      setStatus('Successfully unsubscribed.')
    } catch (requestError) {
      setError(requestError.message || 'Unable to unsubscribe from notifications.')
    } finally {
      setIsUnsubscribing(false)
    }
  }

  function handleEmailChange(event) {
    setEmail(event.target.value)
    setError('')
    setStatus('')
  }

  const isBusy = isSubscribing || isUnsubscribing

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
          disabled={isBusy}
          error={error}
        />

        <div className="mt-4 flex flex-wrap gap-2">
          <Button type="submit" disabled={isBusy}>
            <span aria-hidden="true">+</span>
            {isSubscribing ? 'Subscribing...' : 'Subscribe'}
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={handleUnsubscribe}
            disabled={isBusy}
          >
            <span aria-hidden="true">-</span>
            {isUnsubscribing ? 'Unsubscribing...' : 'Unsubscribe'}
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
