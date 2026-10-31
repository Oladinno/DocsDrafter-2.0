interface Testimonial {
  quote: string;
  initials: string;
  name: string;
  role: string;
}

const testimonials: Testimonial[] = [
  {
    quote:
      "Before DocsDrafter, our consultants manually transcribed briefings into proposals. Now a messy kickoff call becomes a structured draft in under a minute — and it exports flawlessly into Word.",
    initials: "AR",
    name: "Ana Rosetti",
    role: "Head of Delivery · Meridian Legal",
  },
  {
    quote:
      "Most AI tools output fluffy boilerplate. DocsDrafter understands document structure — sections, placeholders, versions — and slots into a real drafting workflow.",
    initials: "TK",
    name: "Thomas Kelly",
    role: "SVP, Design & Tech Group · Sirens Drone",
  },
  {
    quote:
      "The DOCX export is solid gold — styled headings, lists and tables land perfectly in front of Fortune 500 procurement teams. DocsDrafter 2.0 has saved our team hundreds of hours.",
    initials: "MC",
    name: "Marcus Osei",
    role: "Co-founder · Orchestrations Guild",
  },
];

export function Testimonials() {
  return (
    <section className="border-y border-line bg-surface/60 px-6 py-20">
      <div className="mx-auto max-w-6xl">
        <p className="text-center text-[11px] font-semibold uppercase tracking-[0.2em] text-brand">
          Field testing
        </p>
        <h2 className="mx-auto mt-3 max-w-2xl text-center font-display text-[32px] font-semibold leading-[1.1] tracking-[-0.02em] sm:text-[40px]">
          From first draft to board review
        </h2>

        <div className="mt-12 grid gap-5 md:grid-cols-3">
          {testimonials.map((testimonial) => (
            <figure
              key={testimonial.name}
              className="flex flex-col rounded-xl border border-line bg-surface p-6 shadow-l1"
            >
              <blockquote className="flex-1 text-[13.5px] font-medium leading-relaxed text-ink">
                “{testimonial.quote}”
              </blockquote>
              <figcaption className="mt-6 flex items-center gap-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-lavender text-[12px] font-semibold text-brand">
                  {testimonial.initials}
                </span>
                <span>
                  <span className="block text-[13px] font-semibold">
                    {testimonial.name}
                  </span>
                  <span className="block text-[11px] text-muted">
                    {testimonial.role}
                  </span>
                </span>
              </figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}
