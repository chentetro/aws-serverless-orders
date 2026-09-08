import { useState } from 'react'
import Button from './Button'
import Input from './Input'
import { createOrder, extractOrderFromDocument } from '../services/ordersService'

function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = String(reader.result || '')
      const base64 = result.includes(',') ? result.split(',')[1] : result
      resolve(base64)
    }
    reader.onerror = () => reject(new Error('Could not read that file.'))
    reader.readAsDataURL(file)
  })
}

export default function CreateOrder({ onOrderCreated }) {
  const [price, setPrice] = useState('')
  const [description, setDescription] = useState('')
  const [errors, setErrors] = useState({})
  const [status, setStatus] = useState('')
  const [extractJson, setExtractJson] = useState(null)
  const [documentFile, setDocumentFile] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isExtracting, setIsExtracting] = useState(false)

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
      setDocumentFile(null)
      setExtractJson(null)
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

  function handleDocumentChange(event) {
    const file = event.target.files?.[0] ?? null
    setDocumentFile(file)
    setExtractJson(null)
    setErrors((currentErrors) => ({ ...currentErrors, extract: '', form: '' }))
  }

  async function handleExtract() {
    if (!documentFile) {
      setErrors((currentErrors) => ({
        ...currentErrors,
        extract: 'Choose a PNG or JPG first.',
      }))
      return
    }

    setIsExtracting(true)
    setErrors((currentErrors) => ({ ...currentErrors, extract: '', form: '' }))
    setStatus('')

    try {
      const imageBase64 = await readFileAsBase64(documentFile)
      const response = await extractOrderFromDocument({
        imageBase64,
        fileName: documentFile.name,
      })
      setExtractJson(response)
      if (response?.description) {
        setDescription(String(response.description))
      }
      if (response?.price != null && Number.isFinite(Number(response.price))) {
        setPrice(String(response.price))
      }
    } catch (requestError) {
      setExtractJson(null)
      setErrors((currentErrors) => ({
        ...currentErrors,
        extract: requestError.message || 'Textract could not read this file.',
      }))
    } finally {
      setIsExtracting(false)
    }
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
          <p className="mt-0.5 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">
            DynamoDB · Amazon Textract
          </p>
        </div>
      </div>

      <form className="mt-5" onSubmit={handleSubmit} noValidate>
        <div className="rounded-md border border-orange-100 bg-orange-50/60 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-orange-800">Amazon Textract</p>
          <p className="mt-1 text-sm text-slate-600">
            Upload a PNG or JPG of the order. Textract fills description and price so you do not type them by hand.
          </p>
          <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-end">
            <Input
              id="order-document"
              label="Order document"
              name="document"
              type="file"
              accept="image/png,image/jpeg,application/pdf"
              onChange={handleDocumentChange}
              disabled={isLoading || isExtracting}
              error={errors.extract}
            />
            <Button type="button" variant="secondary" onClick={handleExtract} disabled={isLoading || isExtracting}>
              {isExtracting ? 'Reading with Textract...' : 'Fill from document'}
            </Button>
          </div>
          {extractJson && (
            <pre className="mt-3 overflow-x-auto rounded-md bg-white px-3 py-2 text-[11px] text-slate-700">
              {JSON.stringify(extractJson, null, 2)}
            </pre>
          )}
        </div>
        <div className="mt-4 grid gap-4 sm:grid-cols-[minmax(0,0.35fr)_minmax(0,1fr)]">
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
            disabled={isLoading || isExtracting}
            error={errors.price}
          />
          <Input
            id="order-description"
            label="Order description"
            name="description"
            value={description}
            onChange={handleDescriptionChange}
            placeholder="What was ordered?"
            disabled={isLoading || isExtracting}
            error={errors.description}
          />
        </div>

        <Button className="mt-4 w-full" type="submit" disabled={isLoading || isExtracting}>
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
