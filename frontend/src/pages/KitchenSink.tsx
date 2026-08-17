import Button from '../components/ui/Button'

export default function KitchenSink() {
  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Kitchen Sink</h1>

      <section className="space-y-3">
        <h2 className="text-sm uppercase tracking-wide text-slate-500">Button variants</h2>
        <div className="flex flex-wrap gap-3">
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="danger">Danger</Button>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm uppercase tracking-wide text-slate-500">Sizes</h2>
        <div className="flex flex-wrap items-center gap-3">
          <Button size="sm">Small</Button>
          <Button size="md">Medium</Button>
          <Button size="lg">Large</Button>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm uppercase tracking-wide text-slate-500">States</h2>
        <div className="flex flex-wrap gap-3">
          <Button disabled>Disabled</Button>
          <Button onClick={() => alert('clicked')}>With onClick</Button>
          <Button className="bg-emerald-600 hover:bg-emerald-500">Overridden color</Button>
        </div>
      </section>
    </div>
  )
}
