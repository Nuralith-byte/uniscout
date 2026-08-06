import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api, COUNTRY_NAMES, type SearchParams } from '../api/client'
import UniversityCard from '../components/UniversityCard'

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [qInput, setQInput] = useState(searchParams.get('q') ?? '')

  const params: SearchParams = {
    q: searchParams.get('q') ?? undefined,
    country: searchParams.get('country') ?? undefined,
    sat: searchParams.get('sat') ? Number(searchParams.get('sat')) : undefined,
    ielts: searchParams.get('ielts') ? Number(searchParams.get('ielts')) : undefined,
    max_tuition_usd: searchParams.get('budget') ? Number(searchParams.get('budget')) : undefined,
    sort: searchParams.get('sort') ?? undefined,
  }

  const { data: meta } = useQuery({ queryKey: ['filters'], queryFn: api.filters })
  const { data, isLoading, error } = useQuery({
    queryKey: ['search', params],
    queryFn: () => api.search(params),
  })

  const setParam = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams)
    if (value) next.set(key, value)
    else next.delete(key)
    setSearchParams(next, { replace: true })
  }

  return (
    <div>
      <div className="mb-2">
        <h1 className="text-2xl font-bold">Найди свой университет</h1>
        <p className="text-sm text-slate-500">
          Требования, стоимость и дедлайны зарубежных вузов — в одном месте, бесплатно.
        </p>
      </div>

      <form
        className="mb-4 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault()
          setParam('q', qInput.trim())
        }}
      >
        <input
          value={qInput}
          onChange={(e) => setQInput(e.target.value)}
          placeholder="Название вуза или город: MIT, каист, Сеул…"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
        <button className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
          Искать
        </button>
      </form>

      <div className="mb-5 grid grid-cols-2 gap-2 sm:grid-cols-5">
        <select
          value={searchParams.get('country') ?? ''}
          onChange={(e) => setParam('country', e.target.value)}
          className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
        >
          <option value="">Все страны</option>
          {(meta?.countries ?? []).map((c) => (
            <option key={c} value={c}>
              {COUNTRY_NAMES[c] ?? c}
            </option>
          ))}
        </select>

        <select
          value={searchParams.get('sat') ?? ''}
          onChange={(e) => setParam('sat', e.target.value)}
          className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
        >
          <option value="">Мой SAT</option>
          {[1000, 1100, 1200, 1300, 1400, 1500, 1600].map((s) => (
            <option key={s} value={s}>
              SAT {s}
            </option>
          ))}
        </select>

        <select
          value={searchParams.get('ielts') ?? ''}
          onChange={(e) => setParam('ielts', e.target.value)}
          className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
        >
          <option value="">Мой IELTS</option>
          {[5.5, 6.0, 6.5, 7.0, 7.5, 8.0].map((s) => (
            <option key={s} value={s}>
              IELTS {s}
            </option>
          ))}
        </select>

        <select
          value={searchParams.get('budget') ?? ''}
          onChange={(e) => setParam('budget', e.target.value)}
          className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
        >
          <option value="">Бюджет / год</option>
          {[5000, 10000, 20000, 30000, 50000, 80000].map((b) => (
            <option key={b} value={b}>
              до ${b.toLocaleString('en')}
            </option>
          ))}
        </select>

        <select
          value={searchParams.get('sort') ?? 'name'}
          onChange={(e) => setParam('sort', e.target.value)}
          className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
        >
          <option value="name">По названию</option>
          <option value="tuition_asc">Дешевле сначала</option>
          <option value="deadline_asc">Ближайший дедлайн</option>
        </select>
      </div>

      {isLoading && <p className="py-10 text-center text-slate-500">Загрузка… (бесплатный сервер может просыпаться до минуты)</p>}
      {error && (
        <p className="py-10 text-center text-red-500">
          Не удалось загрузить данные. Проверь, что бэкенд запущен.
        </p>
      )}

      {data && (
        <>
          <p className="mb-3 text-sm text-slate-500">Найдено: {data.total}</p>
          <div className="grid gap-3 sm:grid-cols-2">
            {data.items.map((u) => (
              <UniversityCard key={u.id} uni={u} />
            ))}
          </div>
          {data.total === 0 && (
            <p className="py-10 text-center text-slate-500">
              Ничего не нашлось — попробуй ослабить фильтры.
            </p>
          )}
        </>
      )}
    </div>
  )
}
