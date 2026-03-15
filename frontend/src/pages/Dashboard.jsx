import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import {
  getProjects, createProject, deleteProject,
  getTasks, createTask, updateTask, deleteTask,
  getSuggestions, applySuggestions,
  getMyAnalytics,
} from '../api/client'

const STATUS_COLORS = {
  todo:        { bg: 'rgba(92,90,110,0.2)', text: '#9996a8', label: 'To Do' },
  in_progress: { bg: 'rgba(124,106,247,0.15)', text: '#a89af7', label: 'In Progress' },
  done:        { bg: 'rgba(200,240,78,0.12)', text: '#c8f04e', label: 'Done' },
  cancelled:   { bg: 'rgba(240,96,96,0.12)', text: '#f09090', label: 'Cancelled' },
}

const PRIORITY_COLORS = {
  low:    '#5c5a6e',
  medium: '#9996a8',
  high:   '#7c6af7',
  urgent: '#f06060',
}

const PRIORITY_DOT = { low: '○', medium: '●', high: '◆', urgent: '▲' }

export default function Dashboard() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

  const [projects, setProjects] = useState([])
  const [selectedProject, setSelectedProject] = useState(null)
  const [tasks, setTasks] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [analyticsLoading, setAnalyticsLoading] = useState(false)
  const [suggestions, setSuggestions] = useState(null)
  const [newProjectName, setNewProjectName] = useState('')
  const [newTaskTitle, setNewTaskTitle] = useState('')
  const [newTaskPriority, setNewTaskPriority] = useState('medium')
  const [newTaskDueDate, setNewTaskDueDate] = useState('')
  const [loadingAI, setLoadingAI] = useState(false)
  const [activeTab, setActiveTab] = useState('tasks')
  const [showNewProject, setShowNewProject] = useState(false)
  const [showNewTask, setShowNewTask] = useState(false)

  // Shared analytics refresh — call after every mutation
  const refreshAnalytics = useCallback(async () => {
    setAnalyticsLoading(true)
    try {
      const r = await getMyAnalytics()
      setAnalytics(r.data)
    } catch (_) {}
    finally { setAnalyticsLoading(false) }
  }, [])

  // Initial load
  useEffect(() => {
    getProjects().then((r) => {
      setProjects(r.data)
      if (r.data.length > 0) setSelectedProject(r.data[0])
    })
    refreshAnalytics()
  }, [refreshAnalytics])

  // Load tasks when project changes
  useEffect(() => {
    if (!selectedProject) return
    getTasks(selectedProject.id).then((r) => setTasks(r.data))
    setSuggestions(null)
  }, [selectedProject])

  // Refresh analytics whenever tasks array changes
  useEffect(() => {
    refreshAnalytics()
  }, [tasks, refreshAnalytics])

  const handleCreateProject = async (e) => {
    e.preventDefault()
    if (!newProjectName.trim()) return
    const res = await createProject({ name: newProjectName })
    setProjects((p) => [res.data, ...p])
    setSelectedProject(res.data)
    setNewProjectName('')
    setShowNewProject(false)
    refreshAnalytics()
  }

  const handleDeleteProject = async (id) => {
    await deleteProject(id)
    const updated = projects.filter((p) => p.id !== id)
    setProjects(updated)
    setSelectedProject(updated[0] || null)
    setTasks([])
    refreshAnalytics()
  }

  const handleCreateTask = async (e) => {
    e.preventDefault()
    if (!newTaskTitle.trim() || !selectedProject) return
    const payload = { title: newTaskTitle, priority: newTaskPriority }
    if (newTaskDueDate) payload.due_date = new Date(newTaskDueDate).toISOString()
    const res = await createTask(selectedProject.id, payload)
    setTasks((t) => [...t, res.data])
    setNewTaskTitle('')
    setNewTaskDueDate('')
    setShowNewTask(false)
  }

  const handleStatusChange = async (task, status) => {
    const res = await updateTask(selectedProject.id, task.id, { status })
    setTasks((t) => t.map((x) => (x.id === task.id ? res.data : x)))
  }

  const handleUpdate = async (task, fields) => {
    const res = await updateTask(selectedProject.id, task.id, fields)
    setTasks((t) => t.map((x) => (x.id === task.id ? res.data : x)))
  }

  const handleDeleteTask = async (task) => {
    await deleteTask(selectedProject.id, task.id)
    setTasks((t) => t.filter((x) => x.id !== task.id))
  }

  const handleGetSuggestions = async () => {
    if (!selectedProject) return
    setLoadingAI(true)
    try {
      const res = await getSuggestions(selectedProject.id)
      setSuggestions(res.data)
      setActiveTab('ai')
    } finally {
      setLoadingAI(false)
    }
  }

  const handleApplySuggestions = async () => {
    if (!selectedProject) return
    setLoadingAI(true)
    try {
      await applySuggestions(selectedProject.id)
      const res = await getTasks(selectedProject.id)
      setTasks(res.data)
      setActiveTab('tasks')
      setSuggestions(null)
    } finally {
      setLoadingAI(false)
    }
  }

  const handleSignOut = () => { signOut(); navigate('/') }

  const tasksByStatus = {
    todo: tasks.filter((t) => t.status === 'todo'),
    in_progress: tasks.filter((t) => t.status === 'in_progress'),
    done: tasks.filter((t) => t.status === 'done'),
    cancelled: tasks.filter((t) => t.status === 'cancelled'),
  }

  return (
    <div style={styles.layout}>
      {/* Sidebar */}
      <aside style={styles.sidebar}>
        <div style={styles.sidebarTop}>
          <div style={styles.logoRow}>
            <span style={styles.dot} />
            <span style={styles.logoText}>TaskFlow</span>
          </div>

          <div style={styles.userRow}>
            <div style={styles.avatar}>{user?.username?.[0]?.toUpperCase()}</div>
            <div>
              <div style={styles.userName}>{user?.username}</div>
              <div style={styles.userEmail}>{user?.email}</div>
            </div>
          </div>

          <div style={styles.sectionLabel}>Projects</div>

          <div style={styles.projectList}>
            {projects.map((p) => (
              <div
                key={p.id}
                style={{
                  ...styles.projectItem,
                  ...(selectedProject?.id === p.id ? styles.projectItemActive : {}),
                }}
                onClick={() => setSelectedProject(p)}
              >
                <span style={styles.projectName}>{p.name}</span>
                <button
                  style={styles.deleteBtn}
                  onClick={(e) => { e.stopPropagation(); handleDeleteProject(p.id) }}
                  title="Delete project"
                >✕</button>
              </div>
            ))}
          </div>

          {showNewProject ? (
            <form onSubmit={handleCreateProject} style={styles.inlineForm}>
              <input
                autoFocus
                style={styles.inlineInput}
                placeholder="Project name"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
              />
              <button style={styles.inlineSubmit} type="submit">Add</button>
            </form>
          ) : (
            <button style={styles.newProjectBtn} onClick={() => setShowNewProject(true)}>
              + New project
            </button>
          )}
        </div>

        <button style={styles.signOutBtn} onClick={handleSignOut}>Sign out</button>
      </aside>

      {/* Main */}
      <main style={styles.main}>
        {!selectedProject ? (
          <div style={styles.empty}>
            <p style={styles.emptyTitle}>No project selected</p>
            <p style={styles.emptyText}>Create a project to get started</p>
          </div>
        ) : (
          <>
            {/* Header */}
            <div style={styles.mainHeader}>
              <div>
                <h1 style={styles.projectTitle}>{selectedProject.name}</h1>
                <p style={styles.taskCount}>{tasks.length} task{tasks.length !== 1 ? 's' : ''}</p>
              </div>
              <div style={styles.headerActions}>
                <button
                  style={{ ...styles.aiBtn, opacity: loadingAI ? 0.6 : 1 }}
                  onClick={handleGetSuggestions}
                  disabled={loadingAI}
                >
                  {loadingAI ? '⏳ Analyzing…' : '✦ AI Suggestions'}
                </button>
                <button style={styles.primaryBtn} onClick={() => setShowNewTask(true)}>+ Add task</button>
              </div>
            </div>

            {/* Tabs */}
            <div style={styles.tabs}>
              {['tasks', 'ai', 'analytics'].map((tab) => (
                <button
                  key={tab}
                  style={{ ...styles.tab, ...(activeTab === tab ? styles.tabActive : {}) }}
                  onClick={() => setActiveTab(tab)}
                >
                  {tab === 'tasks' ? '📋 Tasks' : tab === 'ai' ? '✦ AI Panel' : '📊 Analytics'}
                </button>
              ))}
            </div>

            {/* ── Tasks Tab ── */}
            {activeTab === 'tasks' && (
              <div style={styles.tabContent}>
                {showNewTask && (
                  <form onSubmit={handleCreateTask} style={styles.newTaskForm} className="fade-up">
                    <input
                      autoFocus
                      style={styles.taskInput}
                      placeholder="Task title…"
                      value={newTaskTitle}
                      onChange={(e) => setNewTaskTitle(e.target.value)}
                    />
                    <select
                      style={styles.prioritySelect}
                      value={newTaskPriority}
                      onChange={(e) => setNewTaskPriority(e.target.value)}
                    >
                      {['low', 'medium', 'high', 'urgent'].map((p) => (
                        <option key={p} value={p}>{p}</option>
                      ))}
                    </select>
                    <input
                      type="date"
                      style={styles.dateInput}
                      value={newTaskDueDate}
                      onChange={(e) => setNewTaskDueDate(e.target.value)}
                      title="Due date (optional)"
                    />
                    <button style={styles.primaryBtn} type="submit">Create</button>
                    <button style={styles.cancelBtn} type="button" onClick={() => { setShowNewTask(false); setNewTaskDueDate('') }}>Cancel</button>
                  </form>
                )}

                <div style={styles.kanban}>
                  {Object.entries(tasksByStatus).map(([status, statusTasks]) => (
                    <div key={status} style={styles.column}>
                      <div style={styles.columnHeader}>
                        <span style={{ ...styles.statusBadge, background: STATUS_COLORS[status].bg, color: STATUS_COLORS[status].text }}>
                          {STATUS_COLORS[status].label}
                        </span>
                        <span style={styles.columnCount}>{statusTasks.length}</span>
                      </div>
                      <div style={styles.columnTasks}>
                        {statusTasks.map((task) => (
                          <TaskCard
                            key={task.id}
                            task={task}
                            onStatusChange={handleStatusChange}
                            onDelete={handleDeleteTask}
                            onUpdate={handleUpdate}
                          />
                        ))}
                        {statusTasks.length === 0 && (
                          <div style={styles.emptyColumn}>—</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ── AI Tab ── */}
            {activeTab === 'ai' && (
              <div style={styles.tabContent}>
                {!suggestions ? (
                  <div style={styles.aiEmpty}>
                    <span style={styles.aiEmptyIcon}>✦</span>
                    <p style={styles.aiEmptyTitle}>No suggestions yet</p>
                    <p style={styles.aiEmptyText}>Click "AI Suggestions" to analyze your tasks with Claude.</p>
                    <button style={styles.primaryBtn} onClick={handleGetSuggestions} disabled={loadingAI}>
                      {loadingAI ? 'Analyzing…' : 'Analyze tasks'}
                    </button>
                  </div>
                ) : (
                  <div className="fade-up">
                    <div style={styles.aiSummaryCard}>
                      <p style={styles.aiSummaryLabel}>AI Summary</p>
                      <p style={styles.aiSummary}>{suggestions.summary}</p>
                    </div>

                    <div style={styles.aiGroups}>
                      {Object.entries(suggestions.groups || {}).map(([group, ids]) => (
                        ids.length > 0 && (
                          <div key={group} style={styles.aiGroup}>
                            <p style={styles.aiGroupLabel}>{group.replace('_', ' ')}</p>
                            {ids.map((id) => {
                              const task = tasks.find((t) => t.id === id)
                              return task ? (
                                <div key={id} style={styles.aiGroupTask}>{task.title}</div>
                              ) : null
                            })}
                          </div>
                        )
                      ))}
                    </div>

                    <div style={styles.suggestionList}>
                      {suggestions.suggestions?.map((s) => {
                        const task = tasks.find((t) => t.id === s.task_id)
                        return task ? (
                          <div key={s.task_id} style={styles.suggestionRow}>
                            <span style={styles.suggestionTitle}>{task.title}</span>
                            <span style={{ ...styles.suggestionPriority, color: PRIORITY_COLORS[s.suggested_priority] }}>
                              {PRIORITY_DOT[s.suggested_priority]} {s.suggested_priority}
                            </span>
                            <span style={styles.suggestionReason}>{s.reason}</span>
                          </div>
                        ) : null
                      })}
                    </div>

                    <button
                      style={{ ...styles.primaryBtn, marginTop: 24 }}
                      onClick={handleApplySuggestions}
                      disabled={loadingAI}
                    >
                      {loadingAI ? 'Applying…' : '✓ Apply all suggestions'}
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* ── Analytics Tab ── */}
            {activeTab === 'analytics' && (
              <div style={styles.tabContent}>
                <div style={styles.analyticsHeader}>
                  <span style={styles.analyticsTitle}>Overview</span>
                  <button
                    style={{ ...styles.refreshBtn, opacity: analyticsLoading ? 0.5 : 1 }}
                    onClick={refreshAnalytics}
                    disabled={analyticsLoading}
                  >
                    {analyticsLoading ? '↻ Refreshing…' : '↻ Refresh'}
                  </button>
                </div>

                {!analytics ? (
                  <div style={styles.aiEmpty}><p style={{ color: 'var(--text3)' }}>Loading analytics…</p></div>
                ) : (
                  <div className="fade-up">
                    <div style={styles.analyticsGrid}>
                      <StatCard label="Total Tasks" value={analytics.total_tasks} />
                      <StatCard label="Completion Rate" value={`${analytics.completion_rate_pct}%`} accent />
                      <StatCard label="Overdue" value={analytics.overdue_tasks} warn={analytics.overdue_tasks > 0} />
                      <StatCard label="Projects" value={analytics.project_count} />
                    </div>

                    <div style={styles.analyticsRow}>
                      <div style={styles.analyticsCard}>
                        <p style={styles.analyticsCardTitle}>By Status</p>
                        {Object.keys(STATUS_COLORS).map((s) => {
                          const n = analytics.by_status?.[s] || 0
                          return (
                            <div key={s} style={styles.barRow}>
                              <span style={{ ...styles.barLabel, color: STATUS_COLORS[s].text }}>
                                {STATUS_COLORS[s].label}
                              </span>
                              <div style={styles.barTrack}>
                                <div style={{
                                  ...styles.barFill,
                                  width: `${analytics.total_tasks ? (n / analytics.total_tasks) * 100 : 0}%`,
                                  background: STATUS_COLORS[s].text,
                                }} />
                              </div>
                              <span style={styles.barCount}>{n}</span>
                            </div>
                          )
                        })}
                      </div>

                      <div style={styles.analyticsCard}>
                        <p style={styles.analyticsCardTitle}>By Priority</p>
                        {Object.keys(PRIORITY_COLORS).map((p) => {
                          const n = analytics.by_priority?.[p] || 0
                          return (
                            <div key={p} style={styles.barRow}>
                              <span style={{ ...styles.barLabel, color: PRIORITY_COLORS[p] }}>
                                {PRIORITY_DOT[p]} {p}
                              </span>
                              <div style={styles.barTrack}>
                                <div style={{
                                  ...styles.barFill,
                                  width: `${analytics.total_tasks ? (n / analytics.total_tasks) * 100 : 0}%`,
                                  background: PRIORITY_COLORS[p],
                                }} />
                              </div>
                              <span style={styles.barCount}>{n}</span>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}

function TaskCard({ task, onStatusChange, onDelete, onUpdate }) {
  const [editingDue, setEditingDue] = useState(false)
  const [dueValue, setDueValue] = useState(
    task.due_date ? new Date(task.due_date).toISOString().split('T')[0] : ''
  )

  const now = new Date()
  const dueDate = task.due_date ? new Date(task.due_date) : null
  const isOverdue = dueDate && dueDate < now && task.status !== 'done' && task.status !== 'cancelled'
  const isDueSoon = dueDate && !isOverdue && (dueDate - now) < 86400000 * 2

  const handleDueChange = async (val) => {
    setDueValue(val)
    setEditingDue(false)
    const due_date = val ? new Date(val).toISOString() : null
    await onUpdate(task, { due_date })
  }

  return (
    <div style={{
      ...styles.taskCard,
      ...(isOverdue ? { borderColor: 'rgba(240,96,96,0.4)' } : {}),
      ...(isDueSoon ? { borderColor: 'rgba(239,159,39,0.4)' } : {}),
    }} className="fade-up">
      <div style={styles.taskCardTop}>
        <span style={{ ...styles.priorityTag, color: PRIORITY_COLORS[task.priority] }}>
          {PRIORITY_DOT[task.priority]} {task.priority}
        </span>
        <button style={styles.deleteTaskBtn} onClick={() => onDelete(task)}>✕</button>
      </div>

      <p style={styles.taskTitle}>{task.title}</p>

      <div style={styles.dueDateRow}>
        {editingDue ? (
          <input
            type="date"
            autoFocus
            style={styles.dueDateInput}
            value={dueValue}
            onChange={(e) => handleDueChange(e.target.value)}
            onBlur={() => setEditingDue(false)}
          />
        ) : (
          <button
            style={{
              ...styles.dueDateBtn,
              ...(isOverdue ? { color: '#f06060' } : {}),
              ...(isDueSoon ? { color: '#ef9f27' } : {}),
            }}
            onClick={() => setEditingDue(true)}
            title="Click to set due date"
          >
            {isOverdue && '⚠ '}
            {dueDate ? `Due ${dueDate.toLocaleDateString()}` : '+ Set due date'}
          </button>
        )}
      </div>

      <div style={styles.taskCardFooter}>
        <select
          style={styles.statusSelect}
          value={task.status}
          onChange={(e) => onStatusChange(task, e.target.value)}
        >
          {Object.entries(STATUS_COLORS).map(([s, c]) => (
            <option key={s} value={s}>{c.label}</option>
          ))}
        </select>
      </div>
    </div>
  )
}

function StatCard({ label, value, accent, warn }) {
  return (
    <div style={{
      ...styles.statCard,
      ...(accent ? { border: '1px solid rgba(200,240,78,0.25)', background: 'rgba(200,240,78,0.05)' } : {}),
      ...(warn ? { border: '1px solid rgba(240,96,96,0.25)' } : {}),
    }}>
      <p style={styles.statValue}>{value}</p>
      <p style={styles.statLabel}>{label}</p>
    </div>
  )
}

const styles = {
  layout: { display: 'flex', height: '100vh', overflow: 'hidden' },
  sidebar: { width: 240, flexShrink: 0, background: 'var(--bg2)', borderRight: '1px solid var(--border)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', padding: '24px 0', overflow: 'hidden' },
  sidebarTop: { display: 'flex', flexDirection: 'column', gap: 4, padding: '0 16px', overflow: 'auto' },
  logoRow: { display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 },
  dot: { width: 7, height: 7, borderRadius: '50%', background: 'var(--accent)', boxShadow: '0 0 8px var(--accent)', display: 'inline-block' },
  logoText: { fontFamily: 'var(--font-head)', fontWeight: 700, fontSize: '0.95rem', color: 'var(--text)' },
  userRow: { display: 'flex', alignItems: 'center', gap: 10, marginBottom: 24, padding: '10px 0', borderBottom: '1px solid var(--border)' },
  avatar: { width: 30, height: 30, borderRadius: '50%', background: 'rgba(200,240,78,0.15)', color: 'var(--accent)', fontFamily: 'var(--font-head)', fontWeight: 700, fontSize: '0.8rem', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 },
  userName: { fontSize: '0.82rem', fontWeight: 500, color: 'var(--text)' },
  userEmail: { fontSize: '0.72rem', color: 'var(--text3)', marginTop: 1 },
  sectionLabel: { fontSize: '0.68rem', color: 'var(--text3)', letterSpacing: '0.1em', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', margin: '8px 0 6px' },
  projectList: { display: 'flex', flexDirection: 'column', gap: 2 },
  projectItem: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', borderRadius: 8, cursor: 'pointer', transition: 'background 0.15s' },
  projectItemActive: { background: 'var(--surface2)' },
  projectName: { fontSize: '0.85rem', color: 'var(--text)', fontWeight: 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  deleteBtn: { fontSize: '0.7rem', color: 'var(--text3)', padding: 2, flexShrink: 0, opacity: 0.4 },
  inlineForm: { display: 'flex', gap: 6, marginTop: 8 },
  inlineInput: { flex: 1, background: 'var(--bg3)', border: '1px solid var(--border2)', borderRadius: 6, padding: '7px 10px', fontSize: '0.82rem', color: 'var(--text)', outline: 'none' },
  inlineSubmit: { background: 'var(--accent)', color: '#0a0a0f', fontWeight: 700, fontSize: '0.78rem', padding: '7px 12px', borderRadius: 6, border: 'none', cursor: 'pointer' },
  newProjectBtn: { marginTop: 8, background: 'none', border: '1px dashed var(--border2)', borderRadius: 8, padding: '8px 10px', fontSize: '0.82rem', color: 'var(--text3)', cursor: 'pointer', width: '100%', textAlign: 'left' },
  signOutBtn: { margin: '0 16px', background: 'none', border: '1px solid var(--border)', borderRadius: 8, padding: '9px', fontSize: '0.82rem', color: 'var(--text3)', cursor: 'pointer', width: 'calc(100% - 32px)' },
  main: { flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column', background: 'var(--bg)' },
  mainHeader: { display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', padding: '32px 36px 20px', borderBottom: '1px solid var(--border)', flexShrink: 0 },
  projectTitle: { fontFamily: 'var(--font-head)', fontWeight: 700, fontSize: '1.6rem', letterSpacing: '-0.03em', color: 'var(--text)' },
  taskCount: { fontSize: '0.8rem', color: 'var(--text3)', marginTop: 4, fontFamily: 'var(--font-mono)' },
  headerActions: { display: 'flex', gap: 10, alignItems: 'center' },
  aiBtn: { background: 'rgba(124,106,247,0.12)', color: '#a89af7', border: '1px solid rgba(124,106,247,0.3)', borderRadius: 8, padding: '9px 16px', fontSize: '0.85rem', fontFamily: 'var(--font-head)', fontWeight: 600, cursor: 'pointer', letterSpacing: '-0.01em' },
  primaryBtn: { background: 'var(--accent)', color: '#0a0a0f', border: 'none', borderRadius: 8, padding: '9px 18px', fontSize: '0.85rem', fontFamily: 'var(--font-head)', fontWeight: 700, cursor: 'pointer', letterSpacing: '-0.01em' },
  cancelBtn: { background: 'none', color: 'var(--text3)', border: '1px solid var(--border)', borderRadius: 8, padding: '9px 14px', fontSize: '0.85rem', cursor: 'pointer' },
  tabs: { display: 'flex', gap: 4, padding: '16px 36px 0', borderBottom: '1px solid var(--border)', flexShrink: 0 },
  tab: { padding: '9px 16px', fontSize: '0.83rem', color: 'var(--text3)', background: 'none', border: 'none', borderBottom: '2px solid transparent', cursor: 'pointer', fontFamily: 'var(--font-body)', fontWeight: 400, marginBottom: -1, transition: 'color 0.15s' },
  tabActive: { color: 'var(--text)', borderBottomColor: 'var(--accent)' },
  tabContent: { flex: 1, padding: '28px 36px', overflow: 'auto' },
  analyticsHeader: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 },
  analyticsTitle: { fontFamily: 'var(--font-head)', fontWeight: 600, fontSize: '1rem', color: 'var(--text)', letterSpacing: '-0.02em' },
  refreshBtn: { background: 'none', border: '1px solid var(--border2)', borderRadius: 6, padding: '6px 12px', fontSize: '0.78rem', color: 'var(--text2)', fontFamily: 'var(--font-mono)', cursor: 'pointer', transition: 'opacity 0.15s' },
  newTaskForm: { display: 'flex', gap: 10, marginBottom: 24, alignItems: 'center' },
  taskInput: { flex: 1, background: 'var(--surface)', border: '1px solid var(--border2)', borderRadius: 8, padding: '10px 14px', fontSize: '0.9rem', color: 'var(--text)', outline: 'none' },
  prioritySelect: { background: 'var(--surface)', border: '1px solid var(--border2)', borderRadius: 8, padding: '10px 12px', fontSize: '0.85rem', color: 'var(--text)', outline: 'none' },
  dateInput: { background: 'var(--surface)', border: '1px solid var(--border2)', borderRadius: 8, padding: '10px 10px', fontSize: '0.82rem', color: 'var(--text2)', outline: 'none', colorScheme: 'dark' },
  kanban: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 },
  column: { display: 'flex', flexDirection: 'column', gap: 8 },
  columnHeader: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 },
  statusBadge: { fontSize: '0.75rem', fontFamily: 'var(--font-mono)', padding: '3px 10px', borderRadius: 20, fontWeight: 500 },
  columnCount: { fontSize: '0.72rem', color: 'var(--text3)', fontFamily: 'var(--font-mono)' },
  columnTasks: { display: 'flex', flexDirection: 'column', gap: 8 },
  emptyColumn: { textAlign: 'center', color: 'var(--text3)', fontSize: '0.8rem', padding: '16px 0' },
  taskCard: { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 10, padding: '14px', display: 'flex', flexDirection: 'column', gap: 8, transition: 'border-color 0.15s' },
  taskCardTop: { display: 'flex', alignItems: 'center', justifyContent: 'space-between' },
  priorityTag: { fontSize: '0.72rem', fontFamily: 'var(--font-mono)', fontWeight: 500, letterSpacing: '0.03em' },
  deleteTaskBtn: { fontSize: '0.7rem', color: 'var(--text3)', padding: 2, opacity: 0.4 },
  taskTitle: { fontSize: '0.875rem', color: 'var(--text)', fontWeight: 400, lineHeight: 1.4 },
  dueDateRow: { minHeight: 20 },
  dueDateBtn: { background: 'none', border: 'none', padding: 0, fontSize: '0.72rem', color: 'var(--text3)', fontFamily: 'var(--font-mono)', cursor: 'pointer', textAlign: 'left', transition: 'color 0.15s' },
  dueDateInput: { width: '100%', background: 'var(--bg2)', border: '1px solid var(--border2)', borderRadius: 6, padding: '4px 8px', fontSize: '0.75rem', color: 'var(--text)', outline: 'none', colorScheme: 'dark' },
  taskCardFooter: { marginTop: 4 },
  statusSelect: { width: '100%', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 6, padding: '5px 8px', fontSize: '0.75rem', color: 'var(--text2)', outline: 'none', cursor: 'pointer' },
  aiEmpty: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12, padding: '80px 0', textAlign: 'center' },
  aiEmptyIcon: { fontSize: '2rem', color: 'var(--accent2)' },
  aiEmptyTitle: { fontFamily: 'var(--font-head)', fontWeight: 600, fontSize: '1.1rem', color: 'var(--text)' },
  aiEmptyText: { fontSize: '0.875rem', color: 'var(--text2)', maxWidth: 300 },
  aiSummaryCard: { background: 'rgba(124,106,247,0.08)', border: '1px solid rgba(124,106,247,0.2)', borderRadius: 12, padding: '20px 24px', marginBottom: 24 },
  aiSummaryLabel: { fontSize: '0.72rem', color: '#a89af7', fontFamily: 'var(--font-mono)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 8 },
  aiSummary: { fontSize: '0.9rem', color: 'var(--text)', lineHeight: 1.6, fontWeight: 300 },
  aiGroups: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginBottom: 24 },
  aiGroup: { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 10, padding: '14px' },
  aiGroupLabel: { fontSize: '0.72rem', color: 'var(--accent)', fontFamily: 'var(--font-mono)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 10 },
  aiGroupTask: { fontSize: '0.82rem', color: 'var(--text2)', padding: '5px 0', borderBottom: '1px solid var(--border)', fontWeight: 300 },
  suggestionList: { display: 'flex', flexDirection: 'column', gap: 8 },
  suggestionRow: { display: 'grid', gridTemplateColumns: '1fr auto 1fr', alignItems: 'center', gap: 16, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '12px 16px' },
  suggestionTitle: { fontSize: '0.875rem', color: 'var(--text)', fontWeight: 400 },
  suggestionPriority: { fontSize: '0.75rem', fontFamily: 'var(--font-mono)', fontWeight: 600, textAlign: 'center' },
  suggestionReason: { fontSize: '0.78rem', color: 'var(--text3)', textAlign: 'right' },
  analyticsGrid: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 },
  statCard: { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: '20px', textAlign: 'center' },
  statValue: { fontFamily: 'var(--font-head)', fontWeight: 700, fontSize: '1.8rem', letterSpacing: '-0.03em', color: 'var(--text)' },
  statLabel: { fontSize: '0.78rem', color: 'var(--text3)', fontFamily: 'var(--font-mono)', marginTop: 6, letterSpacing: '0.04em' },
  analyticsRow: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 },
  analyticsCard: { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: '20px 24px' },
  analyticsCardTitle: { fontFamily: 'var(--font-head)', fontWeight: 600, fontSize: '0.9rem', color: 'var(--text)', marginBottom: 16, letterSpacing: '-0.01em' },
  barRow: { display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 },
  barLabel: { fontSize: '0.75rem', fontFamily: 'var(--font-mono)', width: 80, flexShrink: 0 },
  barTrack: { flex: 1, height: 4, background: 'var(--surface2)', borderRadius: 4, overflow: 'hidden' },
  barFill: { height: '100%', borderRadius: 4, transition: 'width 0.5s ease' },
  barCount: { fontSize: '0.72rem', color: 'var(--text3)', fontFamily: 'var(--font-mono)', width: 20, textAlign: 'right' },
  empty: { flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 8 },
  emptyTitle: { fontFamily: 'var(--font-head)', fontWeight: 600, fontSize: '1.2rem', color: 'var(--text)' },
  emptyText: { fontSize: '0.875rem', color: 'var(--text3)' },
}
