import { useEffect, useState } from 'react'
import { Link, Route, Routes } from 'react-router-dom'
import { getFavorites } from './lib/favorites'
import FavoritesPage from './pages/FavoritesPage'
import SearchPage from './pages/SearchPage'
import UniversityPage from './pages/UniversityPage'

export default function App() {
  const [favCount, setFavCount] = useState(getFavorites().length)

  useEffect(() => {
    const update = () => setFavCount(getFavorites().length)
    window.addEventListener('favorites-changed', update)
    return () => window.removeEventListener('favorites-changed', update)
  }, [])

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <Link to="/" className="text-xl font-bold tracking-tight">
            Uni<span className="text-blue-600">Scout</span>
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            <Link to="/" className="hover:text-blue-600">
              Каталог
            </Link>
            <Link to="/favorites" className="hover:text-blue-600">
              Избранное{favCount > 0 && (
                <span className="ml-1 rounded-full bg-blue-600 px-1.5 py-0.5 text-xs text-white">
                  {favCount}
                </span>
              )}
            </Link>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-6">
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/u/:slug" element={<UniversityPage />} />
          <Route path="/favorites" element={<FavoritesPage />} />
        </Routes>
      </main>

      <footer className="mt-10 border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500">
        <p>UniScout — бесплатный каталог зарубежных университетов для абитуриентов из Казахстана.</p>
        <p className="mt-1">
          Данные проверяются вручную, но всегда сверяйтесь с официальным сайтом университета.
        </p>
      </footer>
    </div>
  )
}
