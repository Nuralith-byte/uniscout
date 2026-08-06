// Тонкий API-клиент. В проде задай VITE_API_URL (URL Render-сервиса), локально работает Vite-proxy.
const BASE = (import.meta.env.VITE_API_URL ?? '') + '/api/v1'

export interface UniversityCard {
  id: number
  slug: string
  name_en: string
  name_ru: string | null
  country_code: string
  city: string | null
  logo_url: string | null
  tuition_usd: number | null
  application_fee_usd: number | null
  sat_p25: number | null
  sat_p75: number | null
  ielts_min: number | null
  next_deadline: string | null
  requirements_unknown: boolean
  last_verified_at: string | null
}

export interface SearchResponse {
  items: UniversityCard[]
  total: number
  page: number
  per_page: number
}

export interface Requirement {
  degree_level: string
  sat_min: number | null
  sat_p25: number | null
  sat_p75: number | null
  sat_required: string | null
  ielts_min: number | null
  toefl_ibt_min: number | null
  gpa_min: number | null
  extracurriculars_weight: string | null
  notes_ru: string | null
  source_url: string | null
  last_verified_at: string | null
}

export interface Cost {
  degree_level: string
  cost_type: 'tuition_year' | 'application_fee' | 'living_estimate_year'
  amount: number
  currency: string
  amount_usd: number | null
  academic_year: string | null
  last_verified_at: string | null
}

export interface Deadline {
  degree_level: string
  round_name: string
  deadline_date: string
  intake_term: string | null
  last_verified_at: string | null
}

export interface UniversityDetail {
  id: number
  slug: string
  name_en: string
  name_ru: string | null
  country_code: string
  city: string | null
  website_url: string | null
  apply_url: string | null
  application_system: string | null
  description_ru: string | null
  rankings: Record<string, number> | null
  source_url: string | null
  last_verified_at: string | null
  requirements: Requirement[]
  costs: Cost[]
  deadlines: Deadline[]
}

export interface FilterMeta {
  countries: string[]
  degree_levels: string[]
  tuition_usd_min: number | null
  tuition_usd_max: number | null
}

export interface SearchParams {
  q?: string
  country?: string
  sat?: number
  ielts?: number
  max_tuition_usd?: number
  sort?: string
  page?: number
}

async function get<T>(path: string, params?: Record<string, unknown>): Promise<T> {
  const url = new URL(BASE + path, window.location.origin)
  for (const [k, v] of Object.entries(params ?? {})) {
    if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, String(v))
  }
  const res = await fetch(url)
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`)
  return res.json()
}

export const api = {
  search: (params: SearchParams) => get<SearchResponse>('/universities', { ...params }),
  detail: (slug: string) => get<UniversityDetail>(`/universities/${slug}`),
  filters: () => get<FilterMeta>('/meta/filters'),
  outboundClick: (university_id: number, target_url: string) => {
    // fire-and-forget beacon — не блокируем переход
    navigator.sendBeacon?.(
      BASE + '/events/outbound-click',
      new Blob([JSON.stringify({ university_id, target_url })], { type: 'application/json' }),
    ) ||
      fetch(BASE + '/events/outbound-click', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ university_id, target_url }),
        keepalive: true,
      })
  },
}

export const COUNTRY_NAMES: Record<string, string> = {
  US: 'США',
  GB: 'Великобритания',
  CA: 'Канада',
  DE: 'Германия',
  KR: 'Южная Корея',
  JP: 'Япония',
  CN: 'Китай',
  TR: 'Турция',
  HK: 'Гонконг',
  KZ: 'Казахстан',
}

export const CURRENCY_SYMBOLS: Record<string, string> = {
  USD: '$', EUR: '€', GBP: '£', KZT: '₸', KRW: '₩', TRY: '₺', CAD: 'C$', HKD: 'HK$',
}
