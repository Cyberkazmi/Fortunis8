import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY
export const previewMode = import.meta.env.VITE_PREVIEW_MODE === 'true'

export const previewSession = previewMode
  ? {
      access_token: 'preview-token',
      user: { id: 'preview-user', email: 'preview@fortunis8.local', user_metadata: { display_name: 'Preview Seeker' } },
    }
  : null

export const supabase = url && anonKey
  ? createClient(url, anonKey, {
      auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
    })
  : null

export async function apiFetch(path, session, options = {}) {
  const headers = new Headers(options.headers || {})
  headers.set('Content-Type', 'application/json')
  if (session?.access_token) headers.set('Authorization', `Bearer ${session.access_token}`)
  return fetch(path, { ...options, headers })
}
