import { useState } from 'react'
import Button from './Button'
import { getDeletedOrdersReport } from '../services/ordersService'

function formatCurrency(value) {
  return Number(value).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
  })
}

function formatDate(value) {
  if (!value) {
    return 'Unknown date'
  }

  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString()
}

export default function DeletedOrdersReport() {
  const [isOpen, setIsOpen] = useState(false)
  const [report, setReport] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const reportOrders = Array.isArray(report?.orders) ? report.orders : []

  async function handleToggle() {
    if (isOpen) {
      setIsOpen(false)
      return
    }

    setIsOpen(true)
    setIsLoading(true)
    setError('')

    try {
      setReport(await getDeletedOrdersReport())
    } catch (requestError) {
      setError(requestError.message || 'Unable to load the deleted orders report.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <section className="mt-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-7">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-900">Deleted orders report</h2>
          <p className="mt-0.5 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">
            Revenue history
          </p>
        </div>
        <Button type="button" variant="secondary" onClick={handleToggle} disabled={isLoading}>
          {isLoading ? 'Loading report...' : isOpen ? 'Hide report' : 'View report'}
        </Button>
      </div>

      {isOpen && (
        <div className="mt-5 border-t border-slate-100 pt-5">
          {error && (
            <p className="rounded-md bg-red-50 px-3 py-2 text-xs font-medium text-red-700" role="alert">
              {error}
            </p>
          )}
          {isLoading && <p className="text-sm text-slate-500">Loading deleted orders...</p>}
          {!isLoading && !error && report && (
            <>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-md bg-slate-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Total deleted orders</p>
                  <p className="mt-2 text-2xl font-semibold text-slate-900">{report.totalDeletedOrders}</p>
                </div>
                <div className="rounded-md bg-orange-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-orange-700">Total lost revenue</p>
                  <p className="mt-2 text-2xl font-semibold text-slate-900">{formatCurrency(report.totalLostRevenue)}</p>
                </div>
              </div>

              {reportOrders.length === 0 ? (
                <p className="mt-5 text-sm text-slate-500">No deleted orders found.</p>
              ) : (
                <div className="mt-5 overflow-x-auto">
                  <table className="w-full min-w-[42rem] text-left text-sm">
                    <thead className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                      <tr>
                        <th className="px-3 py-2 font-semibold">Order</th>
                        <th className="px-3 py-2 font-semibold">Description</th>
                        <th className="px-3 py-2 font-semibold">Price</th>
                        <th className="px-3 py-2 font-semibold">Deleted</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {reportOrders.map((order) => (
                        <tr key={`${order.orderId}-${order.deletedAt}`}>
                          <td className="whitespace-nowrap px-3 py-3 font-medium text-slate-900">{order.orderId}</td>
                          <td className="px-3 py-3 text-slate-600">{order.description}</td>
                          <td className="whitespace-nowrap px-3 py-3 text-slate-600">{formatCurrency(order.price)}</td>
                          <td className="whitespace-nowrap px-3 py-3 text-slate-500">{formatDate(order.deletedAt)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </section>
  )
}