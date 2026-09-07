import { useEffect, useState } from 'react'
import OrderItem from './OrderItem'
import { deleteOrder, getOrders, updateOrder } from '../services/ordersService'

function getOrderId(order) {
  return order.orderId ?? order.id
}

export default function OrdersList({ refreshKey }) {
  const [orders, setOrders] = useState([])
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let isMounted = true

    async function loadOrders() {
      setIsLoading(true)
      setError('')

      try {
        const response = await getOrders()
        if (isMounted) {
          setOrders(Array.isArray(response?.orders) ? response.orders : [])
        }
      } catch (requestError) {
        if (isMounted) {
          setError(requestError.message || 'Unable to load orders.')
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    loadOrders()

    return () => {
      isMounted = false
    }
  }, [refreshKey])

  async function handleDelete(orderId) {
    setError('')

    try {
      await deleteOrder(orderId)
      setOrders((currentOrders) =>
        currentOrders.filter((order) => getOrderId(order) !== orderId),
      )
    } catch (requestError) {
      setError(requestError.message || 'Unable to delete the order.')
    }
  }

  async function handleUpdate(orderId, orderData) {
    setError('')

    try {
      const response = await updateOrder(orderId, orderData)
      const updatedOrder = response?.order ?? response
      setOrders((currentOrders) =>
        currentOrders.map((order) =>
          getOrderId(order) === orderId ? { ...order, ...updatedOrder, ...orderData } : order,
        ),
      )
    } catch (requestError) {
      setError(requestError.message || 'Unable to update the order.')
      return false
    }

    return true
  }

  return (
    <section className="mt-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-7">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-slate-900">Orders</h2>
          <p className="mt-0.5 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">
            DynamoDB records
          </p>
        </div>
        {!isLoading && <span className="text-xs font-medium text-slate-500">{orders.length} total</span>}
      </div>

      {isLoading && <p className="mt-5 text-sm text-slate-500">Loading orders...</p>}
      {error && (
        <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-xs font-medium text-red-700" role="alert">
          {error}
        </p>
      )}
      {!isLoading && !error && orders.length === 0 && (
        <p className="mt-5 text-sm text-slate-500">No orders found.</p>
      )}
      {!isLoading && orders.length > 0 && (
        <ul className="mt-5 divide-y divide-slate-100">
          {orders.map((order) => {
            const orderId = getOrderId(order)
            return (
              <OrderItem
                key={orderId}
                order={order}
                onDelete={handleDelete}
                onUpdate={handleUpdate}
              />
            )
          })}
        </ul>
      )}
    </section>
  )
}
