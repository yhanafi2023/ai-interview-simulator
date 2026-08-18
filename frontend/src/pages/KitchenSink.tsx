import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Input from '../components/ui/Input'

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="text-sm uppercase tracking-wide text-slate-500">{title}</h2>
      {children}
    </section>
  )
}

export default function KitchenSink() {
  return (
    <div className="space-y-10">
      <h1 className="text-3xl font-bold">Kitchen Sink</h1>

      <Section title="Button variants">
        <div className="flex flex-wrap gap-3">
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="danger">Danger</Button>
        </div>
      </Section>

      <Section title="Button sizes">
        <div className="flex flex-wrap items-center gap-3">
          <Button size="sm">Small</Button>
          <Button size="md">Medium</Button>
          <Button size="lg">Large</Button>
        </div>
      </Section>

      <Section title="Button states">
        <div className="flex flex-wrap gap-3">
          <Button disabled>Disabled</Button>
          <Button onClick={() => alert('clicked')}>With onClick</Button>
          <Button className="bg-emerald-600 hover:bg-emerald-500">Overridden color</Button>
        </div>
      </Section>

      <Section title="Badges">
        <div className="flex flex-wrap gap-2">
          <Badge>Neutral</Badge>
          <Badge tone="success">Passed</Badge>
          <Badge tone="warning">Needs work</Badge>
          <Badge tone="danger">Failed</Badge>
          <Badge tone="info">Behavioral</Badge>
        </div>
      </Section>

      <Section title="Inputs">
        <div className="grid gap-4 sm:grid-cols-2">
          <Input label="Email" type="email" placeholder="you@example.com" />
          <Input label="Password" type="password" placeholder="••••••••" />
          <Input label="Email" defaultValue="not-an-email" error="Enter a valid email address" />
          <Input label="Disabled" placeholder="Can't touch this" disabled />
        </div>
      </Section>

      <Section title="Cards">
        <div className="grid gap-4 sm:grid-cols-2">
          <Card>
            <h3 className="font-semibold">Technical Interview</h3>
            <p className="mt-1 text-sm text-slate-400">5 questions · Medium difficulty</p>
            <div className="mt-4 flex items-center gap-2">
              <Badge tone="success">Score 8.2</Badge>
              <Badge>Completed</Badge>
            </div>
          </Card>
          <Card className="border-indigo-800 bg-indigo-950/40">
            <h3 className="font-semibold">Overridden styling</h3>
            <p className="mt-1 text-sm text-slate-400">Same component, different look.</p>
            <Button className="mt-4" size="sm">
              Start
            </Button>
          </Card>
        </div>
      </Section>
    </div>
  )
}
