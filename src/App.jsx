import NotificationSubscriptions from './components/NotificationSubscriptions'
import CreateOrder from './components/CreateOrder'

function App() {
  return (
    <main className="min-h-screen bg-slate-100 px-4 py-10 text-slate-900 sm:px-8 sm:py-16">
      <div className="mx-auto max-w-5xl">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-orange-600">Event-driven architecture</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">Keep every order moving.</h1>
        <div className="mt-8 border-t border-slate-300 pt-6">
          <div className="grid gap-4 lg:grid-cols-2">
            <NotificationSubscriptions />
            <CreateOrder />
          </div>
        </div>
      </div>
    </main>
  )
}

export default App
