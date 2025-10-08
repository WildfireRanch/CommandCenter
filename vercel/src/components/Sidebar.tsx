'use client'

import Image from "next/image"
import Link from "next/link"
import { usePathname } from "next/navigation"

const links = [
  { href: "/", label: "Home", icon: "/WildfireMang.png" },
  { href: "/dashboard", label: "Dashboard", icon: "/Hoody.png" },
  { href: "/chat", label: "Ask Agent", icon: "/Echo.png" },
  { href: "/studio", label: "Operator", icon: "/Relay.png" },
  { href: "/energy", label: "Energy", icon: "/PlannerCop.png" },
  { href: "/logs", label: "Logs", icon: "/PigTails.png" },
  { href: "/status", label: "Status", icon: "/beanie and smoke.png" },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-48 bg-white border-r p-3 space-y-2 min-h-screen">
      <h2 className="text-lg font-bold flex items-center gap-2 mb-4">
        <Image src="/wildfireranch.png" alt="logo" width={164} height={164} className="image-rendering-pixelated" unoptimized />
      </h2>
      <nav className="mt-4 space-y-2 text-sm">
        {links.map(({ href, label, icon }) => (
          <Link
            key={href}
            href={href}
            className={`flex items-center gap-2 px-2 py-1 rounded hover:bg-gray-100 transition-colors ${
              pathname === href ? "bg-blue-100 font-semibold" : ""
            }`}
          >
            <Image src={icon} alt={label} width={48} height={48} priority={false} className="image-rendering-pixelated" unoptimized />
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  )
}
