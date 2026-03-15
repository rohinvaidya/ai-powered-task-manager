import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { register, login, getMe } from '../api/client'
import { useAuth } from '../hooks/useAuth'

export default function Register() {
  const navigate = useNavigate()
  const { signIn } = useAuth()
  const [form, setForm] = useState({ email: '', username: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(form)
      const res = await login({ email: form.email, password: form.password })
      const me = await getMe()
      signIn(res.data.access_token, me.data)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card} className="fade-up">
        <div style={styles.logoRow}>
          <span style={styles.dot} />
          <span style={styles.logoText}>TaskFlow</span>
        </div>
        <h1 style={styles.title}>Create account</h1>
        <p style={styles.sub}>Start managing tasks with AI</p>

        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.label}>Email</label>
          <input style={styles.input} type="email" placeholder="you@example.com"
            value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          <label style={styles.label}>Username</label>
          <input style={styles.input} type="text" placeholder="yourname"
            value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
          <label style={styles.label}>Password</label>
          <input style={styles.input} type="password" placeholder="••••••••"
            value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          {error && <p style={styles.error}>{error}</p>}
          <button style={{ ...styles.btn, opacity: loading ? 0.6 : 1 }} type="submit" disabled={loading}>
            {loading ? 'Creating account…' : 'Create account →'}
          </button>
        </form>
        <p style={styles.switchText}>
          Already have an account?{' '}
          <Link to="/login" style={styles.link}>Sign in</Link>
        </p>
      </div>
    </div>
  )
}

const styles = {
  page: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    background: 'radial-gradient(ellipse at 50% 0%, rgba(124,106,247,0.06) 0%, transparent 60%)',
  },
  card: {
    width: '100%',
    maxWidth: 420,
    background: 'var(--surface)',
    border: '1px solid var(--border2)',
    borderRadius: 'var(--radius-xl)',
    padding: '40px 36px',
  },
  logoRow: { display: 'flex', alignItems: 'center', gap: 8, marginBottom: 28 },
  dot: { width: 8, height: 8, borderRadius: '50%', background: 'var(--accent)', boxShadow: '0 0 10px var(--accent)', display: 'inline-block' },
  logoText: { fontFamily: 'var(--font-head)', fontWeight: 700, fontSize: '1rem', color: 'var(--text)' },
  title: { fontFamily: 'var(--font-head)', fontWeight: 700, fontSize: '1.8rem', letterSpacing: '-0.03em', color: 'var(--text)', marginBottom: 6 },
  sub: { fontSize: '0.875rem', color: 'var(--text2)', marginBottom: 28, fontWeight: 300 },
  form: { display: 'flex', flexDirection: 'column', gap: 6 },
  label: { fontSize: '0.78rem', color: 'var(--text2)', fontFamily: 'var(--font-mono)', letterSpacing: '0.04em', marginTop: 10, marginBottom: 4 },
  input: { background: 'var(--bg2)', border: '1px solid var(--border2)', borderRadius: 8, padding: '11px 14px', fontSize: '0.9rem', color: 'var(--text)', outline: 'none', width: '100%' },
  error: { fontSize: '0.82rem', color: 'var(--accent3)', marginTop: 8 },
  btn: { marginTop: 20, background: 'var(--accent)', color: '#0a0a0f', fontFamily: 'var(--font-head)', fontWeight: 700, fontSize: '0.95rem', padding: '13px', borderRadius: 8, border: 'none', cursor: 'pointer' },
  switchText: { textAlign: 'center', marginTop: 20, fontSize: '0.83rem', color: 'var(--text3)' },
  link: { color: 'var(--accent)', fontWeight: 500 },
}
