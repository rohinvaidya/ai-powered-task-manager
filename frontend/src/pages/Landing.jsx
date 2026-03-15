import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const features = [
  { icon: '⚡', title: 'Blazing Fast APIs', desc: 'FastAPI backend with async PostgreSQL and Redis caching for sub-10ms responses.' },
  { icon: '🤖', title: 'AI Priority Engine', desc: 'Claude analyzes your tasks and suggests intelligent priorities and groupings.' },
  { icon: '🔔', title: 'Smart Reminders', desc: 'Celery workers monitor deadlines and fire notifications before you miss them.' },
  { icon: '📊', title: 'Live Analytics', desc: 'Completion rates, overdue counts, and velocity metrics across all projects.' },
  { icon: '🔒', title: 'JWT Auth', desc: 'Secure token-based authentication with bcrypt password hashing.' },
  { icon: '☁️', title: 'Cloud Ready', desc: 'Docker + Kubernetes manifests for AWS/GCP deployment out of the box.' },
]

const stats = [
  { value: 'FastAPI', label: 'Backend' },
  { value: 'Claude', label: 'AI Engine' },
  { value: 'Redis', label: 'Cache' },
  { value: 'K8s', label: 'Deploy' },
]

export default function Landing() {
  const navigate = useNavigate()
  const { user } = useAuth()

  return (
    <div style={styles.page}>
      {/* Noise overlay */}
      <div style={styles.noise} />

      {/* Nav */}
      <nav style={styles.nav}>
        <div style={styles.logo}>
          <span style={styles.logoDot} />
          TaskFlow
        </div>
        <div style={styles.navLinks}>
          {user ? (
            <button style={styles.btnPrimary} onClick={() => navigate('/dashboard')}>
              Open Dashboard →
            </button>
          ) : (
            <>
              <button style={styles.btnGhost} onClick={() => navigate('/login')}>Sign in</button>
              <button style={styles.btnPrimary} onClick={() => navigate('/register')}>Get started</button>
            </>
          )}
        </div>
      </nav>

      {/* Hero */}
      <section style={styles.hero}>
        <div style={styles.heroEyebrow} className="fade-up">
          <span style={styles.badge}>AI-Powered</span>
          <span style={styles.badgeText}>Backend Task Manager</span>
        </div>

        <h1 style={styles.heroTitle} className="fade-up">
          Tasks managed<br />
          <span style={styles.heroAccent}>intelligently.</span>
        </h1>

        <p style={styles.heroSub} className="fade-up">
          A production-grade task management system with AI priority suggestions,
          async workers, real-time analytics, and cloud-native deployment.
        </p>

        <div style={styles.heroCta} className="fade-up">
          {user ? (
            <button style={styles.btnPrimary} onClick={() => navigate('/dashboard')}>
              Go to Dashboard →
            </button>
          ) : (
            <>
              <button style={{ ...styles.btnPrimary, fontSize: '1rem', padding: '14px 32px' }} onClick={() => navigate('/register')}>
                Start for free
              </button>
              <button style={{ ...styles.btnGhost, fontSize: '1rem', padding: '14px 28px' }} onClick={() => navigate('/login')}>
                Sign in
              </button>
            </>
          )}
        </div>

        {/* Stats bar */}
        <div style={styles.statsBar} className="fade-up">
          {stats.map((s) => (
            <div key={s.label} style={styles.statItem}>
              <span style={styles.statValue}>{s.value}</span>
              <span style={styles.statLabel}>{s.label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Divider */}
      <div style={styles.divider} />

      {/* Features */}
      <section style={styles.features}>
        <p style={styles.sectionEyebrow}>What's inside</p>
        <h2 style={styles.sectionTitle}>Built for real-world scale</h2>
        <div style={styles.featureGrid}>
          {features.map((f, i) => (
            <div key={f.title} style={{ ...styles.featureCard, animationDelay: `${i * 0.07}s` }} className="fade-up">
              <span style={styles.featureIcon}>{f.icon}</span>
              <h3 style={styles.featureTitle}>{f.title}</h3>
              <p style={styles.featureDesc}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA banner */}
      <section style={styles.ctaBanner} className="fade-up">
        <div style={styles.ctaBannerInner}>
          <h2 style={styles.ctaTitle}>Ready to build?</h2>
          <p style={styles.ctaSub}>Create an account and start managing tasks with AI in seconds.</p>
          {!user && (
            <button style={{ ...styles.btnPrimary, fontSize: '1rem', padding: '14px 36px' }} onClick={() => navigate('/register')}>
              Create free account →
            </button>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer style={styles.footer}>
        <div style={styles.footerLogo}>
          <span style={styles.logoDot} />
          TaskFlow
        </div>
        <p style={styles.footerText}>Built with FastAPI · PostgreSQL · Redis · Claude AI</p>
      </footer>
    </div>
  )
}

const styles = {
  page: {
    minHeight: '100vh',
    position: 'relative',
    overflow: 'hidden',
  },
  noise: {
    position: 'fixed',
    inset: 0,
    backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E")`,
    pointerEvents: 'none',
    zIndex: 0,
  },
  nav: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 100,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '20px 48px',
    borderBottom: '1px solid var(--border)',
    backdropFilter: 'blur(20px)',
    background: 'rgba(10,10,15,0.8)',
  },
  logo: {
    fontFamily: 'var(--font-head)',
    fontWeight: 700,
    fontSize: '1.15rem',
    letterSpacing: '-0.01em',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    color: 'var(--text)',
  },
  logoDot: {
    display: 'inline-block',
    width: 8,
    height: 8,
    borderRadius: '50%',
    background: 'var(--accent)',
    boxShadow: '0 0 10px var(--accent)',
  },
  navLinks: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  },
  btnPrimary: {
    background: 'var(--accent)',
    color: '#0a0a0f',
    fontFamily: 'var(--font-head)',
    fontWeight: 700,
    fontSize: '0.88rem',
    padding: '10px 22px',
    borderRadius: 8,
    letterSpacing: '-0.01em',
    transition: 'opacity 0.15s, transform 0.15s',
    cursor: 'pointer',
    border: 'none',
  },
  btnGhost: {
    background: 'transparent',
    color: 'var(--text2)',
    fontFamily: 'var(--font-body)',
    fontWeight: 400,
    fontSize: '0.88rem',
    padding: '10px 16px',
    borderRadius: 8,
    border: '1px solid var(--border2)',
    transition: 'color 0.15s, border-color 0.15s',
    cursor: 'pointer',
  },
  hero: {
    position: 'relative',
    zIndex: 1,
    maxWidth: 860,
    margin: '0 auto',
    padding: '180px 48px 100px',
    textAlign: 'center',
  },
  heroEyebrow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    marginBottom: 32,
  },
  badge: {
    background: 'rgba(200,240,78,0.12)',
    color: 'var(--accent)',
    fontFamily: 'var(--font-mono)',
    fontSize: '0.75rem',
    fontWeight: 500,
    padding: '4px 12px',
    borderRadius: 20,
    border: '1px solid rgba(200,240,78,0.25)',
    letterSpacing: '0.05em',
  },
  badgeText: {
    color: 'var(--text3)',
    fontFamily: 'var(--font-mono)',
    fontSize: '0.75rem',
    letterSpacing: '0.03em',
  },
  heroTitle: {
    fontFamily: 'var(--font-head)',
    fontWeight: 800,
    fontSize: 'clamp(3rem, 8vw, 6rem)',
    lineHeight: 1.0,
    letterSpacing: '-0.04em',
    color: 'var(--text)',
    marginBottom: 28,
  },
  heroAccent: {
    color: 'var(--accent)',
    display: 'inline-block',
  },
  heroSub: {
    fontSize: '1.05rem',
    color: 'var(--text2)',
    lineHeight: 1.75,
    maxWidth: 560,
    margin: '0 auto 40px',
    fontWeight: 300,
  },
  heroCta: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 14,
    marginBottom: 64,
  },
  statsBar: {
    display: 'flex',
    justifyContent: 'center',
    gap: 0,
    borderTop: '1px solid var(--border)',
    borderBottom: '1px solid var(--border)',
    padding: '24px 0',
  },
  statItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 4,
    padding: '0 40px',
    borderRight: '1px solid var(--border)',
  },
  statValue: {
    fontFamily: 'var(--font-head)',
    fontWeight: 700,
    fontSize: '1.1rem',
    color: 'var(--text)',
    letterSpacing: '-0.02em',
  },
  statLabel: {
    fontFamily: 'var(--font-mono)',
    fontSize: '0.72rem',
    color: 'var(--text3)',
    letterSpacing: '0.06em',
    textTransform: 'uppercase',
  },
  divider: {
    height: 1,
    background: 'linear-gradient(90deg, transparent, var(--border2), transparent)',
    margin: '0 48px',
  },
  features: {
    position: 'relative',
    zIndex: 1,
    maxWidth: 1100,
    margin: '0 auto',
    padding: '100px 48px',
    textAlign: 'center',
  },
  sectionEyebrow: {
    fontFamily: 'var(--font-mono)',
    fontSize: '0.75rem',
    color: 'var(--accent)',
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
    marginBottom: 16,
  },
  sectionTitle: {
    fontFamily: 'var(--font-head)',
    fontWeight: 700,
    fontSize: 'clamp(1.8rem, 4vw, 2.8rem)',
    letterSpacing: '-0.03em',
    color: 'var(--text)',
    marginBottom: 56,
  },
  featureGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: 20,
    textAlign: 'left',
  },
  featureCard: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-lg)',
    padding: '28px 24px',
    transition: 'border-color 0.2s, transform 0.2s',
  },
  featureIcon: {
    fontSize: '1.6rem',
    display: 'block',
    marginBottom: 14,
  },
  featureTitle: {
    fontFamily: 'var(--font-head)',
    fontWeight: 600,
    fontSize: '1rem',
    letterSpacing: '-0.02em',
    color: 'var(--text)',
    marginBottom: 8,
  },
  featureDesc: {
    fontSize: '0.875rem',
    color: 'var(--text2)',
    lineHeight: 1.65,
    fontWeight: 300,
  },
  ctaBanner: {
    position: 'relative',
    zIndex: 1,
    margin: '0 48px 80px',
    borderRadius: 'var(--radius-xl)',
    background: 'linear-gradient(135deg, var(--surface) 0%, var(--bg3) 100%)',
    border: '1px solid var(--border2)',
    overflow: 'hidden',
  },
  ctaBannerInner: {
    padding: '80px 48px',
    textAlign: 'center',
    position: 'relative',
    zIndex: 1,
  },
  ctaTitle: {
    fontFamily: 'var(--font-head)',
    fontWeight: 800,
    fontSize: 'clamp(2rem, 5vw, 3.5rem)',
    letterSpacing: '-0.04em',
    color: 'var(--text)',
    marginBottom: 16,
  },
  ctaSub: {
    fontSize: '1rem',
    color: 'var(--text2)',
    marginBottom: 36,
    fontWeight: 300,
  },
  footer: {
    position: 'relative',
    zIndex: 1,
    borderTop: '1px solid var(--border)',
    padding: '32px 48px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  footerText: {
    fontFamily: 'var(--font-mono)',
    fontSize: '0.75rem',
    color: 'var(--text3)',
    letterSpacing: '0.03em',
  },
}
