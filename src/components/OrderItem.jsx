import { useState } from 'react'
import Button from './Button'
import Input from './Input'

function formatCreatedAt(createdAt) {
  if (!createdAt) {
    return ''
  }

  const date = new Date(createdAt)
  return Number.isNaN(date.getTime()) ? String(createdAt) : date.toLocaleString()
}

function getKeyPhrases(keyPhrases) {
  if (Array.isArray(keyPhrases)) {
    return keyPhrases.join(', ')
  }

  return keyPhrases
}

export default function OrderItem({ order, onDelete, onUpdate }) {
  const [isEditing, setIsEditing] = useState(false)
  const [isPending, setIsPending] = useState(false)
  const [description, setDescription] = useState(order.description ?? '')
  const [price, setPrice] = useState(String(order.price ?? ''))
  const [error, setError] = useState('')
  const orderId = order.orderId ?? order.id
  const keyPhrases = getKeyPhrases(order.keyPhrases)

  async function handleUpdate(event) {
    event.preventDefault()
    const numericPrice = Number(price)

    if (!description.trim() || !Number.isFinite(numericPrice) || numericPrice <= 0) {
      setError('Enter a description and a price greater than 0.')
      return
    }

    setError('')
    setIsPending(true)

    try {
      const didUpdate = await onUpdate(orderId, {
        description: description.trim(),
        price: numericPrice,
      })
      if (didUpdate) {
        setIsEditing(false)
      }
    } finally {
      setIsPending(false)
    }
  }

  async function handleDelete() {
    setIsPending(true)

    try {
      await onDelete(orderId)
    } finally {
      setIsPending(false)
    }
  }

  function handleCancel() {
    setDescription(order.description ?? '')
    setPrice(String(order.price ?? ''))
    setError('')
    setIsEditing(false)
  }

  return (
    <li className="py-4 first:pt-0 last:pb-0">
      {isEditing ? (
        <form className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_10rem_auto] sm:items-end" onSubmit={handleUpdate}>
          <Input
            id={`order-description-${orderId}`}
            label="Description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            disabled={isPending}
            error={error}
          />
          <Input
            id={`order-price-${orderId}`}
            label="Price USD"
            type="number"
            min="0"
            step="0.01"
            value={price}
            onChange={(event) => setPrice(event.target.value)}
            disabled={isPending}
          />
          <div className="flex gap-2">
            <Button type="submit" disabled={isPending}>
              {isPending ? 'Saving...' : 'Save'}
            </Button>
            <Button type="button" variant="secondary" onClick={handleCancel} disabled={isPending}>
              Cancel
            </Button>
          </div>
        </form>
      ) : (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-slate-900">{order.description}</p>
            <p className="mt-1 text-xs text-slate-500">${Number(order.price).toFixed(2)}</p>
            {order.createdAt && <p className="mt-1 text-xs text-slate-400">{formatCreatedAt(order.createdAt)}</p>}
            {(order.sentiment || keyPhrases) && (
              <dl className="mt-3 grid gap-1 text-xs text-slate-500 sm:grid-cols-2">
                {order.sentiment && (
                  <div>
                    <dt className="font-semibold text-slate-700">Sentiment</dt>
                    <dd>{order.sentiment}</dd>
                  </div>
                )}
                {keyPhrases && (
                  <div>
                    <dt className="font-semibold text-slate-700">Key phrases</dt>
                    <dd>{keyPhrases}</dd>
                  </div>
                )}
              </dl>
            )}
          </div>
          <div className="flex shrink-0 gap-2">
            <Button type="button" variant="secondary" onClick={() => setIsEditing(true)} disabled={isPending}>
              Edit
            </Button>
            <Button type="button" variant="secondary" onClick={handleDelete} disabled={isPending}>
              {isPending ? 'Deleting...' : 'Delete'}
            </Button>
          </div>
        </div>
      )}
    </li>
  )
}