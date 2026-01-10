/**
 * Actifix Dashboard - Modern blade-based UI
 * 
 * Features:
 * - System Information Blade
 * - App Stats & Health Blade
 * - Ticket Summary Blade
 * - Master Logging Blade
 */

const { useState, useEffect, useRef, createElement: h } = React;

// API Configuration
const API_BASE = 'http://localhost:5001/api';
const REFRESH_INTERVAL = 5000; // 5 seconds

// ============================================================================
// Utility Functions
// ============================================================================

const formatTime = (isoString) => {
  if (!isoString) return 'N/A';
  const date = new Date(isoString);
  return date.toLocaleTimeString();
};

const formatDateTime = (isoString) => {
  if (!isoString) return 'N/A';
  const date = new Date(isoString);
  return date.toLocaleString();
};

const getPriorityColor = (priority) => {
  const colors = {
    'P0': '#ff4444',
    'P1': '#ff8800',
    'P2': '#ffcc00',
    'P3': '#88cc00',
  };
  return colors[priority] || '#888888';
};

const getStatusColor = (status) => {
  const colors = {
    'OK': '#00cc66',
    'WARNING': '#ffcc00',
    'ERROR': '#ff4444',
    'SLA_BREACH': '#ff8800',
  };
  return colors[status] || '#888888';
};

const getLogLevelColor = (level) => {
  const colors = {
    'ERROR': '#ff4444',
    'WARNING': '#ffcc00',
    'SUCCESS': '#00cc66',
    'INFO': '#888888',
  };
  return colors[level] || '#888888';
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

// Blade Container Component
const Blade = ({ title, icon, children, className = '', fullWidth = false }) => {
  return h('div', { className: `blade ${className} ${fullWidth ? 'blade-full' : ''}` },
    h('div', { className: 'blade-header' },
      h('span', { className: 'blade-icon' }, icon),
      h('h2', { className: 'blade-title' }, title)
    ),
    h('div', { className: 'blade-content' }, children)
  );
};

// Status Indicator Component
const StatusIndicator = ({ status, size = 'medium' }) => {
  const color = getStatusColor(status);
  return h('div', { 
    className: `status-indicator status-${size}`,
    style: { 
      backgroundColor: color,
      boxShadow: `0 0 12px ${color}`,
    }
  });
};

// Metric Card Component
const MetricCard = ({ label, value, subvalue, color }) => {
  return h('div', { className: 'metric-card' },
    h('div', { className: 'metric-value', style: color ? { color } : {} }, value),
    h('div', { className: 'metric-label' }, label),
    subvalue && h('div', { className: 'metric-subvalue' }, subvalue)
  );
};

// Priority Badge Component
const PriorityBadge = ({ priority }) => {
  return h('span', { 
    className: 'priority-badge',
    style: { 
      backgroundColor: getPriorityColor(priority),
      color: priority === 'P2' || priority === 'P3' ? '#000' : '#fff',
    }
  }, priority);
};

// Status Badge Component
const StatusBadge = ({ status }) => {
  const isOpen = status === 'open';
  return h('span', { 
    className: `status-badge ${isOpen ? 'status-open' : 'status-completed'}`
  }, isOpen ? 'OPEN' : 'DONE');
};

// Loading Spinner Component
const LoadingSpinner = () => {
  return h('div', { className: 'loading-spinner' },
    h('div', { className: 'spinner' })
  );
};

// Error Display Component
const ErrorDisplay = ({ message }) => {
  return h('div', { className: 'error-display' },
    h('span', { className: 'error-icon' }, '⚠'),
    h('span', null, message)
  );
};

// ============================================================================
// Blade Components
// ============================================================================

// System Information Blade
const SystemInfoBlade = () => {
  const { data, loading, error } = useFetch('/system');

  if (loading) return h(Blade, { title: 'System Information', icon: '🖥️' }, h(LoadingSpinner));
  if (error) return h(Blade, { title: 'System Information', icon: '🖥️' }, h(ErrorDisplay, { message: error }));

  const { platform, project, server, resources } = data || {};

  return h(Blade, { title: 'System Information', icon: '🖥️' },
    h('div', { className: 'info-grid' },
      h('div', { className: 'info-section' },
        h('h3', null, 'Platform'),
        h('div', { className: 'info-row' },
          h('span', { className: 'info-label' }, 'OS'),
          h('span', { className: 'info-value' }, `${platform?.system || 'N/A'} ${platform?.release || ''}`)
        ),
        h('div', { className: 'info-row' },
          h('span', { className: 'info-label' }, 'Machine'),
          h('span', { className: 'info-value' }, platform?.machine || 'N/A')
        ),
        h('div', { className: 'info-row' },
          h('span', { className: 'info-label' }, 'Python'),
          h('span', { className: 'info-value' }, platform?.python_version || 'N/A')
        )
      ),
      h('div', { className: 'info-section' },
        h('h3', null, 'Server'),
        h('div', { className: 'info-row' },
          h('span', { className: 'info-label' }, 'Uptime'),
          h('span', { className: 'info-value uptime' }, server?.uptime || 'N/A')
        ),
        h('div', { className: 'info-row' },
          h('span', { className: 'info-label' }, 'Started'),
          h('span', { className: 'info-value' }, formatTime(server?.start_time))
        )
      ),
      resources?.memory && h('div', { className: 'info-section' },
        h('h3', null, 'Resources'),
        h('div', { className: 'info-row' },
          h('span', { className: 'info-label' }, 'Memory'),
          h('span', { className: 'info-value' }, `${resources.memory.used_gb}/${resources.memory.total_gb} GB (${resources.memory.percent}%)`)
        ),
        resources.cpu_percent !== null && h('div', { className: 'info-row' },
          h('span', { className: 'info-label' }, 'CPU'),
          h('span', { className: 'info-value' }, `${resources.cpu_percent}%`)
        )
      ),
      h('div', { className: 'info-section' },
        h('h3', null, 'Project'),
        h('div', { className: 'info-row project-path' },
          h('span', { className: 'info-label' }, 'Root'),
          h('span', { className: 'info-value mono' }, project?.root || 'N/A')
        )
      )
    )
  );
};

// App Stats & Health Blade
const HealthStatsBlade = () => {
  const { data, loading, error } = useFetch('/health');

  if (loading) return h(Blade, { title: 'Health & Statistics', icon: '📊' }, h(LoadingSpinner));
  if (error) return h(Blade, { title: 'Health & Statistics', icon: '📊' }, h(ErrorDisplay, { message: error }));

  const { healthy, status, metrics, filesystem, warnings, errors: healthErrors } = data || {};

  return h(Blade, { title: 'Health & Statistics', icon: '📊' },
    h('div', { className: 'health-header' },
      h(StatusIndicator, { status, size: 'large' }),
      h('div', { className: 'health-status' },
        h('span', { className: 'health-status-text', style: { color: getStatusColor(status) } }, status),
        h('span', { className: 'health-status-sub' }, healthy ? 'System Healthy' : 'Issues Detected')
      )
    ),
    h('div', { className: 'metrics-grid' },
      h(MetricCard, { 
        label: 'Open Tickets', 
        value: metrics?.open_tickets || 0,
        color: metrics?.open_tickets > 0 ? '#ffcc00' : '#00cc66'
      }),
      h(MetricCard, { 
        label: 'Completed', 
        value: metrics?.completed_tickets || 0,
        color: '#00cc66'
      }),
      h(MetricCard, { 
        label: 'SLA Breaches', 
        value: metrics?.sla_breaches || 0,
        color: metrics?.sla_breaches > 0 ? '#ff4444' : '#00cc66'
      }),
      h(MetricCard, { 
        label: 'Oldest Ticket', 
        value: `${metrics?.oldest_ticket_age_hours || 0}h`,
        subvalue: 'age'
      })
    ),
    h('div', { className: 'filesystem-status' },
      h('div', { className: `fs-indicator ${filesystem?.files_exist ? 'fs-ok' : 'fs-error'}` },
        h('span', null, filesystem?.files_exist ? '✓' : '✗'),
        ' Files Exist'
      ),
      h('div', { className: `fs-indicator ${filesystem?.files_writable ? 'fs-ok' : 'fs-error'}` },
        h('span', null, filesystem?.files_writable ? '✓' : '✗'),
        ' Writable'
      )
    ),
    (warnings?.length > 0 || healthErrors?.length > 0) && h('div', { className: 'health-alerts' },
      healthErrors?.map((err, i) => h('div', { key: `err-${i}`, className: 'alert alert-error' }, '✗ ', err)),
      warnings?.map((warn, i) => h('div', { key: `warn-${i}`, className: 'alert alert-warning' }, '⚠ ', warn))
    )
  );
};

// Ticket Summary Blade
const TicketsBlade = () => {
  const { data, loading, error } = useFetch('/tickets');

  if (loading) return h(Blade, { title: 'Recent Tickets', icon: '🎫' }, h(LoadingSpinner));
  if (error) return h(Blade, { title: 'Recent Tickets', icon: '🎫' }, h(ErrorDisplay, { message: error }));

  const { tickets, total_open, total_completed } = data || { tickets: [] };

  return h(Blade, { title: 'Recent Tickets', icon: '🎫' },
    h('div', { className: 'tickets-summary' },
      h('span', { className: 'ticket-count open' }, `${total_open || 0} open`),
      h('span', { className: 'ticket-divider' }, '•'),
      h('span', { className: 'ticket-count completed' }, `${total_completed || 0} completed`)
    ),
    tickets?.length > 0 ? h('div', { className: 'tickets-list' },
      tickets.slice(0, 10).map((ticket, i) => 
        h('div', { key: ticket.ticket_id || i, className: 'ticket-item' },
          h('div', { className: 'ticket-header' },
            h(PriorityBadge, { priority: ticket.priority }),
            h(StatusBadge, { status: ticket.status }),
            h('span', { className: 'ticket-id' }, ticket.ticket_id?.slice(0, 8) || 'N/A')
          ),
          h('div', { className: 'ticket-type' }, ticket.error_type || 'Unknown'),
          h('div', { className: 'ticket-message' }, ticket.message || ''),
          h('div', { className: 'ticket-meta' },
            h('span', { className: 'ticket-source' }, ticket.source || ''),
            h('span', { className: 'ticket-time' }, formatTime(ticket.created))
          )
        )
      )
    ) : h('div', { className: 'no-tickets' }, 'No tickets found')
  );
};

// Master Logging Blade
const LoggingBlade = () => {
  const [logType, setLogType] = useState('audit');
  const [autoScroll, setAutoScroll] = useState(true);
  const [filter, setFilter] = useState('');
  const logContainerRef = useRef(null);
  
  const { data, loading, error } = useFetch(`/logs?type=${logType}&lines=200`, 3000);

  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [data, autoScroll]);

  const logTypes = [
    { id: 'audit', label: 'Audit Log' },
    { id: 'errors', label: 'Error Rollup' },
    { id: 'list', label: 'Ticket List' },
    { id: 'setup', label: 'Setup Log' },
  ];

  const filteredLogs = data?.content?.filter(log => {
    if (!filter) return true;
    return log.text.toLowerCase().includes(filter.toLowerCase());
  }) || [];

  return h(Blade, { title: 'Master Logging', icon: '📜', fullWidth: true, className: 'logging-blade' },
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
      h('div', { className: 'log-actions' },
        h('input', {
          type: 'text',
          className: 'log-filter',
          placeholder: 'Filter logs...',
          value: filter,
          onChange: (e) => setFilter(e.target.value)
        }),
        h('button', {
          className: `auto-scroll-btn ${autoScroll ? 'active' : ''}`,
          onClick: () => setAutoScroll(!autoScroll),
          title: autoScroll ? 'Auto-scroll ON' : 'Auto-scroll OFF'
        }, '↓')
      )
    ),
    h('div', { className: 'log-info' },
      h('span', null, `File: ${data?.file || 'N/A'}`),
      h('span', null, `Lines: ${filteredLogs.length}/${data?.total_lines || 0}`)
    ),
    loading && !data ? h(LoadingSpinner) :
    error ? h(ErrorDisplay, { message: error }) :
    h('div', { className: 'log-container', ref: logContainerRef },
      filteredLogs.length > 0 ? filteredLogs.map((log, i) =>
        h('div', { 
          key: i, 
          className: `log-line log-${log.level.toLowerCase()}`
        },
          h('span', { 
            className: 'log-level-indicator',
            style: { backgroundColor: getLogLevelColor(log.level) }
          }),
          h('span', { className: 'log-text' }, log.text)
        )
      ) : h('div', { className: 'no-logs' }, 'No log entries found')
    )
  );
};

// Header Component
const Header = () => {
  const [connected, setConnected] = useState(false);

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

  return h('header', { className: 'dashboard-header' },
    h('div', { className: 'header-left' },
      h('img', { src: './assets/pangolin.svg', alt: 'Actifix', className: 'header-logo' }),
      h('div', { className: 'header-title' },
        h('h1', null, 'ACTIFIX'),
        h('span', { className: 'header-subtitle' }, 'Error Tracking Dashboard')
      )
    ),
    h('div', { className: 'header-right' },
      h('div', { className: `connection-status ${connected ? 'connected' : 'disconnected'}` },
        h('span', { className: 'connection-dot' }),
        h('span', null, connected ? 'API Connected' : 'API Disconnected')
      ),
      h('span', { className: 'header-time' }, new Date().toLocaleTimeString())
    )
  );
};

// Main App Component
const App = () => {
  const [time, setTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return h('div', { className: 'dashboard' },
    h(Header),
    h('main', { className: 'dashboard-content' },
      h('div', { className: 'blade-grid' },
        h(SystemInfoBlade),
        h(HealthStatsBlade),
        h(TicketsBlade)
      ),
      h(LoggingBlade)
    ),
    h('footer', { className: 'dashboard-footer' },
      h('span', null, '© 2026 Actifix'),
      h('span', null, `Last updated: ${time}`)
    )
  );
};

// Render the app
const rootEl = document.getElementById('root');
ReactDOM.createRoot(rootEl).render(h(App));
