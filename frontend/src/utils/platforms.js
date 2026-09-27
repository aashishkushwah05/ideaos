import {
  Camera,
  PlayCircle,
  Briefcase,
  Code2,
  MessageSquare,
  Users2,
  Globe,
} from 'lucide-react'

// Mirrors the platform set the backend's deterministic extractor detects
// (see backend/app/importer/url_utils.py). Icons are intentionally generic
// (camera, play, briefcase, etc.) rather than brand logos — lucide-react
// no longer ships third-party brand marks, and avoiding them here sidesteps
// any trademark concerns in a UI kit that will be reused/screenshotted.
export const PLATFORMS = {
  Instagram: { label: 'Instagram', icon: Camera, color: '#E1306C' },
  YouTube: { label: 'YouTube', icon: PlayCircle, color: '#FF3B3B' },
  LinkedIn: { label: 'LinkedIn', icon: Briefcase, color: '#3B82F6' },
  GitHub: { label: 'GitHub', icon: Code2, color: '#A78BFA' },
  'X/Twitter': { label: 'X/Twitter', icon: MessageSquare, color: '#E8EBF1' },
  Facebook: { label: 'Facebook', icon: Users2, color: '#4C8BF5' },
  'Website/Other': { label: 'Website', icon: Globe, color: '#3DD68C' },
}

export function platformMeta(platform) {
  return PLATFORMS[platform] || PLATFORMS['Website/Other']
}
