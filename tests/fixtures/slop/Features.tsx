import { Sparkles, Zap, Shield } from "lucide-react";
import { BentoGrid } from "@/components/magicui/bento-grid";
import { cn } from "@/lib/utils";

const features = [
  { title: "AI-powered insights", body: "Harness the power of AI to streamline your workflow." },
  { title: "Seamless integrations", body: "Connect your favorite tools effortlessly." },
];

export function Features() {
  return (
    <section className="py-24">
      <BentoGrid className="md:grid-cols-3">
        {features.map((f) => (
          <div key={f.title} className={cn("col-span-2 row-span-2 rounded-3xl p-8 shadow-xl", "bg-white/5 backdrop-blur-xl")}>
            <div className="flex size-12 items-center justify-center rounded-2xl bg-indigo-500/10">
              <Sparkles className="size-6 text-indigo-500" />
            </div>
            <h3 className="mt-4 text-[22px] font-semibold">{f.title}</h3>
            <p className="mt-2 p-[13px] text-zinc-400">{f.body}</p>
          </div>
        ))}
      </BentoGrid>
    </section>
  );
}
