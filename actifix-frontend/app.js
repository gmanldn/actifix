/**
 * Actifix Dashboard - COMPACT & ELEGANT 2026 Edition
 * 
 * Redesigned for maximum information density with modern aesthetics
 */

const { useState, useEffect, useRef, createElement: h } = React;

// API Configuration
const API_BASE = 'http://localhost:5001/api';
const REFRESH_INTERVAL = 5000;
const LOG_REFRESH_INTERVAL = 3000;

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

// ============================================================================
// Custom Hooks
// ============================================================================

const useFetch = (endpoint, interval = REFRESH_INTERVAL) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`${API_BASE}${endpoint}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const json = await response.json();
        setData(json);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const timer = setInterval(fetchData, interval);
    return () => clearInterval(timer);
  }, [endpoint, interval]);

  return { data, loading, error };
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
    { id: 'logs', icon: '📜', label: 'Logs' },
    { id: 'system', icon: '⚙️', label: 'System' },
    { id: 'modules', icon: '🧩', label: 'Modules' },
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
          ].join(' ').trim(),
          onClick: () => onViewChange(item.id),
          title: item.label
        }, item.icon)
      )
    )
  );
};

const VersionBadge = () => {
  const { data, loading } = useFetch('/version', 60000);
  const version = data?.version || '—';
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
    style: {
      borderColor: accentColor,
      color: accentColor,
    }
  },
    h('span', { className: 'version-label' }, `v${version}`),
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
const Header = ({ onFix, isFixing, fixStatus }) => {
  const [connected, setConnected] = useState(false);
  const [time, setTime] = useState(new Date().toLocaleTimeString());
  const { data: health } = useFetch('/health', 10000);

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await fetch(`${API_BASE}/ping`);
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
      h('div', { className: 'header-stats' },
        h('div', { className: 'stat-card', style: { padding: '4px 12px', minWidth: '60px' } },
          h('div', { className: 'stat-value', style: { fontSize: '16px' } }, health?.metrics?.open_tickets ?? '—'),
          h('div', { className: 'stat-label', style: { fontSize: '9px' } }, 'OPEN')
        ),
        h('div', { className: 'stat-card', style: { padding: '4px 12px', minWidth: '60px' } },
          h('div', { className: 'stat-value', style: { fontSize: '16px' } }, health?.metrics?.completed_tickets ?? '—'),
          h('div', { className: 'stat-label', style: { fontSize: '9px' } }, 'DONE')
        ),
        h('div', { className: `connection-status ${connected ? 'connected' : 'disconnected'}` },
          h('span', { className: 'connection-dot' }),
          h('span', null, connected ? 'API ' : 'OFF')
        )
      ),
      h(FixToolbar, { onFix, isFixing, status: fixStatus }),
      h(VersionBadge),
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
    trend && h('div', { className: 'metric-tile-trend' }, trend)
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
        label: 'SLA BREACHES',
        value: metrics.sla_breaches ?? 0,
        icon: '⚡',
        color: metrics.sla_breaches > 0 ? '#ef4444' : '#10b981',
        subvalue: metrics.sla_breaches > 0 ? 'Action Required!' : 'All Good'
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

    // Recent Tickets Panel
    h('div', { className: 'panel' },
      h('div', { className: 'panel-header' },
        h('div', { className: 'panel-title' },
          h('span', { className: 'panel-title-icon' }, '🎫'),
          'RECENT TICKETS'
        ),
        h('div', { className: 'panel-actions' },
          h('span', { className: 'text-muted', style: { fontSize: '11px' } },
            `${tickets?.total_open ?? 0} open • ${tickets?.total_completed ?? 0} done`
          )
        )
      ),
      tickets?.tickets && tickets.tickets.length > 0 ? h('div', { className: 'ticket-list' },
        tickets.tickets.slice(0, 15).map((ticket, i) =>
          h('div', { key: ticket.ticket_id || i, className: 'ticket-item' },
            h('div', { className: 'ticket-item-header' },
              h('span', {
                className: `priority-badge ${ticket.priority.toLowerCase()}`
              }, ticket.priority),
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
          )
        )
      ) : h('div', { style: { padding: '24px', textAlign: 'center', color: 'var(--text-dim)' } }, 'No tickets found')
    )
  );
};

// Tickets View Component
const TicketsView = () => {
  const { data, loading, error } = useFetch('/tickets');

  if (loading) return h(LoadingSpinner);
  if (error) return h(ErrorDisplay, { message: error });

  const tickets = data?.tickets || [];

  return h('div', { className: 'panel' },
    h('div', { className: 'panel-header' },
      h('div', { className: 'panel-title' },
        h('span', { className: 'panel-title-icon' }, '🎫'),
        'ALL TICKETS'
      ),
      h('div', { className: 'panel-actions' },
        h('span', { className: 'text-muted', style: { fontSize: '11px' } },
          `${data?.total_open ?? 0} open • ${data?.total_completed ?? 0} completed`
        )
      )
    ),
    tickets.length > 0 ? h('div', { className: 'ticket-list' },
      tickets.map((ticket, i) =>
        h('div', { key: ticket.ticket_id || i, className: 'ticket-item' },
          h('div', { className: 'ticket-item-header' },
            h('span', {
              className: `priority-badge ${ticket.priority.toLowerCase()}`
            }, ticket.priority),
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
            h('span', null, '📁 ', ticket.source || 'unknown'),
            h('span', null, '🏷️ ', ticket.created ? formatTime(ticket.created) : 'N/A')
          )
        )
      )
    ) : h('div', { style: { padding: '24px', textAlign: 'center', color: 'var(--text-dim)' } }, 'No tickets found')
  );
};

// Logs View Component
const LogsView = () => {
  const [logType, setLogType] = useState('audit');
  const [autoScroll, setAutoScroll] = useState(true);
  const [filter, setFilter] = useState('');
  const logContainerRef = useRef(null);

  const { data, loading, error } = useFetch(`/logs?type=${logType}&lines=300`, LOG_REFRESH_INTERVAL);

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

  const filteredLogs = data?.content?.filter(log => {
    if (!filter) return true;
    return log.text.toLowerCase().includes(filter.toLowerCase());
  }) || [];

  return h('div', { className: 'panel' },
    h('div', { className: 'panel-header' },
      h('div', { className: 'panel-title' },
        h('span', { className: 'panel-title-icon' }, '📜'),
        'LIVE LOGS'
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
      h('div', { style: { display: 'flex', gap: '8px', alignItems: 'center' } },
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

  return h('div', null,
    h('div', { className: 'stats-grid' },
      h(MetricTile, {
        label: 'PYTHON',
        value: platform.python_version?.split('.').slice(0, 2).join('.') || 'N/A',
        icon: '🐍',
        subvalue: platform.python_version || 'N/A'
      }),
      h(MetricTile, {
        label: 'SYSTEM',
        value: platform.system || 'N/A',
        icon: '💻',
        subvalue: platform.release || ''
      }),
      h(MetricTile, {
        label: 'MACHINE',
        value: platform.machine || 'N/A',
        icon: '⚙️'
      }),
      h(MetricTile, {
        label: 'UPTIME',
        value: server.uptime?.split(' ')[0] || 'N/A',
        icon: '⏰',
        subvalue: server.uptime || ''
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
      })
    ),
    
    h('div', { className: 'panel' },
      h('div', { className: 'panel-header' },
        h('div', { className: 'panel-title' },
          h('span', { className: 'panel-title-icon' }, '📋'),
          'SYSTEM DETAILS'
        )
      ),
      h('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' } },
        h('div', null,
          h('div', { className: 'stat-label', style: { marginBottom: '4px' } }, 'PROJECT ROOT'),
          h('div', { className: 'mono', style: { fontSize: '11px', color: 'var(--text-muted)', wordBreak: 'break-all' } }, project.root || 'N/A')
        ),
        h('div', null,
          h('div', { className: 'stat-label', style: { marginBottom: '4px' } }, 'ACTIFIX DIR'),
          h('div', { className: 'mono', style: { fontSize: '11px', color: 'var(--text-muted)', wordBreak: 'break-all' } }, project.actifix_dir || 'N/A')
        ),
        h('div', null,
          h('div', { className: 'stat-label', style: { marginBottom: '4px' } }, 'SERVER START'),
          h('div', { className: 'mono', style: { fontSize: '11px', color: 'var(--text-muted)' } }, server.start_time ? formatTime(server.start_time) : 'N/A')
        ),
        h('div', null,
          h('div', { className: 'stat-label', style: { marginBottom: '4px' } }, 'SNAPSHOT'),
          h('div', { className: 'mono', style: { fontSize: '11px', color: 'var(--text-muted)' } }, data?.timestamp ? formatTime(data.timestamp) : 'N/A')
        )
      )
    )
  );
};

// Modules View Component
const ModulesView = () => {
  const { data, loading, error } = useFetch('/modules', 15000);

  if (loading) return h(LoadingSpinner);
  if (error) return h(ErrorDisplay, { message: error });

  const systemModules = data?.system || [];
  const userModules = data?.user || [];

  const renderModuleGroup = (title, modules, icon) => (
    h('div', { className: 'panel' },
      h('div', { className: 'panel-header' },
        h('div', { className: 'panel-title' },
          h('span', { className: 'panel-title-icon' }, icon),
          title
        ),
        h('span', { className: 'text-muted', style: { fontSize: '11px' } }, `${modules.length} modules`)
      ),
      modules.length === 0 ?
        h('div', { style: { padding: '24px', textAlign: 'center', color: 'var(--text-dim)' } }, 'No modules') :
        h('div', { style: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px' } },
          modules.map((m, idx) =>
            h('div', {
              key: `${title}-${idx}`,
              style: {
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)',
                padding: '12px'
              }
            },
              h('div', { style: { fontWeight: 600, marginBottom: '4px', fontSize: '12px' } }, m.name || 'unknown'),
              h('div', { style: { fontSize: '10px', color: 'var(--text-dim)', marginBottom: '4px' } },
                `${m.domain || '—'} • ${m.owner || '—'}`
              ),
              m.summary && h('div', { style: { fontSize: '11px', color: 'var(--text-muted)', marginTop: '8px' } }, m.summary)
            )
          )
        )
    )
  );

  return h('div', null,
    renderModuleGroup('SYSTEM MODULES', systemModules, '⚙️'),
    renderModuleGroup('USER MODULES', userModules, '👤')
  );
};

// Main App Component
const App = () => {
  const [activeView, setActiveView] = useState('overview');
  const [isFixing, setIsFixing] = useState(false);
  const [fixStatus, setFixStatus] = useState('Ready to fix the next ticket');
  const [logAlert, setLogAlert] = useState(false);
  const logFlashTimer = useRef(null);

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

  const handleFix = async () => {
    if (isFixing) return;
    setIsFixing(true);
    setFixStatus('Fixing the highest priority ticket…');
    triggerLogFlash();

    try {
      const response = await fetch(`${API_BASE}/fix-ticket`, {
        method: 'POST',
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
      case 'tickets': return h(TicketsView);
      case 'logs': return h(LogsView);
      case 'system': return h(SystemView);
      case 'modules': return h(ModulesView);
      default: return h(OverviewView);
    }
  };

  return h('div', { className: 'dashboard' },
    h(NavigationRail, { activeView, onViewChange: setActiveView, logAlert }),
    h(Header, { onFix: handleFix, isFixing, fixStatus }),
    h('main', { className: 'dashboard-content' },
      renderView()
    ),
    h(Footer)
  );
};

// Render App
const rootEl = document.getElementById('root');
ReactDOM.createRoot(rootEl).render(h(App));
