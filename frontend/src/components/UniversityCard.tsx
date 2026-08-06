import { useState } from 'react'
import { Link } from 'react-router-dom'
import { COUNTRY_NAMES, type UniversityCard as CardData } from '../api/client'
import { isFavorite, toggleFavorite } from '../lib/favorites'

function daysAgo(dateStr: string | null): string | null {
  if (!dateStr) return null
  const days = Math.floor((Date.now() - new Date(dateStr).getTime()) / 86_400_000)
  if (days <= 0) return 'проверено сегодня'
  return `проверено ${days} дн. назад`
}

export default function UniversityCard({ uni }: { uni: CardData }) {
  const [fav, setFav] = useState(isFavorite(uni.id))
  const verified = daysAgo(uni.last_verified_at)

  return (
    <div className="relative rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:shadow-md">
      <button
        onClick={() => setFav(toggleFavorite(uni.id))}
        title={fav ? 'Убрать из избранного' : 'В избранное'}
        className="absolute right-3 top-3 text-xl"
      >
        {fav ? '★' : '☆'}
      </button>

      <Link to={`/u/${uni.slug}`} className="block pr-8">
        <h3 className="font-semibold leading-snug hover:text-blue-600">
          {uni.name_ru ?? uni.name_en}
        </h3>
        <p className="text-sm text-slate-500">
          {COUNTRY_NAMES[uni.country_code] ?? uni.country_code}
          {uni.city ? ` · ${uni.city}` : ''}
        </p>
      </Link>

      <div className="mt-3 flex flex-wrap gap-2 text-xs">
        {uni.tuition_usd != null && (
          <span className="rounded-full bg-emerald-50 px-2 py-1 text-emerald-700">
            ≈ ${Math.round(uni.tuition_usd).toLocaleString('ru')} / год
          </span>
        )}
        {uni.sat_p25 != null && uni.sat_p75 != null && (
          <span className="rounded-full bg-blue-50 px-2 py-1 text-blue-700">
            SAT {uni.sat_p25}–{uni.sat_p75}
          </span>
        )}
        {uni.ielts_min != null && (
          <span className="rounded-full bg-blue-50 px-2 py-1 text-blue-700">
            IELTS {uni.ielts_min}+
          </span>
        )}
        {uni.next_deadline && (
          <span className="rounded-full bg-amber-50 px-2 py-1 text-amber-700">
            дедлайн {new Date(uni.next_deadline).toLocaleDateString('ru')}
          </span>
        )}
        {uni.requirements_unknown && (
          <span className="rounded-full bg-slate-100 px-2 py-1 text-slate-500">
            требования уточняйте на сайте
          </span>
        )}
      </div>

      {verified && <p className="mt-2 text-[11px] text-slate-400">{verified}</p>}
    </div>
  )
}
