import { useState } from 'react'
import Button from './Button'
import Input from './Input'
import { createOrder } from '../services/ordersService'

export default function CreateOrder({ onOrderCreated }) {
  const [price, setPrice] = useState('')
  const [description, setDescription] = useState('')
  const [errors, setErrors] = useState({})
  const [status, setStatus] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  function validateForm() {
    const nextErrors = {}
    const numericPrice = Number(price)

    if (!price.trim() || !Number.isFinite(numericPrice) || numericPrice <= 0) {
      nextErrors.price = 'Enter a price greater than 0.'
    }

    if (!description.trim()) {
      nextErrors.description = 'Order description is required.'
    }

    return nextErrors
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const validationErrors = validateForm()
    setErrors(validationErrors)
    setStatus('')

    if (Object.keys(validationErrors).length > 0) {
      return
    }

    setIsLoading(true)

    try {
      const response = await createOrder({
        price: Number(price),
        description: description.trim(),
      })
      const successMessage =
        typeof response === 'object' && response?.message
          ? response.message
          : 'Order created successfully.'

      setPrice('')
      setDescription('')
      setErrors({})
      setStatus(successMessage)
      onOrderCreated?.(response)
    } catch (requestError) {
      setStatus('')
      setErrors({ form: requestError.message || 'Unable to create the order.' })
    } finally {
      setIsLoading(false)
    }
  }

  function handlePriceChange(event) {
    setPrice(event.target.value)
    setErrors((currentErrors) => ({ ...currentErrors, price: '', form: '' }))
    setStatus('')
  }

  function handleDescriptionChange(event) {
    setDescription(event.target.value)
    setErrors((currentErrors) => ({ ...currentErrors, description: '', form: '' }))
    setStatus('')
  }

  return (
    <section className="w-full rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-7">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-orange-50 text-orange-500" aria-hidden="true">
          <svg viewBox="0 0 24 24" className="h-5 w-5 fill-none stroke-current" strokeWidth="1.8">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 5v14m-7-7h14" />
          </svg>
        </div>
        <div>
          <h2 className="text-base font-semibold text-slate-900">Create new order</h2>
          <p className="mt-0.5 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">DynamoDB</p>
        </div>
      </div>

      <form className="mt-5" onSubmit={handleSubmit} noValidate>
        <div className="grid gap-4 sm:grid-cols-[minmax(0,0.35fr)_minmax(0,1fr)]">
          <Input
            id="order-price"
            label="Price USD"
            name="price"
            type="number"
            min="0"
            step="0.01"
            value={price}
            onChange={handlePriceChange}
            placeholder="0.00"
            disabled={isLoading}
            error={errors.price}
          />
          <Input
            id="order-description"
            label="Order description"
            name="description"
            value={description}
            onChange={handleDescriptionChange}
            placeholder="What was ordered?"
            disabled={isLoading}
            error={errors.description}
          />
        </div>

        <Button className="mt-4 w-full" type="submit" disabled={isLoading}>
          <span aria-hidden="true">+</span>
          {isLoading ? 'Creating order...' : 'Create order'}
        </Button>
      </form>

      {errors.form && (
        <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-xs font-medium text-red-700" role="alert">
          {errors.form}
        </p>
      )}
      {status && (
        <p className="mt-4 rounded-md bg-slate-50 px-3 py-2 text-xs font-medium text-slate-600" role="status">
          {status}
        </p>
      )}
    </section>
  )
}
