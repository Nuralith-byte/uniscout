import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, COUNTRY_NAMES, CURRENCY_SYMBOLS, type Cost } from '../api/client'
import { isFavorite, toggleFavorite } from '../lib/favorites'

const COST_LABELS: Record<Cost['cost_type'], string> = {
  tuition_year: 'Обучение / год',
  application_fee: 'Сбор за подачу',
  living_estimate_year: 'Проживание / год (оценка)',
}

const SAT_LABELS: Record<string, string> = {
  required: 'обязателен',
  optional: 'по желанию',
  not_used: 'не используется',
}

function fmtMoney(c: Cost): string {
  const sym = CURRENCY_SYMBOLS[c.currency] ?? c.currency + ' '
  const orig = `${sym}${Number(c.amount).toLocaleString('ru')}`
  if (c.currency !== 'USD' && c.amount_usd != null) {
    return `${orig} (≈ $${Math.round(c.amount_usd).toLocaleString('ru')})`
  }
  return orig
}

export default function UniversityPage() {
  const { slug } = useParams<{ slug: string }>()
  const { data: uni, isLoading, error } = useQuery({
    queryKey: ['university', slug],
    queryFn: () => api.detail(slug!),
    enabled: !!slug,
  })
  const [fav, setFav] = useState<boolean | null>(null)

  if (isLoading) return <p className="py-10 text-center text-slate-500">Загрузка…</p>
  if (error || !uni)
    return (
      <p className="py-10 text-center text-slate-500">
        Университет не найден. <Link to="/" className="text-blue-600">← к каталогу</Link>
      </p>
    )

  const isFav = fav ?? isFavorite(uni.id)
  const req = uni.requirements.find((r) => r.degree_level === 'bachelor')

  return (
    <div className="mx-auto max-w-3xl">
      <Link to="/" className="text-sm text-blue-600">← к каталогу</Link>

      <div className="mt-3 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold leading-tight">{uni.name_ru ?? uni.name_en}</h1>
          {uni.name_ru && <p className="text-slate-500">{uni.name_en}</p>}
          <p className="mt-1 text-sm text-slate-500">
            {COUNTRY_NAMES[uni.country_code] ?? uni.country_code}
            {uni.city ? ` · ${uni.city}` : ''}
            {uni.rankings?.qs && (
              <>
                {' · '}
                <a
                  href={`https://www.topuniversities.com/universities?search=${encodeURIComponent(uni.name_en)}`}
                  target="_blank"
                  rel="noreferrer"
                  className="text-blue-600"
                >
                  QS #{uni.rankings.qs} ↗
                </a>
              </>
            )}
          </p>
        </div>
        <button
          onClick={() => setFav(toggleFavorite(uni.id))}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm hover:bg-slate-100"
        >
          {isFav ? '★ В избранном' : '☆ В избранное'}
        </button>
      </div>

      {uni.description_ru && <p className="mt-4 text-slate-700">{uni.description_ru}</p>}

      {req && (
        <section className="mt-6">
          <h2 className="mb-2 text-lg font-semibold">Требования (бакалавриат)</h2>
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="w-full text-sm">
              <tbody className="divide-y divide-slate-100">
                {req.sat_required && (
                  <Row label="SAT" value={`${SAT_LABELS[req.sat_required] ?? req.sat_required}${req.sat_p25 && req.sat_p75 ? ` · диапазон поступивших ${req.sat_p25}–${req.sat_p75}` : ''}${req.sat_min ? ` · минимум ${req.sat_min}` : ''}`} />
                )}
                {req.ielts_min != null && <Row label="IELTS" value={`от ${req.ielts_min}`} />}
                {req.toefl_ibt_min != null && <Row label="TOEFL iBT" value={`от ${req.toefl_ibt_min}`} />}
                {req.gpa_min != null && <Row label="GPA" value={`от ${req.gpa_min}`} />}
                {req.extracurriculars_weight && req.extracurriculars_weight !== 'none' && (
                  <Row
                    label="Внеклассная активность"
                    value={req.extracurriculars_weight === 'important' ? 'очень важна' : 'учитывается'}
                  />
                )}
              </tbody>
            </table>
          </div>
          {req.notes_ru && <p className="mt-2 text-sm text-slate-600">{req.notes_ru}</p>}
        </section>
      )}

      {uni.costs.length > 0 && (
        <section className="mt-6">
          <h2 className="mb-2 text-lg font-semibold">Стоимость</h2>
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="w-full text-sm">
              <tbody className="divide-y divide-slate-100">
                {uni.costs.map((c) => (
                  <Row key={c.cost_type} label={COST_LABELS[c.cost_type]} value={fmtMoney(c)} />
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {uni.deadlines.length > 0 && (
        <section className="mt-6">
          <h2 className="mb-2 text-lg font-semibold">Дедлайны</h2>
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="w-full text-sm">
              <tbody className="divide-y divide-slate-100">
                {uni.deadlines.map((d, i) => (
                  <Row
                    key={i}
                    label={d.round_name + (d.intake_term ? ` (${d.intake_term})` : '')}
                    value={new Date(d.deadline_date).toLocaleDateString('ru', {
                      day: 'numeric',
                      month: 'long',
                      year: 'numeric',
                    })}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <div className="mt-8 flex flex-wrap gap-3">
        {uni.apply_url && (
          <a
            href={uni.apply_url}
            target="_blank"
            rel="noreferrer"
            onClick={() => api.outboundClick(uni.id, uni.apply_url!)}
            className="rounded-lg bg-blue-600 px-5 py-2.5 font-medium text-white hover:bg-blue-700"
          >
            Подать заявку на официальном сайте ↗
          </a>
        )}
        {uni.website_url && (
          <a
            href={uni.website_url}
            target="_blank"
            rel="noreferrer"
            className="rounded-lg border border-slate-300 px-5 py-2.5 hover:bg-slate-100"
          >
            Сайт университета ↗
          </a>
        )}
      </div>

      <p className="mt-6 text-xs text-slate-400">
        {uni.last_verified_at &&
          `Проверено: ${new Date(uni.last_verified_at).toLocaleDateString('ru')}. `}
        Данные могут меняться — всегда сверяйтесь с официальным сайтом.
        {uni.source_url && (
          <>
            {' '}
            <a href={uni.source_url} target="_blank" rel="noreferrer" className="text-blue-500">
              Источник ↗
            </a>
          </>
        )}
      </p>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <tr>
      <td className="w-1/2 px-4 py-2.5 text-slate-500">{label}</td>
      <td className="px-4 py-2.5 font-medium">{value}</td>
    </tr>
  )
}
