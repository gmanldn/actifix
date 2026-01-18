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
const TICKET_REFRESH_INTERVAL = 4000;
const TICKET_LIMIT = 250;

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

const normalizePriority = (priority) => (
  PRIORITY_ORDER.includes(priority) ? priority : 'P4'
);

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
    const fetchData = async () => {
      try {
        const response = await fetch(`${API_BASE}${endpoint}`, { cache: 'no-store' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const json = await response.json();
        setData(json);
        setError(null);
        setLastUpdated(new Date());
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

  return { data, loading, error, lastUpdated };
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
  { id: 'ideas', icon: '💡', label: 'Ideas' },
  { id: 'settings', icon: '🔧', label: 'Settings' },
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
const [prevVersion, setPrevVersion] = useState(null);
const firstVersionCheck = useRef(true);
const { data, loading } = useFetch('/version', REFRESH_INTERVAL);
  const version = data?.version || '—';

  useEffect(() => {
    if (loading) return;
    if (firstVersionCheck.current) {
      firstVersionCheck.current = false;
      setPrevVersion(version);
      return;
    }
    if (version !== prevVersion) {
      console.log(`Detected version change ${prevVersion} -> ${version}; reloading page.`);
      window.location.reload();
      setPrevVersion(version);
    }
  }, [version, loading]);

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
      backgroundColor: 'var(--accent)',
      borderColor: '#000',
      color: '#000',
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
const Header = ({ onFix, isFixing, fixStatus, theme, onToggleTheme }) => {
  const [connected, setConnected] = useState(false);
  const [time, setTime] = useState(new Date().toLocaleTimeString());
  const { data: health } = useFetch('/health', REFRESH_INTERVAL);
  // Search query for the dashboard.
  const [search, setSearch] = useState('');
  const handleSearchChange = (e) => setSearch(e.target.value);

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
        onClick: onToggleTheme,
        title: `Switch to ${theme === 'dark' ? 'Azure light' : 'Dark'} theme`,
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
            `${metrics.open_tickets ?? 0} open • ${metrics.completed_tickets ?? 0} done`
          )
        )
      ),
      tickets?.tickets && tickets.tickets.length > 0 ? h('div', { className: 'ticket-list' },
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

  const [selectedTicket, setSelectedTicket] = useState(null);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState('');

  const fetchTicket = async (ticketId) => {
    setModalLoading(true);
    setModalError('');
    try {
      const response = await fetch(`${API_BASE}/ticket/${ticketId}`);
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
  const groupedTickets = groupTicketsByPriority(tickets);
  const updatedLabel = lastUpdated
    ? lastUpdated.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : '—';

  const renderTicketCard = (ticket, index) => {
    const priority = normalizePriority(ticket.priority);
    return h('article', { 
      key: ticket.ticket_id || index, 
      className: `ticket-card ${ticket.status}`,
      onClick: () => fetchTicket(ticket.ticket_id),
      style: { cursor: 'pointer' }
    },
      h('div', { className: 'ticket-card-header' },
        h('span', { className: `priority-badge ${priority.toLowerCase()}` }, priority),
        h('span', { className: `status-badge ${ticket.status}` }, ticket.status),
        h('span', { className: 'ticket-id' }, ticket.ticket_id?.slice(0, 10) || 'N/A')
      ),
      h('div', { className: 'ticket-card-title' }, ticket.error_type || 'Unknown'),
      h('div', { className: 'ticket-card-message' }, ticket.message || ''),
      h('div', { className: 'ticket-card-meta' },
        h('span', null, '📁 ', ticket.source || 'unknown'),
        h('span', null, '⏱ ', formatRelativeTime(ticket.created))
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
    tickets.length > 0 ? h('div', { className: 'priority-lanes' },
      PRIORITY_ORDER.map((priority) => {
        const group = groupedTickets[priority];
        const openTickets = group?.open || [];
        const completedTickets = group?.completed || [];
        const label = PRIORITY_LABELS[priority] || 'Priority';

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
    if (!selectedTicket && !modalLoading && !modalError) return null;

    const backdropStyle = {
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0,0,0,0.8)',
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
            selectedTicket.completion_notes && h('div', { style: fieldStyle },
              h('strong', null, 'Notes: '), selectedTicket.completion_notes
            ),
            selectedTicket.test_steps && h('div', { style: fieldStyle },
              h('strong', null, 'Test Steps: '), selectedTicket.test_steps
            ),
            selectedTicket.test_results && h('div', { style: fieldStyle },
              h('strong', null, 'Test Results: '), selectedTicket.test_results
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
        ...((health.warnings || []).map(w => h('li', { className: 'health-warning' }, w))),
        ...((health.errors || []).map(e => h('li', { className: 'health-error' }, e)))
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
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const { data: aiStatus } = useFetch('/ai-status', 8000);
  const { data: systemInfo } = useFetch('/system', 10000);

  // Load current settings
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const response = await fetch(`${API_BASE}/settings`);
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
      const response = await fetch(`${API_BASE}/settings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ai_provider: aiProvider,
          ai_api_key: aiApiKey,
          ai_model: aiModel,
          ai_enabled: aiEnabled,
        }),
      });

      if (response.ok) {
        setMessage('Settings saved successfully!');
        setTimeout(() => setMessage(''), 3000);
      } else {
        const data = await response.json();
        setMessage(`Error: ${data.error || 'Failed to save settings'}`);
      }
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
        h('div', { className: 'settings-actions' },
          h('button', {
            className: 'btn btn-primary',
            onClick: handleSave,
            disabled: saving,
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

  const handleToggle = async (moduleId) => {
    try {
      const response = await fetch(`${API_BASE}/modules/${moduleId}`, { method: 'POST' });
      if (response.ok) {
        setRefreshKey((rk) => rk + 1);
      } else {
        console.error('Toggle failed:', await response.text());
      }
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

  const renderModuleTable = (title, modules, icon) => {
    const sortedModules = sortModules(modules);
    return h('div', { className: 'panel' },
      h('div', { className: 'panel-header' },
        h('div', { className: 'panel-title' },
          h('span', { className: 'panel-title-icon' }, icon),
          title
        ),
        h('span', { className: 'text-muted', style: { fontSize: '10px' } }, `${sortedModules.length} modules`),
        h('span', { className: 'text-dim', style: { fontSize: '9px' } }, `Sorted: ${sortBy} ${sortDir.toUpperCase()}`)
      ),
      modules.length === 0 ?
        h('div', { className: 'module-empty' }, 'No modules') :
        h('div', { className: 'modules-table' },
          h('div', { className: 'table-header' },
            h('div', { className: 'table-cell name', onClick: () => handleSort('name'), title: 'Click to sort' }, 'Name', sortIndicator('name')),
            h('div', { className: 'table-cell domain', onClick: () => handleSort('domain'), title: 'Click to sort' }, 'Domain', sortIndicator('domain')),
            h('div', { className: 'table-cell owner', onClick: () => handleSort('owner'), title: 'Click to sort' }, 'Owner', sortIndicator('owner')),
            h('div', { className: 'table-cell status', onClick: () => handleSort('status'), title: 'Click to sort' }, 'Status', sortIndicator('status')),
            h('div', { className: 'table-cell actions' }, 'Actions'),
            h('div', { className: 'table-cell summary', onClick: () => handleSort('summary'), title: 'Click to sort' }, 'Summary', sortIndicator('summary'))
          ),
          sortedModules.map((m, idx) =>
            h('div', { key: `${title}-${idx}`, className: 'table-row' },
              h('div', { className: 'table-cell name truncate' }, m.name || '—'),
              h('div', { className: 'table-cell domain truncate' }, m.domain || '—'),
              h('div', { className: 'table-cell owner truncate' }, m.owner || '—'),
              h('div', { className: 'table-cell status' },
                h('span', { className: `status-badge ${m.status || 'active'}` }, m.status || 'active')
              ),
              h('div', { className: 'table-cell actions' },
                h('button', {
                  className: `btn-small ${m.status === 'disabled' ? 'btn-success' : 'btn-warning'}`,
                  onClick: () => handleToggle(m.name),
                  title: `Toggle ${m.name}`
                }, m.status === 'disabled' ? 'Enable' : 'Disable')
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

// Ideas View Component
const IdeasView = () => {
  const [idea, setIdea] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  const submitIdea = async () => {
    if (!idea.trim()) return;
    setLoading(true);
    setErrorMsg('');
    setResult(null);
    try {
      const response = await fetch(`${API_BASE}/ideas`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea: idea.trim() })
      });
      const data = await response.json();
      if (response.ok) {
        setResult(data);
      } else {
        setErrorMsg(data.error || 'Failed to generate ticket');
      }
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
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

// Main App Component
const App = () => {
  const [activeView, setActiveView] = useState('overview');
  const [isFixing, setIsFixing] = useState(false);
  const [fixStatus, setFixStatus] = useState('Ready to fix the next ticket');
  const [logAlert, setLogAlert] = useState(false);
  const [theme, setTheme] = useState('dark');
  const logFlashTimer = useRef(null);

  useEffect(() => {
    const savedTheme = localStorage.getItem('actifix-theme') || 'dark';
    setTheme(savedTheme);
    document.documentElement.dataset.theme = savedTheme;
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'azure' : 'dark';
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

  const handleFix = async () => {
    if (isFixing) return;
    setIsFixing(true);
    setFixStatus('Checking tickets…');
    
    try {
      const statsResp = await fetch(`${API_BASE}/tickets?limit=1`);
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
      case 'ideas': return h(IdeasView);
      case 'settings': return h(SettingsView);
      default: return h(OverviewView);
    }
  };

  return h('div', { className: 'dashboard' },
    h(NavigationRail, { activeView, onViewChange: setActiveView, logAlert }),
    h(Header, { onFix: handleFix, isFixing, fixStatus, theme, onToggleTheme: toggleTheme }),
    h('main', { className: 'dashboard-content' },
      renderView()
    ),
    h(Footer)
  );
};

// Render App
const rootEl = document.getElementById('root');
ReactDOM.createRoot(rootEl).render(h(App));