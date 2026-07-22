const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public details: unknown = null,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

function getAccessToken(): string | null {
  return (
    localStorage.getItem('access_token') ??
    localStorage.getItem('token') ??
    localStorage.getItem('lunaarc_access_token')
  )
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  const token = getAccessToken()

  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(
  `${API_BASE_URL}${path}`,
  {
  ...options,
  headers,
  credentials:'include'
  }
)
  const isJson = (response.headers.get('content-type') ?? '').includes('application/json')
  const data = isJson ? await response.json() : await response.text()

  if (!response.ok) {
    const message = typeof data === 'object' && data && 'detail' in data
      ? String((data as { detail: unknown }).detail)
      : `Request failed with status ${response.status}`
    throw new ApiError(message, response.status, data)
  }

  return data as T
}
