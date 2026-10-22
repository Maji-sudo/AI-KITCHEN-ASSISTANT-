import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
  }).format(new Date(date))
}

export function formatTime(date: string | Date): string {
  return new Intl.DateTimeFormat('en-IN', {
    hour: '2-digit', minute: '2-digit', hour12: true,
  }).format(new Date(date))
}

export function formatDateTime(date: string | Date): string {
  return `${formatDate(date)}, ${formatTime(date)}`
}

export function formatGrams(grams: number): string {
  if (grams >= 1000) return `${(grams / 1000).toFixed(2)} kg`
  return `${grams.toFixed(0)} g`
}

export function formatPPM(ppm: number): string {
  return `${ppm.toFixed(1)} ppm`
}

export function getPPMStatus(ppm: number): 'safe' | 'warning' | 'danger' {
  if (ppm < 500) return 'safe'
  if (ppm < 1000) return 'warning'
  return 'danger'
}

export function getCylinderColor(percentage: number): string {
  if (percentage > 50) return '#16a34a'
  if (percentage > 25) return '#f59e0b'
  return '#dc2626'
}

export function getScoreColor(score: number): string {
  if (score >= 75) return '#16a34a'
  if (score >= 50) return '#f59e0b'
  return '#dc2626'
}

export function getDaysLeftLabel(days: number): string {
  if (days <= 0) return 'Empty'
  if (days === 1) return '1 day left'
  return `${days} days left`
}

export function truncate(str: string, length = 60): string {
  return str.length > length ? str.slice(0, length) + '…' : str
}
