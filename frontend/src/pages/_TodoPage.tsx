// Placeholder used by unbuilt pages. Delete once every page is real.
export default function TodoPage({ title, spec }: { title: string; spec: string[] }) {
  return (
    <section className="py-8">
      <h2 className="text-2xl font-bold">{title}</h2>
      <p className="mt-2 text-sm text-amber-700">TODO(Yared): not built yet</p>
      <ul className="mt-4 list-disc pl-6 text-sm text-slate-600">
        {spec.map((s) => (
          <li key={s}>{s}</li>
        ))}
      </ul>
    </section>
  );
}
