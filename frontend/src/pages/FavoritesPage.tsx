import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import UniversityCard from '../components/UniversityCard'
import { getFavorites } from '../lib/favorites'

export default function FavoritesPage() {
  const ids = getFavorites()
  // MVP: избранное в localStorage, фильтруем общий список на клиенте (каталог маленький).
  // После Supabase Auth (недели 5-6) заменяется на GET /me/favorites.
  const { data, isLoading } = useQuery({
    queryKey: ['search', { per_page: 100 }],
    queryFn: () => api.search({ page: 1 }),
  })

  const favorites = (data?.items ?? []).filter((u) => ids.includes(u.id))

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold">Избранное</h1>
      {isLoading && <p className="py-10 text-center text-slate-500">Загрузка…</p>}
      {!isLoading && favorites.length === 0 && (
        <p className="py-10 text-center text-slate-500">
          Пока пусто. Отмечай университеты звёздочкой в{' '}
          <Link to="/" className="text-blue-600">каталоге</Link> — они появятся здесь.
        </p>
      )}
      <div className="grid gap-3 sm:grid-cols-2">
        {favorites.map((u) => (
          <UniversityCard key={u.id} uni={u} />
        ))}
      </div>
    </div>
  )
}
