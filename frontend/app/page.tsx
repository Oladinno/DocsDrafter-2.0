import { Header } from "@/components/landing/header";
import { Hero } from "@/components/landing/hero";
import { Method } from "@/components/landing/method";
import { Features } from "@/components/landing/features";
import { Blueprints } from "@/components/landing/blueprints";
import { Testimonials } from "@/components/landing/testimonials";
import { Pricing } from "@/components/landing/pricing";
import { ClosingCta } from "@/components/landing/closing-cta";
import { Footer } from "@/components/landing/footer";

export default function Home() {
  return (
    <div className="min-h-screen bg-canvas text-ink">
      <Header />
      <main>
        <Hero />
        <Method />
        <Features />
        <Blueprints />
        <Testimonials />
        <Pricing />
        <ClosingCta />
      </main>
      <Footer />
    </div>
  );
}
