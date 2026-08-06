// Избранное до логина живёт в localStorage; после подключения Supabase Auth (недели 5-6)
// содержимое мёрджится в БД одним вызовом POST /me/favorites/merge.
const KEY = 'uniscout.favorites'

function read(): number[] {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? '[]')
  } catch {
    return []
  }
}

export function getFavorites(): number[] {
  return read()
}

export function isFavorite(id: number): boolean {
  return read().includes(id)
}

export function toggleFavorite(id: number): boolean {
  const favs = read()
  const idx = favs.indexOf(id)
  if (idx >= 0) favs.splice(idx, 1)
  else favs.push(id)
  localStorage.setItem(KEY, JSON.stringify(favs))
  window.dispatchEvent(new Event('favorites-changed'))
  return idx < 0
}
