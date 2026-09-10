import Link from "next/link";

const LINKS = [
  { href: "/", label: "Home" },
  { href: "/opportunities", label: "Opportunities" },
  { href: "/combinations", label: "Combination Lab" },
  { href: "/track-record", label: "Track Record" },
  { href: "/admin", label: "Admin" },
];

export function NavBar() {
  return (
    <nav className="border-b border-neutral-800 px-6 py-4">
      <div className="mx-auto flex max-w-5xl items-center justify-between">
        <span className="text-sm font-semibold tracking-tight text-neutral-100">
          Football AI
        </span>
        <div className="flex gap-5">
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm text-neutral-400 hover:text-neutral-100"
            >
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
