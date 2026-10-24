// Email reply buttons redirect here: /thanks?action=bought|keep|reject. Owner: Yared.
import { Link, useSearchParams } from "react-router-dom";

const MESSAGES: Record<string, string> = {
  bought: "Enjoy the show! We've stopped watching for you.",
  keep: "Got it. We'll keep watching for a better match.",
  reject: "Thanks for telling us. We're reviewing it and will keep watching.",
};

export default function Thanks() {
  const [params] = useSearchParams();
  return (
    <section className="py-16">
      <p className="text-2xl font-bold">{MESSAGES[params.get("action") ?? ""] ?? "Thanks!"}</p>
      <Link to="/me" className="mt-4 inline-block underline">See my watches</Link>
    </section>
  );
}
