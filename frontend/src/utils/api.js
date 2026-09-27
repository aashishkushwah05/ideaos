const API_BASE = '/api'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })
  let body = null
  try { body = await response.json() } catch { /* empty response */ }
  if (!response.ok) throw new Error(body?.detail || body?.message || `Request failed (${response.status})`)
  return body
}

// Multipart uploads must NOT set a JSON Content-Type — the browser needs to
// set its own `multipart/form-data; boundary=...` header.
async function uploadRequest(path, formData, { onProgress } = {}) {
  if (typeof XMLHttpRequest === 'undefined' || !onProgress) {
    const response = await fetch(`${API_BASE}${path}`, { method: 'POST', body: formData })
    let body = null
    try { body = await response.json() } catch { /* empty response */ }
    if (!response.ok) throw new Error(body?.detail || body?.message || `Request failed (${response.status})`)
    return body
  }
  // XHR path only used when the caller wants upload-progress events.
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${API_BASE}${path}`)
    xhr.upload.onprogress = (e) => { if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100)) }
    xhr.onload = () => {
      let body = null
      try { body = JSON.parse(xhr.responseText) } catch { /* empty response */ }
      if (xhr.status >= 200 && xhr.status < 300) resolve(body)
      else reject(new Error(body?.detail || body?.message || `Request failed (${xhr.status})`))
    }
    xhr.onerror = () => reject(new Error('Network error during upload.'))
    xhr.send(formData)
  })
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body: JSON.stringify(body) }),
  patch: (path, body) => request(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: (path) => request(path, { method: 'DELETE' }),
  upload: (path, formData, opts) => uploadRequest(path, formData, opts),
}
