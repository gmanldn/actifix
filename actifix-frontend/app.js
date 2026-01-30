/**
 * Actifix Dashboard - COMPACT & ELEGANT 2026 Edition
 * 
 * Redesigned for maximum information density with modern aesthetics
 */

const { useState, useEffect, useRef, createElement: h } = React;

// API Configuration
// Dynamically construct API_BASE using window.location to match the frontend port
const API_BASE = `${window.location.protocol}//${window.location.hostname}:5001/api`;
const UI_VERSION = '8.0.36';
const REFRESH_INTERVAL = 5000;
const LOG_REFRESH_INTERVAL = 3000;
const TICKET_REFRESH_INTERVAL = 4000;
const TICKET_LIMIT = 250;

const ADMIN_PASSWORD_KEY = 'actifix_admin_password';
const getAdminPassword = () => localStorage.getItem(ADMIN_PASSWORD_KEY) || '';
const setAdminPasswordInStorage = (value) => {
  if (!value) {
    localStorage.removeItem(ADMIN_PASSWORD_KEY);
  } else {
    localStorage.setItem(ADMIN_PASSWORD_KEY, value);
  }
};
const clearAuthToken = () => setAdminPasswordInStorage('');
const isAuthenticated = () => !!getAdminPassword();

const ONBOARDING_STORAGE_KEY = 'actifix_onboarding_v1';
const hasCompletedOnboarding = () => localStorage.getItem(ONBOARDING_STORAGE_KEY) === '1';
const markOnboardingCompleted = () => localStorage.setItem(ONBOARDING_STORAGE_KEY, '1');

const buildAdminHeaders = (initial = {}) => {
  const headers = { ...initial };
  const adminPassword = getAdminPassword();
  if (adminPassword) {
    headers['X-Admin-Password'] = adminPassword;
  }
  return headers;
};

const applyAssetVersion = () => {
  const version = window.ACTIFIX_ASSET_VERSION || '4';
  const link = document.querySelector('link[rel="stylesheet"]');
  if (!link) return;
  const href = link.getAttribute('href') || '';
  if (!href.includes(`v=${version}`)) {
    const nextHref = href.split('?')[0] + `?v=${version}`;
    link.setAttribute('href', nextHref);
  }
};

applyAssetVersion();

// ============================================================================
// Utility Functions
// ============================================================================

const formatTime = (isoString) => {
  if (!isoString) return 'N/A';
  const date = new Date(isoString);
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
};

const formatRelativeTime = (isoString) => {
  if (!isoString) return 'N/A';
  const date = new Date(isoString);
  const now = new Date();
  const diff = now - date;
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  if (minutes > 0) return `${minutes}m ago`;
  return `${seconds}s ago`;
};

const getPriorityColor = (priority) => {
  const colors = {
    'P0': '#ef4444',
    'P1': '#f59e0b',
    'P2': '#eab308',
    'P3': '#10b981',
    'P4': '#6b7280',
  };
  return colors[priority] || '#6b7280';
};

const getStatusColor = (status) => {
  const colors = {
    'OK': '#10b981',
    'WARNING': '#f59e0b',
    'ERROR': '#ef4444',
    'SLA_BREACH': '#ef4444',
  };
  return colors[status] || '#6b7280';
};

const PRIORITY_ORDER = ['P0', 'P1', 'P2', 'P3', 'P4'];
const PRIORITY_LABELS = {
  P0: 'Critical',
  P1: 'High',
  P2: 'Medium',
  P3: 'Low',
  P4: 'Deferred',
};

const SLA_HOURS = {
  'P0': 1,
  'P1': 4,
  'P2': 24,
  'P3': 72,
  'P4': 168, // 1 week
};

const normalizePriority = (priority) => (
  PRIORITY_ORDER.includes(priority) ? priority : 'P4'
);

const getSlaStatus = (created, priority) => {
  const createdAt = created ? new Date(created) : null;
  if (!createdAt || Number.isNaN(createdAt.getTime())) {
    return null;
  }
  const ageHours = (Date.now() - createdAt.getTime()) / 3600000;
  const slaHours = SLA_HOURS[priority] || 168;
  const remainingHours = Math.max(0, slaHours - ageHours);
  const overdueHours = Math.max(0, ageHours - slaHours);
  const isOverdue = overdueHours > 0;
  return {
    ageHours,
    slaHours,
    remainingHours,
    overdueHours,
    isOverdue,
  };
};

const groupTicketsByPriority = (tickets) => {
  const grouped = {};
  PRIORITY_ORDER.forEach((priority) => {
    grouped[priority] = { open: [], completed: [] };
  });

  tickets.forEach((ticket) => {
    const priority = normalizePriority(ticket.priority);
    const bucket = ticket.status === 'completed' ? 'completed' : 'open';
    grouped[priority][bucket].push(ticket);
  });

  return grouped;
};

// ============================================================================
// Custom Hooks
// ============================================================================

const useFetch = (endpoint, interval = REFRESH_INTERVAL) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    const fetchData = async (retryCount = 0, maxRetries = 3) => {
      try {
        const headers = buildAdminHeaders();
        const response = await fetch(`${API_BASE}${endpoint}`, { cache: 'no-store', headers });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const text = await response.text();
        try {
          const json = JSON.parse(text);
          setData(json);
          setError(null);
          setLastUpdated(new Date());
          return; // Success, no retry
        } catch (parseErr) {
          // Response is not JSON, likely an error page
          throw new Error(`Invalid response from ${endpoint}: expected JSON`);
        }
      } catch (err) {
        // Detect network errors
        let errorMsg = err.message;
        if (err.name === 'TypeError' && (errorMsg.includes('fetch') || errorMsg.includes('Failed to fetch'))) {
          errorMsg = 'Backend offline - API server not responding on port 5001. Run "python scripts/bounce.py" or "python scripts/start.py" to restart.';
        } else if (retryCount < maxRetries) {
          // Retry on network errors
          const delay = Math.pow(2, retryCount) * 1000; // Exponential backoff
          setTimeout(() => fetchData(retryCount + 1, maxRetries), delay);
          return;
        }
        setError(errorMsg);
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const timer = setInterval(() => fetchData(0), interval);
    return () => clearInterval(timer);
  }, [endpoint, interval]);

  return { data, loading, error, lastUpdated };
};

// Custom hook for authenticated POST requests
const useAuthenticatedFetch = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const execute = async (endpoint, options = {}) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const headers = buildAdminHeaders({
        'Content-Type': 'application/json',
        ...options.headers
      });

      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: options.method || 'POST',
        headers,
        body: options.body ? JSON.stringify(options.body) : undefined,
        ...options
      });

      const text = await response.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        throw new Error(`Invalid response from ${endpoint}: expected JSON`);
      }

      if (!response.ok) {
        throw new Error(data.error || `HTTP ${response.status}`);
      }

      setResult(data);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { execute, loading, error, result };
};

const postJSON = async (endpoint, payload) => {
  const headers = buildAdminHeaders({ 'Content-Type': 'application/json' });
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });
  const text = await response.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error(`Invalid response from ${endpoint}: expected JSON, got HTML or error page`);
  }
  if (!response.ok) {
    throw new Error(data.message || data.error || `HTTP ${response.status}`);
  }
  return data;
};

const useEventStream = (endpoint) => {
  const [updates, setUpdates] = useState([]);
  const [latest, setLatest] = useState(null);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const source = new EventSource(`${API_BASE}${endpoint}`);
    source.addEventListener('update', (event) => {
      try {
        const payload = JSON.parse(event.data);
        setLatest(payload);
        setUpdates((prev) => [...prev.slice(-5), payload]);
      } catch (err) {
        console.error('Invalid SSE payload', err);
      }
    });
    source.addEventListener('status', (event) => {
      try {
        const payload = JSON.parse(event.data);
        setStatus(payload);
      } catch (err) {
        console.error('Invalid SSE status', err);
      }
    });
    source.onerror = () => {
      setError('Detection stream disconnected.');
      source.close();
    };
    return () => source.close();
  }, [endpoint]);

  return { updates, latest, status, error };
};

// ============================================================================
// Components
// ============================================================================

const LoadingSpinner = () => {
  return h('div', { className: 'loading-spinner' },
    h('div', { className: 'spinner' })
  );
};

const ErrorDisplay = ({ message }) => {
  return h('div', { className: 'error-display' },
    h('span', { className: 'error-icon' }, '⚠'),
    h('span', null, message)
  );
};

// Navigation Rail Component
const NavigationRail = ({ activeView, onViewChange, logAlert }) => {
const navItems = [
  { id: 'overview', icon: '📊', label: 'Overview' },
  { id: 'tickets', icon: '🎫', label: 'Tickets' },
  { id: 'quiz', icon: '🎯', label: 'Quiz' },
  { id: 'logs', icon: '📜', label: 'Logs' },
  { id: 'system', icon: 'S', label: 'System' },
  { id: 'modules', icon: '🧩', label: 'Modules' },
  { id: 'ideas', icon: '💡', label: 'Ideas' },
  { id: 'settings', icon: '⚙️', label: 'Settings' },
];

  return h('nav', { className: 'nav-rail' },
    h('img', { src: './assets/pangolin.svg', alt: 'Actifix', className: 'nav-rail-logo' }),
    h('div', { className: 'nav-rail-items' },
      navItems.map(item =>
        h('button', {
          key: item.id,
          className: [
            'nav-rail-item',
            activeView === item.id ? 'active' : '',
            item.id === 'logs' && logAlert ? 'flash' : '',
            item.id === 'system' ? 'system-item' : '',
          ].join(' ').trim(),
          onClick: () => onViewChange(item.id),
          title: item.label
        }, item.icon)
      )
    )
  );
};

const VersionBadge = () => {
const [prevVersion, setPrevVersion] = useState(null);
const firstVersionCheck = useRef(true);
const { data, loading } = useFetch('/version', REFRESH_INTERVAL);
  // Always display the UI build version; use the API version for mismatch + reload detection.
  const apiVersion = data?.version || '—';
  const versionMismatch = apiVersion !== '—' && apiVersion !== UI_VERSION;

  useEffect(() => {
    if (loading) return;
    if (firstVersionCheck.current) {
      firstVersionCheck.current = false;
      setPrevVersion(apiVersion);
      return;
    }
    if (apiVersion !== prevVersion) {
      console.log(`Detected version change ${prevVersion} -> ${apiVersion}; reloading page.`);
      window.location.reload();
      setPrevVersion(apiVersion);
    }
  }, [apiVersion, loading]);

  const gitChecked = data?.git_checked ?? false;
  const clean = data?.clean ?? false;
  const branchLabel = data?.branch ? `branch ${data.branch}` : 'branch unknown';
  const statusLabel = loading
    ? 'Checking git…'
    : gitChecked
      ? clean
        ? 'Git clean'
        : 'Git dirty'
      : 'Git unchecked';
  const accentColor = gitChecked && clean ? '#2ee6b8' : '#ff5f5f';

  return h('span', {
    className: 'version-indicator',
    title: versionMismatch ? `UI version (${UI_VERSION}) does not match API version (${apiVersion}). Reload recommended.` : '',
    style: {
      backgroundColor: versionMismatch ? '#ef4444' : 'var(--accent)',
      borderColor: '#000',
      color: versionMismatch ? '#fff' : '#000',
    }
  },
    h('span', { className: 'version-label' }, `v${UI_VERSION}`),
    h('span', { className: 'version-sub' }, `${statusLabel} • ${branchLabel}`)
  );
};

const FixToolbar = ({ onFix, isFixing, status }) => {
  const label = status || 'Ready to fix the next ticket';
  return h('div', { className: 'fix-toolbar' },
    h('button', {
      type: 'button',
      className: `btn fix-button ${isFixing ? 'working' : ''}`,
      onClick: () => onFix?.(),
      disabled: isFixing,
    },
      h('span', null, isFixing ? 'Fixing ticket…' : 'Fix highest priority ticket'),
      h('span', { className: 'fix-button-sub' }, isFixing ? 'Ultrathink engaged' : 'Ready')
    ),
    h('span', { className: 'fix-status' }, label)
  );
};

// Header Component
const Header = ({ onFix, isFixing, fixStatus, theme, onToggleTheme, onLogout, onOpenOnboarding }) => {
  const [connected, setConnected] = useState(false);
  const [time, setTime] = useState(new Date().toLocaleTimeString());
  const { data: health } = useFetch('/health', REFRESH_INTERVAL);
  // Search query for the dashboard.
  const [search, setSearch] = useState('');
  const handleSearchChange = (e) => setSearch(e.target.value);

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const headers = buildAdminHeaders();
        
        const response = await fetch(`${API_BASE}/ping`, { headers });
        setConnected(response.ok);
      } catch {
        setConnected(false);
      }
    };

    checkConnection();
    const timer = setInterval(checkConnection, 10000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return h('header', { className: 'dashboard-header' },
    h('div', { className: 'header-left' },
      h('img', { src: './assets/pangolin.svg', alt: 'Actifix', className: 'header-logo' }),
      h('div', { className: 'header-title' },
        h('h1', null, 'ACTIFIX'),
        h('span', { className: 'header-subtitle' }, 'Live Error Intelligence')
      )
    ),
    h('div', { className: 'header-right' },
      h('input', { type: 'text', className: 'header-search', placeholder: 'Search…', value: search, onChange: handleSearchChange }),
      h('div', { className: 'header-stats' },
        h('div', { className: 'stat-card', style: { padding: '6px 14px', minWidth: '70px' } },
          h('div', { className: 'stat-value', style: { fontSize: '18px', fontWeight: '700' } }, health?.metrics?.open_tickets ?? '—'),
          h('div', { className: 'stat-label', style: { fontSize: '10px', fontWeight: '600', letterSpacing: '0.05em' } }, 'OPEN')
        ),
        h('div', { className: 'stat-card', style: { padding: '6px 14px', minWidth: '70px' } },
          h('div', { className: 'stat-value', style: { fontSize: '18px', fontWeight: '700' } }, health?.metrics?.completed_tickets ?? '—'),
          h('div', { className: 'stat-label', style: { fontSize: '10px', fontWeight: '600', letterSpacing: '0.05em' } }, 'DONE')
        ),
        h('div', { className: `connection-status ${connected ? 'connected' : 'disconnected'}` },
          h('span', { className: 'connection-dot' }),
          h('span', null, connected ? 'API ' : 'OFF')
        )
      ),
      h(FixToolbar, { onFix, isFixing, status: fixStatus }),
      h(VersionBadge),
      h('button', {
        onClick: onOpenOnboarding,
        title: 'Open onboarding walkthrough',
        className: 'theme-toggle-btn',
        style: {
          background: 'transparent',
          border: '1px solid var(--border)',
          borderRadius: '999px',
          padding: '4px 8px',
          fontSize: '16px',
          cursor: 'pointer',
          color: 'var(--text-primary)'
        }
      }, '❓'),
      h('button', {
        onClick: onToggleTheme,
        title: `Switch to ${theme === 'dark' ? 'Portal light' : theme === 'portal' ? 'Azure light' : 'Dark'} theme`,
        className: 'theme-toggle-btn',
        style: {
          background: 'transparent',
          border: '1px solid var(--border)',
          borderRadius: '999px',
          padding: '4px 8px',
          fontSize: '16px',
          cursor: 'pointer',
          color: 'var(--text-primary)'
        }
      }, theme === 'dark' ? '☀️' : '🌙'),
      h('button', {
        onClick: onLogout,
        title: 'Logout',
        className: 'theme-toggle-btn',
        style: {
          background: 'transparent',
          border: '1px solid var(--border)',
          borderRadius: '999px',
          padding: '4px 8px',
          fontSize: '16px',
          cursor: 'pointer',
          color: 'var(--text-primary)'
        }
      }, '🚪'),
      h('span', { className: 'header-time' }, time)
    )
  );
};

// Footer Component
const Footer = () => {
  return h('footer', { className: 'dashboard-footer' },
    h('span', null, '© 2026 Actifix - Compact Dashboard'),
    h('span', null, `Last updated: ${new Date().toLocaleTimeString()}`)
  );
};

// Metric Tile Component
const MetricTile = ({ label, value, subvalue, icon, color, trend }) => {
  return h('div', { className: 'metric-tile' },
    h('div', { className: 'metric-tile-header' },
      h('span', { className: 'metric-tile-label' }, label),
      icon && h('span', { className: 'metric-tile-icon' }, icon)
    ),
    h('div', { className: 'metric-tile-value', style: color ? { color } : {} }, value),
    subvalue && h('div', { className: 'metric-tile-subvalue' }, subvalue),
    trend && h('div', { className: 'metric-tile-tag' }, trend)
  );
};

const PokerToolPanel = () => {
  const { data: detectStatus } = useFetch('/modules/pokertool/api/detect/status', 6000);
  const { updates, latest, status: streamStatus, error: streamError } = useEventStream('/modules/pokertool/api/detect/stream');

  const [nashPayload, setNashPayload] = useState({ hand: 'Ah,Kd', board: 'Qs, Jh, 10d' });
  const [nashResult, setNashResult] = useState(null);
  const [nashLoading, setNashLoading] = useState(false);
  const [nashError, setNashError] = useState('');

  const [icmPayload, setIcmPayload] = useState({ stacks: '100,50', payouts: '5,2.5' });
  const [icmResult, setIcmResult] = useState(null);
  const [icmError, setIcmError] = useState('');

  const [mlPayload, setMlPayload] = useState({ history: '[{"action":"raise","aggression":0.9}]', scores: '0.3,0.65,0.82' });
  const [mlResult, setMlResult] = useState(null);
  const [mlError, setMlError] = useState('');

  const callNash = async () => {
    setNashError('');
    setNashLoading(true);
    try {
      const hand = nashPayload.hand.split(',').map((h) => h.trim()).filter(Boolean);
      const board = nashPayload.board.split(',').map((h) => h.trim()).filter(Boolean);
      const data = await postJSON('/modules/pokertool/api/solvers/nash', { hand, board });
      setNashResult(data);
    } catch (err) {
      setNashError(err.message);
    } finally {
      setNashLoading(false);
    }
  };

  const callIcm = async () => {
    setIcmError('');
    try {
      const stacks = icmPayload.stacks.split(',').map((value) => parseFloat(value.trim())).filter(Boolean);
      const payouts = icmPayload.payouts.split(',').map((value) => parseFloat(value.trim())).filter(Boolean);
      const data = await postJSON('/modules/pokertool/api/solvers/icm', { stacks, payouts });
      setIcmResult(data);
    } catch (err) {
      setIcmError(err.message);
    }
  };

  const callMl = async (type) => {
    setMlError('');
    try {
      if (type === 'opponent') {
        const history = JSON.parse(mlPayload.history);
        const data = await postJSON('/modules/pokertool/api/ml/opponent', { history });
        setMlResult(data);
      } else {
        const scores = mlPayload.scores.split(',').map((value) => parseFloat(value.trim())).filter((value) => !Number.isNaN(value));
        const data = await postJSON('/modules/pokertool/api/ml/learn', { scores });
        setMlResult(data);
      }
    } catch (err) {
      setMlError(err.message);
    }
  };

  const detectionSummary = detectStatus || {};
  const latestEvent = latest || {};

  return h('div', { className: 'panel pokertool-panel' },
    h('div', { className: 'panel-header' },
      h('div', { className: 'panel-title' },
        h('span', { className: 'panel-title-icon' }, '🃏'),
        'PokerTool Insights'
      ),
      h('div', { className: 'panel-actions' },
        streamError && h('span', { className: 'text-dim' }, streamError),
        streamStatus && h('span', { className: 'poker-tag' }, streamStatus.active ? 'Streaming' : 'Idle')
      )
    ),
    h('div', { className: 'poker-section detection' },
      h('div', { className: 'poker-subheader' }, 'Detection'),
      h('div', { className: 'poker-detection-row' },
        h('div', { className: 'poker-detection-card' },
          h('strong', null, 'Host'),
          h('span', null, detectionSummary.host || '—'),
          h('small', null, 'Port: ', detectionSummary.port || '—')
        ),
        h('div', { className: 'poker-detection-card' },
          h('strong', null, 'Latest Action'),
          h('span', null, latestEvent.table_state?.action || 'N/A'),
          h('small', null, 'Confidence:', latestEvent.confidence ?? '—')
        ),
        h('div', { className: 'poker-detection-card' },
          h('strong', null, 'Board'),
          h('span', null, (latestEvent.table_state?.board || []).join(', ') || '—'),
          h('small', null, `${streamStatus?.history_count ?? 0} snapshots`)
        )
      ),
      h('div', { className: 'poker-detection-stream' },
        updates.map((event, idx) =>
          h('div', { key: `det-${idx}`, className: 'poker-detection-item' },
            h('div', { className: 'poker-detection-item-header' },
              h('span', null, `#${event.sequence}`),
              h('span', null, formatTime(new Date(event.timestamp).toISOString()))
            ),
            h('div', null, event.table_state?.action || 'update'),
            h('small', null, `Confidence: ${event.confidence ?? 0}`)
          )
        )
      )
    ),
    h('div', { className: 'poker-section solvers' },
      h('div', { className: 'poker-subheader' }, 'Solvers'),
      h('div', { className: 'poker-solver-grid' },
        h('div', { className: 'poker-solver-card' },
          h('label', null, 'Hand'),
          h('input', {
            className: 'poker-input',
            value: nashPayload.hand,
            onChange: (e) => setNashPayload({ ...nashPayload, hand: e.target.value }),
          }),
          h('label', null, 'Board'),
          h('input', {
            className: 'poker-input',
            value: nashPayload.board,
            onChange: (e) => setNashPayload({ ...nashPayload, board: e.target.value }),
          }),
          h('button', { className: 'btn btn-small', onClick: callNash, disabled: nashLoading },
            nashLoading ? 'Computing…' : 'Run Nash'
          ),
          nashError && h('span', { className: 'poker-error' }, nashError),
          nashResult && h('p', { className: 'poker-result' }, `Action: ${nashResult.recommendation?.action}`)
        ),
        h('div', { className: 'poker-solver-card' },
          h('label', null, 'Stacks'),
          h('input', {
            className: 'poker-input',
            value: icmPayload.stacks,
            onChange: (e) => setIcmPayload({ ...icmPayload, stacks: e.target.value }),
          }),
          h('label', null, 'Payouts'),
          h('input', {
            className: 'poker-input',
            value: icmPayload.payouts,
            onChange: (e) => setIcmPayload({ ...icmPayload, payouts: e.target.value }),
          }),
          h('button', { className: 'btn btn-small', onClick: callIcm }, 'Run ICM'),
          icmError && h('span', { className: 'poker-error' }, icmError),
          icmResult && h('p', { className: 'poker-result' }, `Value: ${icmResult.icm_value}`)
        )
      )
    ),
    h('div', { className: 'poker-section ml' },
      h('div', { className: 'poker-subheader' }, 'ML Insights'),
      h('div', { className: 'poker-ml-grid' },
        h('div', { className: 'poker-ml-card' },
          h('label', null, 'History (JSON)'),
          h('textarea', {
            className: 'poker-input',
            value: mlPayload.history,
            onChange: (e) => setMlPayload({ ...mlPayload, history: e.target.value }),
            rows: 3,
          }),
          h('button', { className: 'btn btn-small', onClick: () => callMl('opponent') }, 'Opponent Model')
        ),
        h('div', { className: 'poker-ml-card' },
          h('label', null, 'Score Stream'),
          h('input', {
            className: 'poker-input',
            value: mlPayload.scores,
            onChange: (e) => setMlPayload({ ...mlPayload, scores: e.target.value }),
          }),
          h('button', { className: 'btn btn-small', onClick: () => callMl('learn') }, 'Active Learning')
        )
      ),
      mlError && h('span', { className: 'poker-error' }, mlError),
      mlResult && h('p', { className: 'poker-result' }, mlResult.message || 'ML response received')
    )
  );
};

// Overview View Component
const OverviewView = () => {
  const { data: health, loading: hLoading, error: hError } = useFetch('/health');
  const { data: system, loading: sLoading, error: sError } = useFetch('/system');
  const { data: tickets, loading: tLoading, error: tError } = useFetch('/tickets');

  if (hLoading || sLoading) return h(LoadingSpinner);
  if (hError || sError) return h(ErrorDisplay, { message: hError || sError });

  const metrics = health?.metrics || {};
  const status = health?.status || 'UNKNOWN';

  return h('div', null,
    // Stats Grid
    h('div', { className: 'stats-grid' },
      h(MetricTile, {
        label: 'STATUS',
        value: status,
        icon: '📡',
        color: getStatusColor(status),
        subvalue: health?.healthy ? 'All Systems Go' : 'Issues Detected'
      }),
      h(MetricTile, {
        label: 'OPEN TICKETS',
        value: metrics.open_tickets ?? 0,
        icon: '🎫',
        color: metrics.open_tickets > 0 ? '#f59e0b' : '#10b981',
        subvalue: `${metrics.completed_tickets ?? 0} completed`
      }),
      h(MetricTile, {
        label: 'OLDEST TICKET',
        value: `${metrics.oldest_ticket_age_hours ?? 0}h`,
        icon: '⏱️',
        subvalue: 'ticket age'
      }),
      h(MetricTile, {
        label: 'UPTIME',
        value: system?.server?.uptime?.split(' ')[0] || 'N/A',
        icon: '⏰',
        subvalue: system?.server?.uptime || 'N/A'
      }),
      h(MetricTile, {
        label: 'MEMORY',
        value: system?.resources?.memory ? `${system.resources.memory.percent}%` : 'N/A',
        icon: '💾',
        color: system?.resources?.memory?.percent > 80 ? '#ef4444' : '#10b981',
        subvalue: system?.resources?.memory ? `${system.resources.memory.used_gb}/${system.resources.memory.total_gb} GB` : 'N/A'
      }),
      h(MetricTile, {
        label: 'CPU',
        value: system?.resources?.cpu_percent !== null ? `${system.resources.cpu_percent}%` : 'N/A',
        icon: '🔥',
        color: system?.resources?.cpu_percent > 80 ? '#ef4444' : '#10b981'
      }),
      h(MetricTile, {
        label: 'PLATFORM',
        value: system?.platform?.system || 'N/A',
        icon: '🖥️',
        subvalue: system?.platform?.release || ''
      })
    ),

    h(RecentActivityPanel),

    // Recent Tickets Panel
    h('div', { className: 'panel' },
      h('div', { className: 'panel-header' },
        h('div', { className: 'panel-title' },
          h('span', { className: 'panel-title-icon' }, '🎫'),
          'RECENT TICKETS'
        ),
        h('div', { className: 'panel-actions' },
          h('span', { className: 'text-muted', style: { fontSize: '11px' } },
            `${metrics.open_tickets ?? 0} open • ${metrics.completed_tickets ?? 0} done`
          )
        )
      ),
        tickets.tickets.slice(0, 15).map((ticket, i) => {
          const priority = normalizePriority(ticket.priority);
          return h('div', { key: ticket.ticket_id || i, className: 'ticket-item' },
            h('div', { className: 'ticket-item-header' },
              h('span', {
                className: `priority-badge ${priority.toLowerCase()}`
              }, priority),
              h('span', {
                className: `status-badge ${ticket.status}`
              }, ticket.status),
              h('span', { className: 'ticket-id' }, ticket.ticket_id?.slice(0, 12) || 'N/A'),
              h('span', { className: 'text-dim', style: { fontSize: '10px', marginLeft: 'auto' } },
                formatRelativeTime(ticket.created)
              )
            ),
            h('div', { className: 'ticket-type' }, ticket.error_type || 'Unknown'),
            h('div', { className: 'ticket-message' }, ticket.message || ''),
            h('div', { className: 'ticket-meta' },
              h('span', null, '📁 ', ticket.source || 'unknown')
            )
          );
        })
      ) : h('div', { style: { padding: '24px', textAlign: 'center', color: 'var(--text-dim)' } }, 'No tickets found')
    )
  );
};

// Tickets View Component
const TicketsView = () => {
  const { data, loading, error, lastUpdated } = useFetch(`/tickets?limit=${TICKET_LIMIT}`, TICKET_REFRESH_INTERVAL);
  const { execute: authenticatedFetch, loading: authLoading, error: authError } = useAuthenticatedFetch();

  const [selectedTicket, setSelectedTicket] = useState(null);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTickets, setSelectedTickets] = useState(new Set());
  const [savedViews, setSavedViews] = useState([]);
  const SAVED_VIEWS_KEY = 'actifix_saved_views_v1';

  useEffect(() => {
    const saved = localStorage.getItem(SAVED_VIEWS_KEY);
    if (saved) setSavedViews(JSON.parse(saved));
  }, []);


  const fetchTicket = async (ticketId) => {
    if (!ticketId) return;
    setSelectedTicket(null);
    setModalLoading(true);
    setModalError('');
    try {
      const headers = buildAdminHeaders();
      const response = await fetch(`${API_BASE}/ticket/${ticketId}`, { headers });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const ticketData = await response.json();
      setSelectedTicket(ticketData);
    } catch (err) {
      setModalError(err.message);
    } finally {
      setModalLoading(false);
    }
  };

  const closeModal = () => setSelectedTicket(null);

  if (loading) return h(LoadingSpinner);
  if (error) return h(ErrorDisplay, { message: error });

  const tickets = data?.tickets || [];
  const searchTermNormalized = searchTerm.trim().toLowerCase();
  const filteredTickets = tickets.filter((ticket) => {
    const tokenPriority = normalizePriority(ticket.priority);
    if (priorityFilter !== 'All' && tokenPriority !== priorityFilter) {
      return false;
    }
    if (statusFilter !== 'all' && ticket.status !== statusFilter) {
      return false;
    }
    if (searchTermNormalized) {
      const haystack = `${ticket.ticket_id || ''} ${ticket.error_type || ''} ${ticket.message || ''}`.toLowerCase();
      if (!haystack.includes(searchTermNormalized)) {
        return false;
      }
    }
    return true;
  });
  const groupedTickets = groupTicketsByPriority(filteredTickets);
  const updatedLabel = lastUpdated
    ? lastUpdated.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : '—';
  const priorityOptions = ['All', 'P0', 'P1', 'P2', 'P3', 'P4'];
  const statusOptions = [
    { key: 'all', label: 'All' },
    { key: 'open', label: 'Open' },
    { key: 'completed', label: 'Completed' },
  ];

    const TicketCard = ({ ticket, index, onSelect }) => {
      const priority = normalizePriority(ticket.priority);
      const [isFixing, setIsFixing] = useState(false);
      const [fixStatus, setFixStatus] = useState('');
      
      const handleFixTicket = async (e) => {
        e.stopPropagation();
        if (isFixing || ticket.status === 'completed') return;
      
      setIsFixing(true);
      setFixStatus('Fixing...');
      
      try {
        await authenticatedFetch('/fix-ticket', {
          body: {
            completion_notes: `Ticket ${ticket.ticket_id} fixed via dashboard fix button`,
            test_steps: 'Manual fix via dashboard UI',
            test_results: 'Fix applied successfully',
            summary: `Resolved ${ticket.ticket_id} via dashboard fix`
          }
        });
        
        setFixStatus('✓ Fixed');
        setTimeout(() => setFixStatus(''), 2000);
      } catch (err) {
        setFixStatus(`✗ ${err.message}`);
        setTimeout(() => setFixStatus(''), 3000);
      } finally {
        setIsFixing(false);
      }
    };
    
    const handleCardClick = () => {
      if (typeof onSelect === 'function') {
        onSelect();
      }
    };

    const handleCardKeyDown = (event) => {
      if (!onSelect) return;
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        onSelect();
      }
    };

    return h('article', { 
      key: ticket.ticket_id || index, 
      className: `ticket-card ${ticket.status}`,
      style: { cursor: 'pointer' },
      role: 'button',
      tabIndex: 0,
      onClick: handleCardClick,
      onKeyDown: handleCardKeyDown
    },
      h('div', { className: 'ticket-select' },
        h('input', {
          type: 'checkbox',
          checked: selectedTickets.has(ticket.ticket_id),
          onChange: (e) => {
            const newSet = new Set(selectedTickets);
            if (e.target.checked) {
              newSet.add(ticket.ticket_id);
            } else {
              newSet.delete(ticket.ticket_id);
            }
            setSelectedTickets(newSet);
          }
        })
      ),

            h('div', { className: 'ticket-card-header' },
              h('span', { className: `priority-badge ${priority.toLowerCase()}` }, priority),
              h('span', { className: `severity-badge ${priority.toLowerCase()}` }, PRIORITY_LABELS[priority] || 'Priority'),
              h('span', { className: `status-badge ${ticket.status}` }, ticket.status),
              (() => {
                const sla = getSlaStatus(ticket.created, priority);
                if (!sla) {
                  return h('span', { className: 'sla-badge' }, '⏰ n/a');
                }
                const remaining = Math.round(sla.remainingHours);
                const overdue = Math.round(sla.overdueHours);
                if (sla.isOverdue) {
                  return h('span', {
                    className: 'sla-badge overdue',
                    title: `SLA breach: ${overdue}h overdue (P${priority} SLA: ${sla.slaHours}h)`
                  }, `SLA +${overdue}h`);
                }
                const warning = remaining <= Math.max(1, Math.round(sla.slaHours * 0.25));
                return h('span', {
                  className: `sla-badge${warning ? ' warning' : ''}`,
                  title: `SLA remaining: ${remaining}h (P${priority} SLA: ${sla.slaHours}h)`
                }, `SLA ${remaining}h`);
              })(),
              h('span', { className: 'ticket-id' }, ticket.ticket_id?.slice(0, 10) || 'N/A')
            ),
      h('div', { className: 'ticket-card-title' }, ticket.error_type || 'Unknown'),
      h('div', { className: 'ticket-card-message' }, ticket.message || ''),
      h('div', { className: 'ticket-card-meta' },
        h('span', null, '📁 ', ticket.source || 'unknown'),
        h('span', null, '⏱ ', formatRelativeTime(ticket.created))
      ),
      ticket.status === 'open' && h('div', { className: 'ticket-card-actions' },
        h('button', {
          className: `btn-small fix-ticket-btn ${isFixing ? 'working' : ''}`,
          onClick: handleFixTicket,
          disabled: isFixing,
          title: 'Fix this ticket'
        }, isFixing ? 'Fixing...' : 'Fix'),
        fixStatus && h('span', { className: 'fix-status-badge' }, fixStatus)
      )
    );
  };

  const renderFiltersBar = () => h('div', { className: 'tickets-filter-bar' },
    h('div', { className: 'filter-groups' },
      h('div', { className: 'filter-group' },
        h('span', { className: 'filter-label' }, 'Priority'),
        priorityOptions.map((option) =>
          h('button', {
            key: option,
            type: 'button',
            className: `filter-chip ${priorityFilter === option ? 'active' : ''}`,
            onClick: () => setPriorityFilter(option),
          }, option)
        )
      ),
      h('div', { className: 'filter-group' },
        h('span', { className: 'filter-label' }, 'Status'),
        statusOptions.map((option) =>
          h('button', {
            key: option.key,
            type: 'button',
            className: `filter-chip ${statusFilter === option.key ? 'active' : ''}`,
            onClick: () => setStatusFilter(option.key),
          }, option.label)
        )
      )
    ),
    h('div', { className: 'filter-search-wrapper' },
      h('input', {
        type: 'search',
        className: 'filter-search',
        placeholder: 'Search tickets…',
        value: searchTerm,
        onChange: (e) => setSearchTerm(e.target.value),
        'aria-label': 'Search tickets',
      })
    ),
    h('div', { className: 'filter-meta' },
      `Updated ${updatedLabel} • Showing ${filteredTickets.length} of ${tickets.length} tickets`
    )
  );

    const renderTicketCard = (ticket, index) => {
      return h(TicketCard, {
        ticket,
        index,
        onSelect: () => fetchTicket(ticket.ticket_id)
      });
    };

  const renderModal = () => {
    if (!selectedTicket && !modalLoading && !modalError) return null;

    const backdropStyle = {
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'transparent',
      zIndex: 9999,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    };

    const modalStyle = {
      background: 'var(--bg-secondary)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)',
      maxWidth: '90vw',
      maxHeight: '90vh',
      overflow: 'auto',
      color: 'var(--text-primary)',
      padding: 'var(--spacing-xl)'
    };

    const sectionStyle = {
      marginBottom: 'var(--spacing-xl)',
      paddingBottom: 'var(--spacing-lg)',
      borderBottom: '1px solid var(--border)'
    };

    const fieldStyle = { marginBottom: 'var(--spacing-md)', fontSize: '13px' };
    const labelStyle = { fontWeight: '600', color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' };

    return h('div', { 
      style: backdropStyle,
      onClick: closeModal 
    },
      h('div', { 
        style: { 
          background: 'transparent', 
          maxWidth: '800px', 
          width: '100%', 
          maxHeight: '90vh', 
          overflow: 'auto' 
        },
        onClick: (e) => e.stopPropagation()
      },
        modalLoading ? h(LoadingSpinner) :
        modalError ? h(ErrorDisplay, { message: modalError }) :
        h('div', { style: modalStyle },
          h('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-xl)' } },
            h('h2', { style: { fontSize: '20px', fontWeight: '600' } }, `Ticket ${selectedTicket.id}`),
            h('button', { 
              onClick: closeModal, 
              style: { 
                background: 'transparent', 
                border: '1px solid var(--border)', 
                borderRadius: 'var(--radius-md)', 
                padding: '8px 16px', 
                color: 'var(--text-primary)',
                cursor: 'pointer'
              } 
            }, 'Close')
          ),
          h('div', { style: sectionStyle },
            h('div', { style: labelStyle }, 'Summary'),
            h('div', { style: fieldStyle },
              h('strong', null, 'Priority: '), selectedTicket.priority
            ),
            h('div', { style: fieldStyle },
              h('strong', null, 'Status: '), selectedTicket.status
            ),
            h('div', { style: fieldStyle },
              h('strong', null, 'Created: '), formatTime(selectedTicket.created_at)
            ),
            h('div', { style: fieldStyle },
              h('strong', null, 'Updated: '), selectedTicket.updated_at ? formatTime(selectedTicket.updated_at) : 'N/A'
            )
          ),
          h('div', { style: sectionStyle },
            h('div', { style: labelStyle }, 'Error Details'),
            h('div', { style: fieldStyle },
              h('strong', null, 'Type: '), selectedTicket.error_type
            ),
            h('div', { style: fieldStyle },
              h('strong', null, 'Message: '), selectedTicket.message
            ),
            h('div', { style: fieldStyle },
              h('strong', null, 'Source: '), selectedTicket.source
            )
          ),
          selectedTicket.stack_trace && h('div', { style: sectionStyle },
            h('div', { style: labelStyle }, 'Stack Trace'),
            h('pre', { 
              style: { 
                background: 'var(--bg-panel)', 
                padding: 'var(--spacing-md)', 
                borderRadius: 'var(--radius-md)', 
                fontSize: '12px',
                maxHeight: '200px',
                overflow: 'auto',
                whiteSpace: 'pre-wrap',
                fontFamily: 'IBM Plex Mono, monospace'
              } 
            }, selectedTicket.stack_trace)
          ),
          (selectedTicket.ai_remediation_notes || selectedTicket.completion_summary || selectedTicket.completion_notes) && h('div', { style: sectionStyle },
            h('div', { style: labelStyle }, 'Remediation & Completion'),
            selectedTicket.ai_remediation_notes && h('div', { style: fieldStyle },
              h('strong', null, 'AI Notes: '), selectedTicket.ai_remediation_notes
            ),
            selectedTicket.completion_summary && h('div', { style: fieldStyle },
              h('strong', null, 'Summary: '), selectedTicket.completion_summary
            ),
            selectedTicket.completion_notes && h('div', { style: { ...fieldStyle, fontWeight: 'bold', color: '#10b981', background: 'rgba(16,185,129,0.1)', padding: '8px', borderRadius: '4px', borderLeft: '3px solid #10b981' } },
              h('strong', null, '📝 Completion Notes: '), selectedTicket.completion_notes
            ),

            selectedTicket.test_steps && h('div', { style: fieldStyle },
              h('strong', null, 'Test Steps: '), selectedTicket.test_steps
            ),
            selectedTicket.test_results && h('div', { style: fieldStyle },
              h('strong', null, 'Test Results: '), selectedTicket.test_results
            )
          ),
          selectedTicket.completion_notes && selectedTicket.message && h('div', { style: sectionStyle },
            h('div', { style: labelStyle }, 'Changes Diff'),
            h('div', { style: { display: 'flex', gap: 'var(--spacing-md)', fontSize: '12px' } },
              h('div', { style: { flex: 1, background: '#1a1a1a', padding: 'var(--spacing-sm)', borderRadius: 'var(--radius-sm)', maxHeight: '200px', overflow: 'auto' } },
                h('div', { style: labelStyle }, 'Before (Issue)'),
                h('pre', { style: { margin: 0, whiteSpace: 'pre-wrap', fontFamily: 'IBM Plex Mono, monospace' } }, selectedTicket.message.substring(0, 1000))
              ),
              h('div', { style: { flex: 1, background: '#1e3a1e', padding: 'var(--spacing-sm)', borderRadius: 'var(--radius-sm)', maxHeight: '200px', overflow: 'auto' } },
                h('div', { style: labelStyle }, 'After (Resolution)'),
                h('pre', { style: { margin: 0, whiteSpace: 'pre-wrap', fontFamily: 'IBM Plex Mono, monospace' } }, selectedTicket.completion_notes.substring(0, 1000))
              )
            )
          ),
          h('div', { style: sectionStyle },
            h('div', { style: labelStyle }, 'Remediation Checklist'),
            h('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 'var(--spacing-sm)' } },
              [
                { label: 'Documented', key: 'documented', status: selectedTicket.documented },
                { label: 'Functioning', key: 'functioning', status: selectedTicket.functioning },
                { label: 'Tested', key: 'tested', status: selectedTicket.tested },
                { label: 'Completed', key: 'completed', status: selectedTicket.completed }
              ].map(({ label, status }) =>
                h('label', { style: { display: 'flex', alignItems: 'center', fontSize: '13px' } },
                  h('input', {
                    type: 'checkbox',
                    checked: status || false,
                    disabled: true,
                    style: { marginRight: 'var(--spacing-xs)' }
                  }),
                  label
                )
              )
            )
          ),


          selectedTicket.file_context && Object.keys(selectedTicket.file_context).length > 0 && h('div', { style: sectionStyle },
            h('div', { style: labelStyle }, 'File Context'),
            Object.entries(selectedTicket.file_context).map(([file, content]) =>
              h('div', { key: file, style: { marginBottom: 'var(--spacing-md)' } },
                h('strong', { style: { fontSize: '12px' } }, file),
                h('pre', { 
                  style: { 
                    background: 'var(--bg-panel)', 
                    padding: 'var(--spacing-sm)', 
                    borderRadius: 'var(--radius-sm)', 
                    fontSize: '11px',
                    maxHeight: '100px',
                    overflow: 'auto',
                    whiteSpace: 'pre-wrap',
                    fontFamily: 'IBM Plex Mono, monospace'
                  } 
                }, content.substring(0, 500) + (content.length > 500 ? '...' : ''))
              )
            )
          )
        )
      )
    );
  };

  return h('div', { className: 'panel tickets-board' },
    h('div', { className: 'panel-header' },
      h('div', { className: 'panel-title' },
        h('span', { className: 'panel-title-icon' }, '🎫'),
        'ALL TICKETS'
      ),
      h('div', { className: 'panel-actions' },
        h('span', { className: 'tickets-live' },
          h('span', { className: 'tickets-live-dot' }),
          'Live',
          h('span', { className: 'tickets-live-time' }, `Updated ${updatedLabel}`)
        ),
        h('span', { className: 'text-muted', style: { fontSize: '11px' } },
          `${data?.total_open ?? 0} open • ${data?.total_completed ?? 0} completed`
        )
      )
    ),
    renderFiltersBar(),
    filteredTickets.length > 0 ? h('div', { className: 'priority-lanes' },
      PRIORITY_ORDER.map((priority) => {
        const group = groupedTickets[priority];
        const openTickets = group?.open || [];
        const completedTickets = group?.completed || [];
        const label = PRIORITY_LABELS[priority] || 'Priority';
        const oldestOpen = openTickets.reduce((oldest, ticket) => {
          const createdAt = ticket?.created ? new Date(ticket.created) : null;
          if (!createdAt || Number.isNaN(createdAt.getTime())) {
            return oldest;
          }
          if (!oldest) {
            return ticket;
          }
          const oldestDate = new Date(oldest.created);
          return createdAt < oldestDate ? ticket : oldest;
        }, null);
        const laneSla = oldestOpen ? getSlaStatus(oldestOpen.created, priority) : null;

        return h('section', {
          key: priority,
          className: 'priority-lane',
          'data-priority': priority,
        },
          h('div', { className: 'priority-lane-header' },
            h('div', { className: 'priority-lane-title' },
              h('span', { className: `priority-badge ${priority.toLowerCase()}` }, priority),
              h('div', { className: 'priority-lane-label' }, label)
            ),
            h('div', { className: 'priority-lane-meta' },
              h('span', { className: `severity-badge ${priority.toLowerCase()}` }, label),
              laneSla
                ? h('span', {
                  className: `sla-badge${laneSla.isOverdue ? ' overdue' : ''}${laneSla.remainingHours <= Math.max(1, Math.round(laneSla.slaHours * 0.25)) ? ' warning' : ''}`,
                  title: laneSla.isOverdue
                    ? `SLA breach: ${Math.round(laneSla.overdueHours)}h overdue (P${priority} SLA: ${laneSla.slaHours}h)`
                    : `SLA remaining: ${Math.round(laneSla.remainingHours)}h (P${priority} SLA: ${laneSla.slaHours}h)`
                }, laneSla.isOverdue
                  ? `SLA +${Math.round(laneSla.overdueHours)}h`
                  : `SLA ${Math.round(laneSla.remainingHours)}h`)
                : h('span', { className: 'sla-badge idle' }, 'SLA idle')
            ),
            h('div', { className: 'priority-lane-counts' },
              h('span', { className: 'lane-count open' }, `${openTickets.length} open`),
              h('span', { className: 'lane-count completed' }, `${completedTickets.length} done`)
            )
          ),
          openTickets.length > 0
            ? openTickets.map(renderTicketCard)
            : h('div', { className: 'lane-empty' }, 'No open tickets'),
          completedTickets.length > 0 && h('details', { className: 'lane-completed' },
            h('summary', null, `Show ${completedTickets.length} completed`),
            h('div', { className: 'lane-completed-list' },
              completedTickets.map(renderTicketCard)
            )
          )
        );
      })
    ) : h('div', { style: { padding: '24px', textAlign: 'center', color: 'var(--text-dim)' } }, 'No tickets found'),
    renderModal()
  );
};

// Logs View Component
const LogsView = () => {
  const [logType, setLogType] = useState('audit');
  const [autoScroll, setAutoScroll] = useState(true);
  const [filter, setFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all');
  const logContainerRef = useRef(null);

  const { data, loading, error, lastUpdated } = useFetch(`/logs?type=${logType}&lines=300`, LOG_REFRESH_INTERVAL);

  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [data, autoScroll]);

  const logTypes = [
    { id: 'audit', label: 'Audit' },
    { id: 'errors', label: 'Errors' },
    { id: 'list', label: 'List' },
    { id: 'setup', label: 'Setup' },
  ];

  const logEntries = data?.content || [];
  const normalizedFilter = filter.toLowerCase();
  const severityLevels = [
    { id: 'all', label: 'All', color: '#9ca3ff' },
    { id: 'error', label: 'Errors', color: '#f87171' },
    { id: 'warning', label: 'Warnings', color: '#fbbf24' },
    { id: 'info', label: 'Info', color: '#38bdf8' },
    { id: 'audit', label: 'Audit', color: '#34d399' },
  ];

  const severityCounts = logEntries.reduce((acc, log) => {
    const level = (log.level || log.event || 'info').toLowerCase();
    acc.all += 1;
    if (level.includes('error')) {
      acc.error += 1;
    } else if (level.includes('warn')) {
      acc.warning += 1;
    } else if (level === 'audit' || log.event === 'audit') {
      acc.audit += 1;
    } else if (level.includes('info')) {
      acc.info += 1;
    } else {
      acc.info += 1;
    }
    return acc;
  }, { all: 0, error: 0, warning: 0, info: 0, audit: 0 });

  const severityMatches = (logLevel) => {
    if (severityFilter === 'all') return true;
    const normalized = (logLevel || 'info').toLowerCase();
    if (severityFilter === 'audit') {
      return normalized === 'audit' || logLevel === 'audit';
    }
    return normalized.includes(severityFilter);
  };

  const filteredLogs = logEntries
    .filter((log) => severityMatches(log.level || log.event))
    .filter((log) => {
      if (!normalizedFilter) return true;
      return (log.text || '').toLowerCase().includes(normalizedFilter);
    });

  const updatedLabel = lastUpdated
    ? `Updated ${formatTime(lastUpdated.toISOString())}`
    : 'Updated —';

  return h('div', { className: 'panel' },
    h('div', { className: 'panel-header' },
      h('div', { className: 'panel-title' },
        h('span', { className: 'panel-title-icon' }, '📜'),
        'LIVE LOGS'
      )
    ),
    h('div', { className: 'log-summary-grid' },
      severityLevels.map((level) =>
        h('div', { key: level.id, className: 'log-summary-card' },
          h('span', { className: 'log-summary-label' }, level.label),
          h('strong', {
            className: 'log-summary-value',
            style: { color: level.color }
          }, (severityCounts[level.id] ?? 0).toString()),
          h('span', { className: 'log-summary-meta' }, `${level.id === 'all' ? logEntries.length : (severityCounts[level.id] ?? 0)} entries`)
        )
      )
    ),
    h('div', { className: 'log-controls' },
      h('div', { className: 'log-tabs' },
        logTypes.map(type =>
          h('button', {
            key: type.id,
            className: `log-tab ${logType === type.id ? 'active' : ''}`,
            onClick: () => setLogType(type.id)
          }, type.label)
        )
      ),
      h('div', { className: 'log-chips' },
        severityLevels.map(level =>
          h('button', {
            key: level.id,
            type: 'button',
            className: `log-chip ${severityFilter === level.id ? 'active' : ''}`,
            onClick: () => setSeverityFilter(level.id)
          }, level.label)
        )
      ),
      h('div', { className: 'log-controls-actions' },
        h('input', {
          type: 'text',
          className: 'log-filter',
          placeholder: 'Filter logs...',
          value: filter,
          onChange: (e) => setFilter(e.target.value)
        }),
        h('button', {
          className: `btn ${autoScroll ? 'btn-primary' : ''}`,
          onClick: () => setAutoScroll(!autoScroll),
          title: autoScroll ? 'Auto-scroll ON' : 'Auto-scroll OFF'
        }, autoScroll ? '▼' : '▽'),
        h('span', { className: 'log-updated-label' }, updatedLabel),
        h('span', { className: 'text-dim', style: { fontSize: '10px' } },
          `${filteredLogs.length}/${data?.total_lines || 0}`
        )
      )
    ),
    loading && !data ? h(LoadingSpinner) :
    error ? h(ErrorDisplay, { message: error }) :
    h('div', { className: 'log-container', ref: logContainerRef },
      filteredLogs.length > 0 ? filteredLogs.map((log, i) => {
        const levelClass = log.level ? `log-${log.level.toLowerCase()}` : 'log-info';
        const meta = log.ticket && log.ticket !== '-' ? log.ticket : null;
        return h('div', {
          key: `${log.timestamp || 'ts'}-${i}`,
          className: `log-line ${levelClass}`
        },
          h('span', { className: 'log-level-indicator' }),
          h('div', { className: 'log-line-body' },
            h('div', { className: 'log-line-meta' },
              h('span', { className: 'log-event-label' }, log.event || 'LOG'),
              meta && h('span', { className: 'log-ticket' }, meta)
            ),
            h('span', { className: 'log-text' }, log.text || '')
          )
        );
      }) : h('div', { style: { padding: '24px', textAlign: 'center', color: 'var(--text-dim)' } }, 'No log entries')
    )
  );
};

// System View Component
const SystemView = () => {
  const { data, loading, error } = useFetch('/system');

  if (loading) return h(LoadingSpinner);
  if (error) return h(ErrorDisplay, { message: error });

  const platform = data?.platform || {};
  const project = data?.project || {};
  const server = data?.server || {};
  const resources = data?.resources || {};
  const health = data?.health || {};
  const git = data?.git || {};
  const paths = data?.paths || {};
  const recentEvents = data?.recent_events || [];

  const getDiskColor = (percent) => percent > 90 ? '#ef4444' : percent > 80 ? '#f59e0b' : '#10b981';

  return h('div', null,
    // Enhanced Stats Grid
    h('div', { className: 'stats-grid' },
      h(MetricTile, {
        label: 'HEALTH',
        value: health.status || 'UNKNOWN',
        icon: '📡',
        color: health.healthy ? '#10b981' : '#ef4444',
        subvalue: `${health.warnings || 0} warnings • ${health.errors || 0} errors`
      }),
      h(MetricTile, {
        label: 'DISK',
        value: resources.disk ? `${resources.disk.percent}%` : 'N/A',
        icon: '💿',
        color: resources.disk ? getDiskColor(resources.disk.percent) : undefined,
        subvalue: resources.disk ? `${resources.disk.used_gb}/${resources.disk.total_gb} GB` : ''
      }),
      h(MetricTile, {
        label: 'GIT',
        value: git.clean ? 'CLEAN' : 'DIRTY',
        icon: '🐙',
        color: git.clean ? '#10b981' : '#f59e0b',
        subvalue: git.branch ? `branch ${git.branch}` : 'unknown'
      }),
      h(MetricTile, {
        label: 'OPEN TICKETS',
        value: health.open_tickets || 0,
        icon: '🎫',
        color: (health.open_tickets || 0) > 0 ? '#f59e0b' : '#10b981'
      }),
      h(MetricTile, {
        label: 'MEMORY',
        value: resources.memory ? `${resources.memory.percent}%` : 'N/A',
        icon: '💾',
        color: resources.memory?.percent > 80 ? '#ef4444' : '#10b981',
        subvalue: resources.memory ? `${resources.memory.used_gb}/${resources.memory.total_gb} GB` : ''
      }),
      h(MetricTile, {
        label: 'CPU',
        value: resources.cpu_percent !== null ? `${resources.cpu_percent}%` : 'N/A',
        icon: '🔥',
        color: resources.cpu_percent > 80 ? '#ef4444' : '#10b981'
      }),
      h(MetricTile, {
        label: 'PYTHON',
        value: platform.python_version?.split('.').slice(0, 2).join('.') || 'N/A',
        icon: '🐍',
        subvalue: platform.python_version || 'N/A'
      }),
      h(MetricTile, {
        label: 'UPTIME',
        value: server.uptime?.split(' ')[0] || 'N/A',
        icon: '⏰',
        subvalue: server.uptime || ''
      })
    ),

    // Paths Panel
    h('div', { className: 'panel' },
      h('div', { className: 'panel-header' },
        h('div', { className: 'panel-title' },
          h('span', { className: 'panel-title-icon' }, '📁'),
          'PATHS'
        )
      ),
      h('div', { className: 'paths-table' },
        h('div', { className: 'table-row header' },
          h('div', { className: 'table-cell label' }, 'Path'),
          h('div', { className: 'table-cell value truncate' }, 'Location')
        ),
        h('div', { className: 'table-row' },
          h('div', { className: 'table-cell label' }, 'Project'),
          h('div', { className: 'table-cell value mono truncate' }, project.root || 'N/A')
        ),
        h('div', { className: 'table-row' },
          h('div', { className: 'table-cell label' }, 'Base'),
          h('div', { className: 'table-cell value mono truncate' }, paths.base_dir || 'N/A')
        ),
        h('div', { className: 'table-row' },
          h('div', { className: 'table-cell label' }, 'Data'),
          h('div', { className: 'table-cell value mono truncate' }, paths.data_dir || 'N/A')
        ),
        h('div', { className: 'table-row' },
          h('div', { className: 'table-cell label' }, 'Logs'),
          h('div', { className: 'table-cell value mono truncate' }, paths.logs_dir || 'N/A')
        )
      )
    ),

    // Git Panel
    h('div', { className: 'panel' },
      h('div', { className: 'panel-header' },
        h('div', { className: 'panel-title' },
          h('span', { className: 'panel-title-icon' }, '🐙'),
          'GIT STATUS'
        )
      ),
      h('div', { className: 'git-table' },
        h('div', { className: 'table-row header' },
          h('div', { className: 'table-cell label' }, 'Info'),
          h('div', { className: 'table-cell value' }, 'Value')
        ),
        h('div', { className: 'table-row' },
          h('div', { className: 'table-cell label' }, 'Branch'),
          h('div', { className: 'table-cell value mono' }, git.branch || 'N/A')
        ),
        h('div', { className: 'table-row' },
          h('div', { className: 'table-cell label' }, 'Commit'),
          h('div', { className: 'table-cell value mono truncate' }, git.commit?.slice(0,8) || 'N/A')
        ),
        h('div', { className: 'table-row' },
          h('div', { className: 'table-cell label' }, 'Clean'),
          h('div', { className: 'table-cell value', style: { color: git.clean ? '#10b981' : '#f59e0b' } }, git.clean ? 'Yes' : 'No')
        )
      )
    ),

    // Recent Events
    recentEvents.length > 0 && h('div', { className: 'panel' },
      h('div', { className: 'panel-header' },
        h('div', { className: 'panel-title' },
          h('span', { className: 'panel-title-icon' }, '📜'),
          'RECENT EVENTS'
        ),
        h('span', { className: 'text-muted', style: { fontSize: '11px' } }, `${recentEvents.length} events`)
      ),
      h('div', { className: 'events-list' },
        recentEvents.map((event, i) =>
          h('div', { key: i, className: 'event-item' },
            h('span', { className: 'event-event' }, event.event),
            h('span', { className: 'event-text truncate' }, event.text)
          )
        )
      )
    ),

    // Health Warnings (if any)
    (health.warnings > 0 || health.errors > 0) && h('div', { className: 'panel warning-panel' },
      h('div', { className: 'panel-header' },
        h('div', { className: 'panel-title' },
          h('span', { className: 'panel-title-icon' }, '⚠️'),
          'HEALTH ISSUES'
        )
      ),
      h('ul', { className: 'health-list' },
        health.warnings > 0 && h('li', { className: 'health-warning' }, `${health.warnings} warning(s) detected`),
        health.errors > 0 && h('li', { className: 'health-error' }, `${health.errors} error(s) detected`)
      )
    )
  );
};

// Settings View Component
const SettingsView = () => {
  const [aiProvider, setAiProvider] = useState('mimo-flash-v2-free');
  const [aiApiKey, setAiApiKey] = useState('');
  const [aiModel, setAiModel] = useState('');
  const [aiEnabled, setAiEnabled] = useState(false);
  const [adminPassword, setAdminPassword] = useState('');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const { data: aiStatus } = useFetch('/ai-status', 8000);
  const { data: systemInfo } = useFetch('/system', 10000);
  const { execute: authenticatedFetch } = useAuthenticatedFetch();

  // Load current settings
  useEffect(() => {
    // Load stored admin password from localStorage
    const storedPassword = getAdminPassword();
    if (storedPassword) {
      setAdminPassword(storedPassword);
    }

    const loadSettings = async () => {
      try {
        const headers = buildAdminHeaders();
        const response = await fetch(`${API_BASE}/settings`, { headers });
        if (response.ok) {
          const data = await response.json();
          setAiProvider(data.ai_provider || 'mimo-flash-v2-free');
          setAiApiKey(data.ai_api_key || '');
          setAiModel(data.ai_model || '');
          setAiEnabled(data.ai_enabled || false);
        }
      } catch (err) {
        console.error('Failed to load settings:', err);
      }
    };
    loadSettings();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setMessage('');

    try {
      // Store admin password in localStorage for subsequent requests
      if (adminPassword) {
        setAdminPasswordInStorage(adminPassword);
      }

      await authenticatedFetch('/settings', {
        body: {
          ai_provider: aiProvider,
          ai_api_key: aiApiKey,
          ai_model: aiModel,
          ai_enabled: aiEnabled,
        }
      });

      setMessage('Settings saved successfully! Admin password stored for this session.');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setMessage(`Error: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const fallbackProviders = [
    { value: 'auto', label: 'Auto (Do_AF fallback chain)' },
    { value: 'claude_local', label: 'Claude Code (local CLI)' },
    { value: 'openai_cli', label: 'OpenAI CLI (local session)' },
    { value: 'claude_api', label: 'Claude API' },
    { value: 'openai', label: 'OpenAI API' },
    { value: 'ollama', label: 'Ollama (local)' },
    { value: 'mimo-flash-v2-free', label: 'Mimo Flash v2 Free (default)' },
  ];
  const providerOptions = aiStatus?.provider_options || fallbackProviders;
  const feedbackLog = aiStatus?.feedback_log?.join('\n') || 'No AI feedback yet.';
  const providerOrder = aiStatus?.provider_order?.join(' → ') || '—';
  const activeProvider = aiStatus?.active_provider || '—';
  const activeModel = aiStatus?.active_model || '—';
  const preferredProvider = aiStatus?.preferred_provider || aiProvider;
  const aiHealth = aiStatus?.status || 'Unknown';
  const lastSync = aiStatus?.timestamp
    ? new Date(aiStatus.timestamp).toLocaleString()
    : '—';
  const serverUptime = systemInfo?.server?.uptime || '—';
  const platformSummary = systemInfo?.platform
    ? `${systemInfo.platform.system} ${systemInfo.platform.release}`
    : '—';
  const memoryPercent = systemInfo?.resources?.memory?.percent
    ? `${systemInfo.resources.memory.percent}%`
    : '—';
  const projectRoot = systemInfo?.project?.root || '—';
  const aiHeaderLabel = aiEnabled ? 'AI automation ON' : 'AI automation OFF';
  const aiHeaderTone = aiEnabled ? 'enabled' : 'disabled';

  useEffect(() => {
    if (aiProvider === 'mimo-flash-v2-free' && (!aiModel || aiModel === '')) {
      setAiModel('mimo-flash-v2-free');
    }
  }, [aiProvider, aiModel]);

  return h('div', { className: 'panel settings-panel' },
    h('div', { className: 'panel-header settings-header' },
      h('div', { className: 'panel-title' },
        h('span', { className: 'panel-title-icon' }, '🔧'),
        'Settings'
      ),
      h('div', { className: 'settings-header-meta' },
        h('span', { className: `settings-chip ${aiHeaderTone}` }, aiHeaderLabel),
        h('span', { className: 'settings-chip secondary' }, `AI Health • ${aiHealth}`),
        h('span', { className: 'settings-chip secondary' }, `Last sync • ${lastSync}`)
      )
    ),
    h('div', { className: 'settings-grid' },
      h('div', { className: 'settings-card' },
        h('div', { className: 'settings-card-title' }, 'Active AI'),
        h('div', { className: 'settings-metric' },
          h('span', { className: 'settings-metric-label' }, 'Preferred'),
          h('span', { className: 'settings-metric-value' }, preferredProvider)
        ),
        h('div', { className: 'settings-metric' },
          h('span', { className: 'settings-metric-label' }, 'Active'),
          h('span', { className: 'settings-metric-value' }, `${activeProvider} • ${activeModel}`)
        ),
        h('div', { className: 'settings-metric' },
          h('span', { className: 'settings-metric-label' }, 'Provider Order'),
          h('span', { className: 'settings-metric-value' }, providerOrder)
        ),
        h('div', { className: 'settings-pill-row' },
          (aiStatus?.providers || []).map((provider) =>
            h('span', {
              key: provider.provider,
              className: `settings-pill ${provider.available ? 'available' : 'unavailable'}`
            }, provider.provider)
          )
        )
      ),
      h('div', { className: 'settings-card' },
        h('div', { className: 'settings-card-title' }, 'System Snapshot'),
        h('div', { className: 'settings-metric' },
          h('span', { className: 'settings-metric-label' }, 'Platform'),
          h('span', { className: 'settings-metric-value' }, platformSummary)
        ),
        h('div', { className: 'settings-metric' },
          h('span', { className: 'settings-metric-label' }, 'Uptime'),
          h('span', { className: 'settings-metric-value' }, serverUptime)
        ),
        h('div', { className: 'settings-metric' },
          h('span', { className: 'settings-metric-label' }, 'Memory usage'),
          h('span', { className: 'settings-metric-value' }, memoryPercent)
        ),
        h('div', { className: 'settings-metric' },
          h('span', { className: 'settings-metric-label' }, 'Project root'),
          h('span', { className: 'settings-metric-value' }, projectRoot)
        )
      ),
      h('div', { className: 'settings-card' },
        h('div', { className: 'settings-card-title' }, 'AI Controls'),
        h('div', { className: 'settings-field' },
          h('label', { className: 'settings-label' }, 'Provider'),
          h('select', {
            value: aiProvider,
            onChange: (e) => setAiProvider(e.target.value),
            className: 'settings-input',
          },
            providerOptions.map((p) => h('option', { key: p.value, value: p.value }, p.label))
          )
        ),
        h('div', { className: 'settings-field' },
          h('label', { className: 'settings-label' }, 'API Key'),
          h('input', {
            type: 'password',
            value: aiApiKey,
            onChange: (e) => setAiApiKey(e.target.value),
            placeholder: 'Provider API key (when needed)',
            className: 'settings-input',
          })
        ),
        h('div', { className: 'settings-field' },
          h('label', { className: 'settings-label' }, 'Model'),
          h('input', {
            type: 'text',
            value: aiModel,
            onChange: (e) => setAiModel(e.target.value),
            placeholder: 'Default model override',
            className: 'settings-input',
          })
        ),
        h('div', { className: 'settings-toggle' },
          h('input', {
            type: 'checkbox',
            checked: aiEnabled,
            onChange: (e) => setAiEnabled(e.target.checked),
            id: 'ai-enabled',
          }),
          h('label', { htmlFor: 'ai-enabled' }, 'Enable AI Integration')
        ),
        h('div', { className: 'settings-field' },
          h('label', { className: 'settings-label' }, 'Admin Password'),
          h('input', {
            type: 'password',
            value: adminPassword,
            onChange: (e) => setAdminPassword(e.target.value),
            placeholder: 'Enter admin password to save settings',
            className: 'settings-input',
          })
        ),
        h('div', { className: 'settings-actions' },
          h('button', {
            className: 'btn btn-primary',
            onClick: handleSave,
            disabled: saving || !adminPassword,
          }, saving ? 'Saving...' : 'Save Settings'),
          message && h('span', {
            className: `settings-message ${message.includes('Error') ? 'error' : 'ok'}`,
          }, message)
        )
      ),
      h('div', { className: 'settings-card' },
        h('div', { className: 'settings-card-title' }, 'AI Feedback Log'),
        h('textarea', {
          className: 'settings-log',
          readOnly: true,
          value: feedbackLog,
        })
      ),
      h('div', { className: 'settings-card settings-note' },
        h('div', { className: 'settings-card-title' }, 'Notes'),
        h('div', { className: 'settings-note-text' },
          'Settings are stored in memory and will reset when the server restarts. For persistent configuration, set environment variables:'
        ),
        h('ul', { className: 'settings-note-list' },
          h('li', null, 'ACTIFIX_AI_PROVIDER'),
          h('li', null, 'ACTIFIX_AI_API_KEY'),
          h('li', null, 'ACTIFIX_AI_MODEL'),
          h('li', null, 'ACTIFIX_AI_ENABLED')
        )
      )
    )
  );
};

// Modules View Component
const ModulesView = () => {
  const [refreshKey, setRefreshKey] = useState(0);
  const { data, loading, error } = useFetch(`/modules?key=${refreshKey}`, 15000);
  const [sortBy, setSortBy] = useState('name');
  const [sortDir, setSortDir] = useState('asc');
  const { execute: authenticatedFetch } = useAuthenticatedFetch();
  const refreshModules = () => setRefreshKey((rk) => rk + 1);

  const handleToggle = async (moduleId) => {
    try {
      await authenticatedFetch(`/modules/${moduleId}`, { method: 'POST' });
      setRefreshKey((rk) => rk + 1);
    } catch (e) {
      console.error('Toggle failed:', e);
    }
  };

  if (loading) return h(LoadingSpinner);
  if (error) return h(ErrorDisplay, { message: error });

  const systemModules = data?.system || [];
  const userModules = data?.user || [];

  const sortModules = (modules) => {
    return [...modules].sort((a, b) => {
      let aVal = (a[sortBy] || '').toString().toLowerCase();
      let bVal = (b[sortBy] || '').toString().toLowerCase();
      if (aVal < bVal) return sortDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
  };

  const handleSort = (column) => {
    if (sortBy === column) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortDir('asc');
    }
  };

  const sortIndicator = (column) => {
    if (sortBy !== column) return '';
    return sortDir === 'asc' ? ' ↑' : ' ↓';
  };

  const CRITICAL_MODULE_HINTS = ['screenscan'];
  const isCriticalModule = (module) => {
    const identifier = ((module.name || module.id || module.module_id) || '').toLowerCase();
    return CRITICAL_MODULE_HINTS.some((needle) => identifier.includes(needle));
  };

  const renderModuleTable = (title, modules, icon) => {
    const sortedModules = sortModules(modules);
    return h('div', { className: 'panel modules-panel' },
      h('div', { className: 'panel-header modules-header' },
        h('div', { className: 'modules-note' }, 'Critical modules (screenscan, etc.) display extra warnings before toggling.'),
        h('div', { className: 'panel-title' },
          h('span', { className: 'panel-title-icon' }, icon),
          title
        ),
        h('div', { className: 'panel-actions panel-actions--modules' },
          h('span', { className: 'text-muted modules-count' }, `${sortedModules.length} modules`),
          h('span', { className: 'text-dim modules-count-info' }, `Sorted: ${sortBy} ${sortDir.toUpperCase()}`),
          h('button', {
            type: 'button',
            className: 'btn modules-refresh',
            onClick: refreshModules,
          }, 'Refresh')
        )
      ),
      modules.length === 0 ?
        h('div', { className: 'module-empty' }, 'No modules') :
        h('div', { className: 'modules-table' },
          h('div', { className: 'table-header' },
            h('div', { className: 'table-cell name', onClick: () => handleSort('name'), title: 'Click to sort' }, 'Name', sortIndicator('name')),
            h('div', { className: 'table-cell domain', onClick: () => handleSort('domain'), title: 'Click to sort' }, 'Domain', sortIndicator('domain')),
            h('div', { className: 'table-cell owner', onClick: () => handleSort('owner'), title: 'Click to sort' }, 'Owner', sortIndicator('owner')),
            h('div', { className: 'table-cell port', onClick: () => handleSort('port'), title: 'Click to sort' }, 'Port', sortIndicator('port')),
            h('div', { className: 'table-cell status', onClick: () => handleSort('status'), title: 'Click to sort' }, 'Status', sortIndicator('status')),
            h('div', { className: 'table-cell actions' }, 'Actions'),
            h('div', { className: 'table-cell summary', onClick: () => handleSort('summary'), title: 'Click to sort' }, 'Summary', sortIndicator('summary'))
          ),
          sortedModules.map((m, idx) =>
            h('div', { key: `${title}-${idx}`, className: 'table-row' },
              h('div', { className: 'table-cell name truncate' }, m.name || '—'),
              h('div', { className: 'table-cell domain truncate' }, m.domain || '—'),
              h('div', { className: 'table-cell owner truncate' }, m.owner || '—'),
              h('div', { className: 'table-cell port' }, m.port ? `${m.port}` : '—'),
              h('div', { className: 'table-cell status' },
                h('span', { className: `status-badge ${m.status || 'active'}` }, m.status || 'active')
              ),
              h('div', { className: 'table-cell actions' },
                h('button', {
                  className: `btn-small ${m.status === 'disabled' ? 'btn-success' : 'btn-warning'} ${isCriticalModule(m) && m.status === 'active' ? 'critical-warning' : ''}`,
                  onClick: () => handleToggle(m.name, m.status),
                  title: `Toggle ${m.name}${isCriticalModule(m) ? ' (Critical module – keep enabled)' : ''}`
                }, m.status === 'disabled' ? 'Enable' : 'Disable'),
                isCriticalModule(m) && h('span', { className: 'critical-chip', title: 'This module is critical and should stay enabled whenever possible.' }, 'Critical module')

              ),
              h('div', { className: 'table-cell summary truncate' }, m.summary || '—')
            )
          )
        )
    );
  };

  return h('div', null,
    renderModuleTable('SYSTEM MODULES', systemModules, '⚙️'),
    renderModuleTable('USER MODULES', userModules, '👤')
  );
};

// Quiz View Component
const QuizView = () => {
  const [currentQuiz, setCurrentQuiz] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [score, setScore] = useState(0);
  const [answered, setAnswered] = useState(false);
  const [category, setCategory] = useState('all');

  const quizData = {
    actifix: [
      {
        question: "What is the primary purpose of the Actifix system?",
        options: [
          "To manage poker games",
          "To track and fix software errors automatically",
          "To monitor network traffic",
          "To manage user authentication"
        ],
        correct: 1,
        explanation: "Actifix is an error intelligence system that automatically tracks, prioritizes, and fixes software errors."
      },
      {
        question: "What does P0 priority indicate in Actifix?",
        options: [
          "Low priority issues",
          "Medium priority issues",
          "Critical issues requiring immediate attention",
          "Deferred issues"
        ],
        correct: 2,
        explanation: "P0 is the highest priority level, indicating critical issues like crashes, data loss, or security vulnerabilities that require immediate attention (1 hour SLA)."
      },
      {
        question: "Where is the canonical ticket database stored?",
        options: [
          "In memory only",
          "In .actifix/ directory",
          "In data/actifix.db",
          "In a remote cloud database"
        ],
        correct: 2,
        explanation: "The SQLite database at data/actifix.db is the single source of truth for all ticket data."
      },
      {
        question: "What is the Raise_AF gate requirement?",
        options: [
          "No environment variable required",
          "ACTIFIX_CHANGE_ORIGIN=raise_af must be set",
          "Only git commits need it",
          "It's optional for testing"
        ],
        correct: 1,
        explanation: "All changes must set ACTIFIX_CHANGE_ORIGIN=raise_af before running Actifix or making changes."
      },
      {
        question: "What does the duplicate_guard field prevent?",
        options: [
          "Multiple users from editing",
          "Duplicate tickets from being created",
          "File corruption",
          "Database locks"
        ],
        correct: 1,
        explanation: "The duplicate_guard field ensures the same error isn't logged multiple times, preventing ticket spam."
      }
    ],
    python: [
      {
        question: "What is the correct way to handle exceptions in Actifix?",
        options: [
          "Try-except with pass",
          "record_error() then re-raise",
          "Ignore the error",
          "Print to console only"
        ],
        correct: 1,
        explanation: "Always use record_error() to capture the error, then re-raise it. Never suppress errors."
      },
      {
        question: "Which module should NOT import higher-level modules?",
        options: [
          "bootstrap.py",
          "raise_af.py",
          "do_af.py",
          "main.py"
        ],
        correct: 0,
        explanation: "Lower layers cannot import higher layers. bootstrap.py is at the bottom of the dependency chain."
      },
      {
        question: "What is the correct import for recording errors?",
        options: [
          "from actifix import record_error",
          "from actifix.raise_af import record_error, TicketPriority",
          "import raise_af",
          "from raise_af import record_error"
        ],
        correct: 1,
        explanation: "Use: from actifix.raise_af import record_error, TicketPriority"
      },
      {
        question: "What should you use for atomic file writes?",
        options: [
          "open().write()",
          "atomic_write()",
          "file.write()",
          "print()"
        ],
        correct: 1,
        explanation: "Always use atomic_write() from actifix.log_utils for atomic file operations."
      },
      {
        question: "What is the correct way to get Actifix paths?",
        options: [
          "os.path.join()",
          "get_actifix_paths()",
          "manual path construction",
          "Pathlib only"
        ],
        correct: 1,
        explanation: "Use get_actifix_paths() from actifix.state_paths to get canonical paths."
      }
    ],
    git: [
      {
        question: "What is the correct commit message format?",
        options: [
          "Fixed bug in raise_af",
          "feat(raise_af): add error taxonomy",
          "Changes made",
          "Update"
        ],
        correct: 1,
        explanation: "Use format: type(scope): description. Types: feat|fix|refactor|test|docs|chore|perf"
      },
      {
        question: "Which branch should you work on?",
        options: [
          "feature branches",
          "develop",
          "main",
          "master"
        ],
        correct: 1,
        explanation: "Work directly on develop with regular pushes. No per-change branches required."
      },
      {
        question: "When should you commit?",
        options: [
          "Only at the end of the day",
          "After every ticket",
          "Never",
          "Only when tests pass"
        ],
        correct: 1,
        explanation: "Always commit after every ticket and push. This is a mandatory rule."
      },
      {
        question: "What command increments the version?",
        options: [
          "git commit",
          "Manual edit of pyproject.toml",
          "Automatic after commit",
          "npm version"
        ],
        correct: 1,
        explanation: "Increment version in pyproject.toml after every commit."
      },
      {
        question: "What is the correct git push command?",
        options: [
          "git push origin develop",
          "git push",
          "git push --all",
          "git push origin main"
        ],
        correct: 0,
        explanation: "Push to develop branch: git push origin develop"
      }
    ],
    architecture: [
      {
        question: "What is the architecture graph file?",
        options: [
          "docs/ARCHITECTURE.md",
          "docs/architecture/MAP.yaml",
          "architecture.json",
          "MAP.md"
        ],
        correct: 1,
        explanation: "Always open docs/architecture/MAP.yaml and docs/architecture/DEPGRAPH.json before starting work."
      },
      {
        question: "What is the dependency rule for modules?",
        options: [
          "Higher layers can import lower layers",
          "Lower layers cannot import higher layers",
          "All modules can import each other",
          "Only main.py can import others"
        ],
        correct: 1,
        explanation: "Dependency rule: Lower layers cannot import higher layers. bootstrap → state_paths → config → log_utils → persistence → raise_af → do_af → api → main"
      },
      {
        question: "Where is the ticket database located?",
        options: [
          "In memory",
          "In .actifix/",
          "In data/actifix.db",
          "In a remote server"
        ],
        correct: 2,
        explanation: "The database at data/actifix.db is the single source of truth for all ticket data."
      },
      {
        question: "What is the fallback queue location?",
        options: [
          "data/actifix.db",
          ".actifix/actifix_fallback_queue.json",
          "logs/fallback.json",
          "tmp/queue.json"
        ],
        correct: 1,
        explanation: "If main storage fails, errors queue to .actifix/actifix_fallback_queue.json and replay on recovery."
      },
      {
        question: "What is the correct API for processing tickets?",
        options: [
          "actifix.process_tickets()",
          "actifix.do_af.get_open_tickets()",
          "actifix.main.process()",
          "actifix.api.get_tickets()"
        ],
        correct: 1,
        explanation: "Use: from actifix.do_af import get_open_tickets, mark_ticket_complete, get_ticket_stats"
      }
    ]
  };

  const allQuestions = [
    ...quizData.actifix,
    ...quizData.python,
    ...quizData.git,
    ...quizData.architecture
  ];

  const filteredQuestions = category === 'all' ? allQuestions : quizData[category];

  const startQuiz = (quizCategory) => {
    setCategory(quizCategory);
    setCurrentQuiz(quizCategory);
    setCurrentQuestionIndex(0);
    setSelectedAnswer(null);
    setShowResult(false);
    setScore(0);
    setAnswered(false);
  };

  const restartQuiz = () => {
    setCurrentQuiz(null);
    setCurrentQuestionIndex(0);
    setSelectedAnswer(null);
    setShowResult(false);
    setScore(0);
    setAnswered(false);
  };

  const handleAnswerSelect = (index) => {
    if (answered) return;
    setSelectedAnswer(index);
  };

  const submitAnswer = () => {
    if (selectedAnswer === null) return;
    
    const currentQuestion = filteredQuestions[currentQuestionIndex];
    const isCorrect = selectedAnswer === currentQuestion.correct;
    
    if (isCorrect) {
      setScore(score + 1);
    }
    
    setAnswered(true);
  };

  const nextQuestion = () => {
    if (currentQuestionIndex < filteredQuestions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      setSelectedAnswer(null);
      setAnswered(false);
    } else {
      setShowResult(true);
    }
  };

  const getScorePercentage = () => {
    return Math.round((score / filteredQuestions.length) * 100);
  };

  const getScoreMessage = () => {
    const percentage = getScorePercentage();
    if (percentage === 100) return "Perfect! You're an Actifix expert! 🎉";
    if (percentage >= 80) return "Excellent! Great knowledge! 🌟";
    if (percentage >= 60) return "Good job! Keep learning! 📚";
    if (percentage >= 40) return "Not bad! Review the docs! 📖";
    return "Keep studying! You'll get there! 💪";
  };

  const getScoreColor = () => {
    const percentage = getScorePercentage();
    if (percentage >= 80) return '#10b981';
    if (percentage >= 60) return '#f59e0b';
    return '#ef4444';
  };

  if (!currentQuiz) {
    return h('div', { className: 'panel' },
      h('div', { className: 'panel-header' },
        h('div', { className: 'panel-title' },
          h('span', { className: 'panel-title-icon' }, '🎯'),
          'ACTIFIX QUIZ'
        ),
        h('div', { className: 'panel-actions' },
          h('span', { className: 'text-muted', style: { fontSize: '11px' } },
            'Test your knowledge of Actifix, Python, Git & Architecture'
          )
        )
      ),
      h('div', { className: 'quiz-categories' },
        h('div', { className: 'quiz-category-card', onClick: () => startQuiz('actifix') },
          h('div', { className: 'quiz-category-icon' }, '🎫'),
          h('div', { className: 'quiz-category-title' }, 'Actifix'),
          h('div', { className: 'quiz-category-desc' }, '5 questions about the system')
        ),
        h('div', { className: 'quiz-category-card', onClick: () => startQuiz('python') },
          h('div', { className: 'quiz-category-icon' }, '🐍'),
          h('div', { className: 'quiz-category-title' }, 'Python'),
          h('div', { className: 'quiz-category-desc' }, '5 questions about Python best practices')
        ),
        h('div', { className: 'quiz-category-card', onClick: () => startQuiz('git') },
          h('div', { className: 'quiz-category-icon' }, '🐙'),
          h('div', { className: 'quiz-category-title' }, 'Git'),
          h('div', { className: 'quiz-category-desc' }, '5 questions about Git workflow')
        ),
        h('div', { className: 'quiz-category-card', onClick: () => startQuiz('architecture') },
          h('div', { className: 'quiz-category-icon' }, '🏗️'),
          h('div', { className: 'quiz-category-title' }, 'Architecture'),
          h('div', { className: 'quiz-category-desc' }, '5 questions about system architecture')
        ),
        h('div', { className: 'quiz-category-card', onClick: () => startQuiz('all') },
          h('div', { className: 'quiz-category-icon' }, '🎯'),
          h('div', { className: 'quiz-category-title' }, 'All Categories'),
          h('div', { className: 'quiz-category-desc' }, '20 questions - Full assessment')
        )
      ),
    );
  }

  if (showResult) {
    const percentage = getScorePercentage();
    const color = getScoreColor();
    
    return h('div', { className: 'panel' },
      h('div', { className: 'panel-header' },
        h('div', { className: 'panel-title' },
          h('span', { className: 'panel-title-icon' }, '📊'),
          'QUIZ RESULTS'
        )
      ),
      h('div', { className: 'quiz-result' },
        h('div', { className: 'quiz-result-score', style: { color } },
          h('div', { className: 'quiz-result-percentage' }, `${percentage}%`),
          h('div', { className: 'quiz-result-text' }, getScoreMessage())
        ),
        h('div', { className: 'quiz-result-details' },
          h('div', { className: 'quiz-result-stat' },
            h('span', { className: 'quiz-result-label' }, 'Correct:'),
            h('span', { className: 'quiz-result-value' }, score)
          ),
          h('div', { className: 'quiz-result-stat' },
            h('span', { className: 'quiz-result-label' }, 'Total:'),
            h('span', { className: 'quiz-result-value' }, filteredQuestions.length)
          ),
          h('div', { className: 'quiz-result-stat' },
            h('span', { className: 'quiz-result-label' }, 'Category:'),
            h('span', { className: 'quiz-result-value' }, category === 'all' ? 'All Categories' : category.charAt(0).toUpperCase() + category.slice(1))
          )
        ),
        h('div', { className: 'quiz-result-actions' },
          h('button', { className: 'btn btn-primary', onClick: restartQuiz }, 'Take Another Quiz'),
          h('button', { className: 'btn', onClick: () => startQuiz(category) }, 'Retry This Quiz')
        )
      )
    );
  }

  const currentQuestion = filteredQuestions[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / filteredQuestions.length) * 100;

  return h('div', { className: 'panel' },
    h('div', { className: 'panel-header' },
      h('div', { className: 'panel-title' },
        h('span', { className: 'panel-title-icon' }, '🎯'),
        `${category === 'all' ? 'All Categories' : category.charAt(0).toUpperCase() + category.slice(1)} Quiz`
      ),
      h('div', { className: 'panel-actions' },
        h('span', { className: 'text-muted', style: { fontSize: '11px' } },
          `Question ${currentQuestionIndex + 1} of ${filteredQuestions.length}`
        )
      )
    ),
    h('div', { className: 'quiz-progress' },
      h('div', { className: 'quiz-progress-bar', style: { width: `${progress}%` } })
    ),
    h('div', { className: 'quiz-question' },
      h('div', { className: 'quiz-question-text' }, currentQuestion.question),
      h('div', { className: 'quiz-options' },
        currentQuestion.options.map((option, index) =>
          h('div', {
            key: index,
            className: [
              'quiz-option',
              selectedAnswer === index ? 'selected' : '',
              answered && index === currentQuestion.correct ? 'correct' : '',
              answered && selectedAnswer === index && index !== currentQuestion.correct ? 'incorrect' : ''
            ].join(' '),
            onClick: () => handleAnswerSelect(index)
          },
            h('div', { className: 'quiz-option-letter' }, String.fromCharCode(65 + index)),
            h('div', { className: 'quiz-option-text' }, option)
          )
        )
      ),
      answered && h('div', { className: 'quiz-explanation' },
        h('div', { className: 'quiz-explanation-label' }, 'Explanation:'),
        h('div', { className: 'quiz-explanation-text' }, currentQuestion.explanation)
      ),
      h('div', { className: 'quiz-actions' },
        !answered && h('button', {
          className: 'btn btn-primary',
          onClick: submitAnswer,
          disabled: selectedAnswer === null
        }, 'Submit Answer'),
        answered && h('button', {
          className: 'btn btn-primary',
          onClick: nextQuestion
        }, currentQuestionIndex < filteredQuestions.length - 1 ? 'Next Question' : 'See Results')
      )
    )
  );
};

// Ideas View Component
const IdeasView = () => {
  const [idea, setIdea] = useState('');
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const { execute: authenticatedFetch, loading, error } = useAuthenticatedFetch();

  const submitIdea = async () => {
    if (!idea.trim()) return;
    setErrorMsg('');
    setResult(null);
    
    try {
      const data = await authenticatedFetch('/ideas', {
        body: { idea: idea.trim() }
      });
      setResult(data);
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  return h('div', { className: 'panel' },
    h('div', { className: 'panel-header' },
      h('div', { className: 'panel-title' },
        h('span', { className: 'panel-title-icon' }, '💡'),
        'IDEAS & REQUESTS'
      ),
      h('div', { className: 'panel-actions' },
        h('span', { className: 'text-muted', style: { fontSize: '11px' } },
          'Submit ideas → AI generates actionable tickets'
        )
      )
    ),
    h('div', { style: { display: 'flex', flexDirection: 'column', gap: 'var(--spacing-lg)' } },
      h('textarea', {
        value: idea,
        onChange: (e) => setIdea(e.target.value),
        placeholder: `Enter your idea or feature request...

Examples:
• Add dark mode toggle to dashboard
• Implement user authentication
• Create export tickets to CSV
• Add real-time notifications for P0 tickets`,
        rows: 6,
        style: {
          width: '100%',
          padding: 'var(--spacing-md)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          background: 'var(--bg-panel)',
          color: 'var(--text-primary)',
          fontSize: '13px',
          fontFamily: 'IBM Plex Mono, monospace',
          resize: 'vertical',
          lineHeight: '1.5'
        }
      }),
      h('div', { style: { display: 'flex', gap: 'var(--spacing-md)', alignItems: 'center', flexWrap: 'wrap' } },
        h('button', {
          className: 'btn btn-primary',
          onClick: submitIdea,
          disabled: loading || !idea.trim(),
          style: { minWidth: '140px' }
        }, loading ? 'Processing...' : 'Generate Ticket'),
        result && h('div', {
          className: 'panel',
          style: { flex: 1, minHeight: '80px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', maxWidth: 'none' }
        },
          h('div', { style: { fontSize: '16px', fontWeight: '600', color: '#10b981', marginBottom: 'var(--spacing-sm)' } },
            `🎫 Ticket Created: ${result.ticket_id}`
          ),
          result.preview && h('div', {
            style: { fontSize: '12px', color: 'var(--text-muted)', textAlign: 'center', maxWidth: '600px' }
          }, result.preview)
        ),
        errorMsg && h(ErrorDisplay, { message: errorMsg })
      )
    )
  );
};

// Login Component
const LoginView = ({ onLogin }) => {
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async () => {
    if (!password) {
      setError('Please enter the admin password');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/auth/verify-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
      });

      const data = await response.json();

      if (data.valid) {
        setAdminPasswordInStorage(password);
        onLogin();
      } else {
        setError(data.error || 'Invalid admin password');
      }
    } catch (err) {
      setError(`Connection error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return h('div', { className: 'login-container' },
    h('div', { className: 'login-card' },
      h('div', { className: 'login-header' },
        h('img', { src: './assets/pangolin.svg', alt: 'Actifix', className: 'login-logo' }),
        h('h1', null, 'ACTIFIX'),
        h('p', { className: 'login-subtitle' }, 'Secure Ticket Management System')
      ),
      
      h('div', { className: 'login-form' },
        h('div', { className: 'form-group' },
          h('label', null, 'Admin Password'),
          h('input', {
            type: 'password',
            value: password,
            onChange: (e) => setPassword(e.target.value),
            placeholder: 'Enter admin password',
            className: 'login-input',
            disabled: loading,
            onKeyPress: (e) => e.key === 'Enter' && handleLogin()
          })
        ),

        error && h('div', { className: 'login-error' }, error),

        h('div', { className: 'login-actions' },
          h('button', {
            onClick: handleLogin,
            disabled: loading || !password,
            className: 'btn btn-primary'
          }, loading ? 'Authenticating...' : 'Login'),
          h('p', { className: 'login-help' }, 'Default password: admin123')
        )
      )
    )
  );
};

const LoginModal = ({ onClose, onSuccess }) => {
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async () => {
    if (!password) {
      setError('Please enter the admin password');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/auth/verify-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
      });

      const data = await response.json();

      if (data.valid) {
        setAdminPasswordInStorage(password);
        onSuccess();
        onClose();
      } else {
        setError(data.error || 'Invalid admin password');
      }
    } catch (err) {
      setError(`Connection error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return h('div', { className: 'login-modal-backdrop', onClick: onClose },
    h('div', { className: 'login-modal', onClick: (e) => e.stopPropagation() },
      h('div', { className: 'login-header' },
        h('img', { src: './assets/pangolin.svg', alt: 'Actifix', className: 'login-logo-small' }),
        h('h2', null, 'Admin Login')
      ),
      h('div', { className: 'login-form' },
        h('input', {
          type: 'password',
          value: password,
          onChange: (e) => setPassword(e.target.value),
          placeholder: 'Enter admin password',
          className: 'login-input',
          disabled: loading,
          onKeyPress: (e) => e.key === 'Enter' && handleLogin()
        }),
        error && h('div', { className: 'login-error' }, error),
        h('div', { className: 'login-actions' },
          h('button', {
            onClick: handleLogin,
            disabled: loading || !password,
            className: 'btn btn-primary'
          }, loading ? 'Authenticating...' : 'Login'),
          h('button', {
            onClick: onClose,
            className: 'btn btn-secondary'
          }, 'Cancel')
        )
      )
    )
  );
};

const OnboardingModal = ({ step, stepIndex, totalSteps, onNext, onBack, onSkip, onNavigate }) => (
  h('div', { className: 'onboarding-backdrop' },
    h('div', { className: 'onboarding-card' },
      h('div', { className: 'onboarding-header' },
        h('span', { className: 'onboarding-pill' }, `Step ${stepIndex + 1} of ${totalSteps}`),
        h('h2', null, step.title)
      ),
      h('p', { className: 'onboarding-body' }, step.body),
      step.action && h('button', {
        className: 'btn onboarding-action',
        onClick: () => onNavigate(step.action.view),
      }, step.action.label),
      h('div', { className: 'onboarding-footer' },
        h('button', {
          className: 'btn btn-secondary',
          onClick: onSkip,
        }, 'Skip'),
        h('div', { className: 'onboarding-nav' },
          h('button', {
            className: 'btn btn-secondary',
            onClick: onBack,
            disabled: stepIndex === 0,
          }, 'Back'),
          h('button', {
            className: 'btn btn-primary',
            onClick: onNext,
          }, stepIndex + 1 === totalSteps ? 'Done' : 'Next')
        )
      )
    )
  )
);

// Main App Component
const App = () => {
  const [activeView, setActiveView] = useState('overview');
  const [isFixing, setIsFixing] = useState(false);
  const [fixStatus, setFixStatus] = useState('Ready to fix the next ticket');
  const [logAlert, setLogAlert] = useState(false);
  const [theme, setTheme] = useState('dark');
  const [hasPassword, setHasPassword] = useState(!!getAdminPassword());
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [onboardingStep, setOnboardingStep] = useState(0);
  const logFlashTimer = useRef(null);

  const onboardingSteps = [
    {
      title: 'Welcome to Actifix',
      body: 'This quick walkthrough highlights the key panes and actions so you can start triaging tickets immediately.',
    },
    {
      title: 'Overview health snapshot',
      body: 'Monitor open tickets, SLA pressure, and system health at a glance before diving deeper.',
      action: { label: 'Open Overview', view: 'overview' },
    },
    {
      title: 'Tickets + triage',
      body: 'Use the Tickets pane to drill into P0/P1 issues, review context, and confirm completion evidence.',
      action: { label: 'Open Tickets', view: 'tickets' },
    },
    {
      title: 'Modules + Ideas',
      body: 'Use Modules for GUI integrations and Ideas to capture product requests that auto-generate tickets.',
      action: { label: 'Open Modules', view: 'modules' },
    },
    {
      title: 'Settings + Logs',
      body: 'Use Settings for AI provider config and Logs to track recent events while you work.',
      action: { label: 'Open Settings', view: 'settings' },
    },
  ];

  const handleLogout = () => {
    clearAuthToken();
    setHasPassword(false);
    setActiveView('overview');
  };

  const handleLoginSuccess = () => {
    setHasPassword(true);
  };

  const openLoginModal = () => setShowLoginModal(true);

  useEffect(() => {
    const savedTheme = localStorage.getItem('actifix-theme') || 'dark';
    setTheme(savedTheme);
    document.documentElement.dataset.theme = savedTheme;
  }, []);

  useEffect(() => {
    if (!hasCompletedOnboarding()) {
      setShowOnboarding(true);
    }
  }, []);

  const toggleTheme = () => {
    const themeOrder = ['dark', 'portal', 'azure'];
    const currentIndex = themeOrder.indexOf(theme);
    const nextIndex = (currentIndex + 1) % themeOrder.length;
    const newTheme = themeOrder[nextIndex];
    setTheme(newTheme);
    localStorage.setItem('actifix-theme', newTheme);
    document.documentElement.dataset.theme = newTheme;
  };

  useEffect(() => {
    return () => {
      if (logFlashTimer.current) {
        clearTimeout(logFlashTimer.current);
      }
    };
  }, []);

  const triggerLogFlash = () => {
    setLogAlert(true);
    if (logFlashTimer.current) {
      clearTimeout(logFlashTimer.current);
    }
    logFlashTimer.current = setTimeout(() => {
      setLogAlert(false);
    }, 4200);
  };

  const openOnboarding = () => {
    setOnboardingStep(0);
    setShowOnboarding(true);
  };

  const closeOnboarding = () => {
    markOnboardingCompleted();
    setShowOnboarding(false);
  };

  const handleOnboardingNext = () => {
    if (onboardingStep + 1 >= onboardingSteps.length) {
      closeOnboarding();
    } else {
      setOnboardingStep((current) => Math.min(current + 1, onboardingSteps.length - 1));
    }
  };

  const handleOnboardingBack = () => {
    setOnboardingStep((current) => Math.max(current - 1, 0));
  };

  const handleOnboardingNavigate = (view) => {
    if (view) {
      setActiveView(view);
    }
  };

  const handleFix = async () => {
    if (isFixing || !hasPassword) return;
    setIsFixing(true);
    setFixStatus('Checking tickets…');

    try {
      const headers = buildAdminHeaders();
      const statsResp = await fetch(`${API_BASE}/tickets?limit=1`, { headers });
      const statsData = await statsResp.json();
      if (!statsResp.ok || !statsData || (statsData.total_open || 0) <= 0) {
        setFixStatus('No open tickets to fix');
        setIsFixing(false);
        return;
      }
    } catch (err) {
      setFixStatus(`Error: ${err.message}`);
      setIsFixing(false);
      return;
    }
    
    setFixStatus('Fixing the highest priority ticket…');
    triggerLogFlash();

    try {
      const headers = buildAdminHeaders({ 'Content-Type': 'application/json' });
      
      const response = await fetch(`${API_BASE}/fix-ticket`, {
        method: 'POST',
        headers,
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.reason || `HTTP ${response.status}`);
      }

      if (data.processed) {
        setFixStatus(data.action || `Resolved ${data.ticket_id}`);
      } else {
        const reasonMap = {
          no_open_tickets: 'No open tickets available',
          mark_failed: 'Unable to close the ticket',
        };
        const reasonMessage = reasonMap[data.reason] || data.reason || 'No action taken';
        setFixStatus(`Standby: ${reasonMessage}`);
      }
    } catch (error) {
      setFixStatus(`Error: ${error.message}`);
    } finally {
      setIsFixing(false);
    }
  };

  const renderView = () => {
    switch (activeView) {
      case 'tickets': return h(TicketsView, { hasPassword });
      case 'quiz': return h(QuizView);
      case 'logs': return h(LogsView);
      case 'system': return h(SystemView);
      case 'modules': return h(ModulesView, { hasPassword });
      case 'ideas': return h(IdeasView, { hasPassword });
      case 'settings': return h(SettingsView, { hasPassword });
      default: return h(OverviewView);
    }
  };

  return h('div', { className: 'dashboard' },
    h(NavigationRail, { activeView, onViewChange: setActiveView, logAlert }),
    h(Header, { onFix: handleFix, isFixing, fixStatus, theme, onToggleTheme: toggleTheme, onLogout: handleLogout, onOpenOnboarding: openOnboarding, hasPassword, onLoginClick: openLoginModal }),
    h('main', { className: 'dashboard-content' },
      renderView()
    ),
    h(Footer),
    showLoginModal && h(LoginModal, { onClose: () => setShowLoginModal(false), onSuccess: handleLoginSuccess }),
    showOnboarding && h(OnboardingModal, {
      step: onboardingSteps[onboardingStep],
      stepIndex: onboardingStep,
      totalSteps: onboardingSteps.length,
      onNext: handleOnboardingNext,
      onBack: handleOnboardingBack,
      onSkip: closeOnboarding,
      onNavigate: handleOnboardingNavigate,
    })
  );
};

// Render App
const rootEl = document.getElementById('root');
ReactDOM.createRoot(rootEl).render(h(App));
