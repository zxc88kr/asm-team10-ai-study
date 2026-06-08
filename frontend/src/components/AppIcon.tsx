import {
  Moon, Lightbulb, MapPin, Shield,
  ShoppingBag, ShoppingCart, Pill, Coffee, Shirt, HeartPulse,
  Wallet, Train, Home, Building2,
  Droplets, Settings, Store, StickyNote, Check, Camera, Sun, Hospital,
  type LucideIcon,
} from 'lucide-react'

const ICON_MAP: Record<string, LucideIcon> = {
  moon: Moon,
  lightbulb: Lightbulb,
  'map-pin': MapPin,
  shield: Shield,
  'shopping-bag': ShoppingBag,
  'shopping-cart': ShoppingCart,
  pill: Pill,
  coffee: Coffee,
  shirt: Shirt,
  'heart-pulse': HeartPulse,
  wallet: Wallet,
  train: Train,
  home: Home,
  'building-2': Building2,
  droplets: Droplets,
  settings: Settings,
  store: Store,
  note: StickyNote,
  check: Check,
  camera: Camera,
  sun: Sun,
  hospital: Hospital,
}

interface AppIconProps {
  name: string
  size?: number
  color?: string
  className?: string
}

export function AppIcon({ name, size = 16, color, className }: AppIconProps) {
  const Icon = ICON_MAP[name]
  if (!Icon) return null
  return <Icon size={size} color={color} className={className} />
}
