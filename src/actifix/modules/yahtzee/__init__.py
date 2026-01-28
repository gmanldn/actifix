"""Yahtzee module with a localhost GUI for a two-player game."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, TYPE_CHECKING, Union

from actifix.log_utils import log_event
from actifix.raise_af import TicketPriority

from actifix.modules.base import ModuleBase

if TYPE_CHECKING:
    from flask import Blueprint

MODULE_DEFAULTS = {
    "host": "127.0.0.1",
    "port": 8090,
}
ACCESS_RULE = "local-only"
MODULE_METADATA = {
    "name": "modules.yahtzee",
    "version": "1.0.0",
    "description": "Two-player Yahtzee module with local GUI.",
    "capabilities": {
        "gui": True,
        "health": True,
    },
    "data_access": {
        "state_dir": True,
    },
    "network": {
        "external_requests": True,
    },
    "permissions": ["logging", "fs_read"],
}
MODULE_DEPENDENCIES = [
    "runtime.state",
    "infra.logging",
    "core.raise_af",
    "runtime.api",
]


def _module_helper(project_root: Optional[Union[str, Path]] = None) -> ModuleBase:
    """Build a ModuleBase helper for Yahtzee."""
    return ModuleBase(
        module_key="yahtzee",
        defaults=MODULE_DEFAULTS,
        metadata=MODULE_METADATA,
        project_root=project_root,
    )


def _resolve_module_config(
    project_root: Optional[Union[str, Path]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> tuple[str, int]:
    """Return the resolved host/port after applying overrides."""
    helper = _module_helper(project_root)
    return helper.resolve_host_port(host, port)


def create_blueprint(
    project_root: Optional[Union[str, Path]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    url_prefix: Optional[str] = "/modules/yahtzee",
) -> Blueprint:
    """Create the Flask blueprint that serves the Yahtzee GUI."""
    helper = _module_helper(project_root)
    try:
        from flask import Blueprint, Response  # Local import keeps Flask optional

        resolved_host, resolved_port = helper.resolve_host_port(host, port)
        blueprint = Blueprint("yahtzee", __name__, url_prefix=url_prefix)

        @blueprint.route("/")
        def index():
            return Response(_HTML_PAGE, mimetype="text/html")

        @blueprint.route("/health")
        def health():
            return helper.health_response()

        helper.log_gui_init(resolved_host, resolved_port)
        return blueprint
    except Exception as exc:
        helper.record_module_error(
            message=f"Failed to create Yahtzee blueprint: {exc}",
            source="modules/yahtzee/__init__.py:create_blueprint",
            error_type=type(exc).__name__,
            priority=TicketPriority.P2,
        )
        raise


def create_app(
    project_root: Optional[Union[str, Path]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> "Flask":
    """Create the Flask app that serves the Yahtzee GUI."""
    try:
        from flask import Flask  # Local import to keep optional dependency optional

        app = Flask(__name__)
        blueprint = create_blueprint(project_root=project_root, host=host, port=port, url_prefix=None)
        app.register_blueprint(blueprint)
        return app
    except Exception as exc:
        helper = _module_helper(project_root)
        helper.record_module_error(
            message=f"Failed to create Yahtzee GUI app: {exc}",
            source="modules/yahtzee/__init__.py:create_app",
            error_type=type(exc).__name__,
            priority=TicketPriority.P2,
        )
        raise


def run_gui(
    host: Optional[str] = None,
    port: Optional[int] = None,
    project_root: Optional[Union[str, Path]] = None,
    debug: bool = False,
) -> None:
    """Run the Yahtzee GUI on localhost."""
    helper = _module_helper(project_root)
    resolved_host, resolved_port = helper.resolve_host_port(host, port)
    try:
        app = create_app(project_root=project_root, host=resolved_host, port=resolved_port)
        log_event(
            "YAHTZEE_GUI_START",
            f"Yahtzee GUI running at http://{resolved_host}:{resolved_port}",
            extra={"host": resolved_host, "port": resolved_port, "module": "modules.yahtzee"},
            source="modules.yahtzee.run_gui",
        )
        # use_reloader=False suppresses Flask's banner output which can cause BrokenPipeError
        # when stdout is closed or redirected in certain environments
        app.run(host=resolved_host, port=resolved_port, debug=debug, use_reloader=False)
    except BrokenPipeError:
        # BrokenPipeError can occur when Flask tries to write its banner to a closed stdout
        # This is safe to ignore when the app is running in background/non-interactive mode
        helper.log_module_info(
            message="Yahtzee GUI started (stdout not available for banner)",
            source="modules/yahtzee/__init__.py:run_gui",
        )
    except Exception as exc:
        helper.record_module_error(
            message=f"Failed to start Yahtzee GUI: {exc}",
            source="modules/yahtzee/__init__.py:run_gui",
            error_type=type(exc).__name__,
            priority=TicketPriority.P1,
        )
        raise


_HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Yahtzee Module</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4f1e8;
      --panel: #fffaf0;
      --ink: #2c2a24;
      --accent: #c44f2c;
      --accent-2: #1c6e6a;
      --muted: #6f6b61;
      --border: #d6cfbf;
    }
    * {
      box-sizing: border-box;
    }
    body {
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", "Palatino", "Georgia", serif;
      background: radial-gradient(circle at top, #fff8e6, #f2efe2 60%, #e7e0cf);
      color: var(--ink);
    }
    .app {
      max-width: 1120px;
      margin: 0 auto;
      padding: 40px 24px 56px;
    }
    header {
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 20px;
    }
    h1 {
      font-family: "Copperplate", "Palatino Linotype", "Book Antiqua", "Palatino", serif;
      font-size: 42px;
      margin: 0;
      letter-spacing: 1.5px;
      text-transform: uppercase;
    }
    .subtitle {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 3px;
      color: var(--muted);
    }
    .port-display {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 2px;
      color: var(--accent-2);
      margin-top: 4px;
      font-family: "Oswald", sans-serif;
      font-weight: 600;
    }
    .port-display span {
      color: var(--ink);
      font-weight: 700;
    }
    h2 {
      font-family: "Copperplate", "Palatino Linotype", "Book Antiqua", "Palatino", serif;
      font-size: 20px;
      letter-spacing: 1px;
      margin-top: 0;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 22px;
      margin-top: 28px;
    }
    .card {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 22px;
      padding: 22px 24px;
      box-shadow: 0 12px 28px rgba(63, 52, 32, 0.1);
    }
    .setup input {
      width: 100%;
      padding: 10px 12px;
      border-radius: 10px;
      border: 1px solid var(--border);
      font-size: 16px;
      margin-top: 6px;
    }
    .setup input:focus {
      outline: none;
      border-color: var(--accent);
      box-shadow: 0 0 0 2px rgba(196, 79, 44, 0.2);
    }
    .button {
      appearance: none;
      border: none;
      padding: 10px 18px;
      border-radius: 999px;
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 1px;
      cursor: pointer;
      background: linear-gradient(135deg, #d25a2d, #b84a28);
      color: #fff7ed;
      box-shadow: 0 8px 16px rgba(196, 79, 44, 0.35);
      transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .button.secondary {
      background: linear-gradient(135deg, #1c6e6a, #155955);
      box-shadow: 0 8px 16px rgba(28, 110, 106, 0.3);
    }
    .button:hover:not([disabled]) {
      transform: translateY(-1px);
      box-shadow: 0 10px 18px rgba(44, 42, 36, 0.25);
    }
    .button:active:not([disabled]) {
      transform: translateY(1px);
    }
    .button[disabled] {
      opacity: 0.5;
      cursor: not-allowed;
      box-shadow: none;
    }
    .status {
      display: flex;
      flex-direction: column;
      gap: 10px;
      font-size: 15px;
    }
    .status strong {
      font-size: 20px;
    }
    .dice-row {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 10px;
    }
    .die {
      width: 72px;
      height: 72px;
      border-radius: 16px;
      border: 2px solid var(--border);
      background: linear-gradient(160deg, #ffffff, #efe7d6);
      font-size: 28px;
      font-weight: bold;
      color: var(--ink);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      position: relative;
      box-shadow: 0 8px 14px rgba(44, 42, 36, 0.15);
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .die:hover {
      transform: translateY(-2px);
      box-shadow: 0 10px 18px rgba(44, 42, 36, 0.2);
    }
    .die.held {
      border-color: var(--accent-2);
      background: linear-gradient(160deg, #e7f6f4, #cfe8e5);
      transform: translateY(-4px) rotate(-1deg);
    }
    .die.rolling {
      animation: roll-jitter 0.5s ease-in-out;
      box-shadow: 0 12px 18px rgba(196, 79, 44, 0.35);
    }
    .die span {
      position: absolute;
      bottom: 6px;
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--muted);
    }
    @keyframes roll-jitter {
      0% {
        transform: translateY(0) rotate(0deg);
      }
      20% {
        transform: translateY(-6px) rotate(-6deg);
      }
      40% {
        transform: translateY(2px) rotate(5deg);
      }
      60% {
        transform: translateY(-4px) rotate(-4deg);
      }
      80% {
        transform: translateY(1px) rotate(3deg);
      }
      100% {
        transform: translateY(0) rotate(0deg);
      }
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: #fffdf7;
      border-radius: 14px;
      overflow: hidden;
    }
    th, td {
      border-bottom: 1px solid var(--border);
      padding: 10px 8px;
      text-align: center;
      font-size: 14px;
    }
    th {
      text-transform: uppercase;
      font-size: 12px;
      letter-spacing: 1px;
      color: var(--muted);
      background: #f3ecdb;
    }
    td.category {
      text-align: left;
      font-weight: 600;
    }
    tbody tr:nth-child(even) {
      background: #fdf7ea;
    }
    tbody tr:hover {
      background: #f7f0df;
    }
    .score-btn {
      border: 1px dashed var(--accent);
      background: rgba(255, 255, 255, 0.6);
      padding: 6px 12px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 12px;
    }
    .score-btn[disabled] {
      opacity: 0.4;
      cursor: not-allowed;
    }
    .totals {
      display: flex;
      justify-content: space-between;
      margin-top: 12px;
      font-weight: bold;
    }
    .note {
      color: var(--muted);
      font-size: 13px;
      margin-top: 8px;
    }
    .session-actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 12px;
    }
    .session-status {
      margin-top: 10px;
      font-size: 13px;
      color: var(--accent-2);
      font-weight: 600;
    }
    .session-status.error {
      color: #b23b2f;
    }
    .session-share {
      margin-top: 6px;
      font-size: 12px;
      color: var(--ink);
      word-break: break-all;
    }

    /* Enhanced scorecard styles */
    tr.upper-row td {
      background: rgba(220, 240, 235, 0.4);
    }
    tr.lower-row td {
      background: rgba(255, 248, 220, 0.3);
    }
    .upper-total-row, .bonus-row {
      font-weight: bold;
      font-size: 15px;
      background: linear-gradient(135deg, var(--panel), #fff8e1);
    }
    .line-separator td {
      border: none;
      height: 16px;
      background: linear-gradient(to right, transparent 30%, var(--accent) 50%, transparent 70%);
      padding: 0;
    }
    .section-header td {
      text-align: center !important;
      font-weight: bold !important;
      padding: 12px 8px !important;
      background: linear-gradient(135deg, #f3ecdb, #e8d9b5) !important;
      text-transform: uppercase;
      letter-spacing: 1.2px;
      font-size: 13px;
      color: var(--accent) !important;
    }
  </style>
</head>
<body>
  <div class="app">
    <header>
      <div>
        <div class="subtitle">Actifix Module</div>
        <h1>Yahtzee</h1>
        <div class="port-display" id="portDisplay">Running on port <span id="portValue">8090</span></div>
      </div>
      <button id="resetBtn" class="button secondary">Reset Game</button>
    </header>

    <div class="grid">
      <section class="card setup">
        <h2>Players</h2>
        <label>Player 1
          <input id="playerOne" type="text" value="Player 1">
        </label>
        <label>Player 2
          <input id="playerTwo" type="text" value="Player 2">
        </label>
        <button id="startBtn" class="button">Start Game</button>
        <div class="note">Roll up to three times, hold dice between rolls, then score a category.</div>
      </section>

      <section class="card">
        <h2>Status</h2>
        <div class="status">
          <div><strong id="currentPlayer">Waiting to start</strong></div>
          <div>Rolls left: <span id="rollsLeft">3</span></div>
          <div>Turn: <span id="turnCount">1</span></div>
        </div>
        <div class="dice-row" id="diceRow"></div>
        <div class="note">Click a die to hold it after the first roll.</div>
        <div style="margin-top: 12px;">
          <button id="rollBtn" class="button">Roll Dice</button>
        </div>
      </section>

      <section class="card">
          <input id="sessionCode" type="text" placeholder="e.g. yhatzee-8k2l1p or paste.rs/yhatzee-8k2l1p">
>>>>>>> Stashed changes:src/actifix/modules/yahtzee/__init__.py
        </label>
        <h2>Session Sync</h2>
        <label>Session code
          <input id="sessionCode" type="text" placeholder="e.g. yahtzee-8k2l1p or paste.rs/yahtzee-8k2l1p">
        </label>
=======
          <input id="sessionCode" type="text" placeholder="e.g. yhatzee-8k2l1p or paste.rs/yhatzee-8k2l1p">
>>>>>>> Stashed changes:src/actifix/modules/yhatzee/__init__.py
        </label>
        <div class="session-actions">
          <button id="createSessionBtn" class="button secondary">Create Session</button>
          <button id="joinSessionBtn" class="button">Join Session</button>
        </div>
        <div class="session-status" id="sessionStatus">Not connected</div>
        <div class="session-share" id="sessionShare"></div>
        <div class="note">Uses free paste.rs sessions. Share the session code with your partner.</div>
      </section>
    </div>

    <section class="card" style="margin-top: 18px;">
      <h2>Score Sheet</h2>
      <div class="note">Upper section (Ones-Sixes subtotal &ge;63 pts) awards 35 bonus. Below: fixed scores. Select category for current player.</div>
      <table id="scoreTable">
        <thead>
          <tr>
            <th>Category</th>
            <th id="playerOneHeader">Player 1</th>
            <th id="playerTwoHeader">Player 2</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
      <div class="totals">
        <div id="totalOne">Player 1 Total: 0</div>
        <div id="totalTwo">Player 2 Total: 0</div>
      </div>
    </section>
  </div>

  <script>
    const categories = [
      { id: "ones", label: "Ones", score: dice => sumOf(dice, 1) },
      { id: "twos", label: "Twos", score: dice => sumOf(dice, 2) },
      { id: "threes", label: "Threes", score: dice => sumOf(dice, 3) },
      { id: "fours", label: "Fours", score: dice => sumOf(dice, 4) },
      { id: "fives", label: "Fives", score: dice => sumOf(dice, 5) },
      { id: "sixes", label: "Sixes", score: dice => sumOf(dice, 6) },
      { id: "three_kind", label: "Three of a kind", score: dice => hasOfKind(dice, 3) ? sum(dice) : 0 },
      { id: "four_kind", label: "Four of a kind", score: dice => hasOfKind(dice, 4) ? sum(dice) : 0 },
      { id: "full_house", label: "Full house", score: dice => isFullHouse(dice) ? 25 : 0 },
      { id: "small_straight", label: "Small straight", score: dice => isSmallStraight(dice) ? 30 : 0 },
      { id: "large_straight", label: "Large straight", score: dice => isLargeStraight(dice) ? 40 : 0 },
      { id: "yahtzee", label: "Yahtzee", score: dice => hasOfKind(dice, 5) ? 50 : 0 },
      { id: "chance", label: "Chance", score: dice => sum(dice) }
    ];

    const UPPER_THRESHOLD = 63;
    const BONUS_VALUE = 35;
    const upperCategoryIds = ['ones', 'twos', 'threes', 'fours', 'fives', 'sixes'];

    const state = {
      players: ["Player 1", "Player 2"],
      currentPlayer: 0,
      rollsLeft: 3,
      turn: 1,
      dice: [1, 1, 1, 1, 1],
      held: [false, false, false, false, false],
      scores: [
        Object.fromEntries(categories.map(cat => [cat.id, null])),
        Object.fromEntries(categories.map(cat => [cat.id, null]))
      ],
      started: false,
      updatedAt: Date.now(),
      rollingIndices: [],
      rollAnimationId: 0
    };

    const sync = {
      baseUrl: "https://paste.rs",
      sessionId: "",
      enabled: false,
      isHost: false,
      suppressPush: false,
      pushTimer: null,
      pollTimer: null,
      pollingMs: 3000
    };

    const diceRow = document.getElementById("diceRow");
    const currentPlayerEl = document.getElementById("currentPlayer");
    const rollsLeftEl = document.getElementById("rollsLeft");
    const turnCountEl = document.getElementById("turnCount");
    const rollBtn = document.getElementById("rollBtn");
    const startBtn = document.getElementById("startBtn");
    const resetBtn = document.getElementById("resetBtn");
    const playerOneInput = document.getElementById("playerOne");
    const playerTwoInput = document.getElementById("playerTwo");
    const playerOneHeader = document.getElementById("playerOneHeader");
    const playerTwoHeader = document.getElementById("playerTwoHeader");
    const scoreTableBody = document.querySelector("#scoreTable tbody");
    const totalOne = document.getElementById("totalOne");
    const totalTwo = document.getElementById("totalTwo");
    const sessionCodeInput = document.getElementById("sessionCode");
    const createSessionBtn = document.getElementById("createSessionBtn");
    const joinSessionBtn = document.getElementById("joinSessionBtn");
    const sessionStatus = document.getElementById("sessionStatus");
    const sessionShare = document.getElementById("sessionShare");

    function sum(dice) {
      return dice.reduce((acc, value) => acc + value, 0);
    }

    function sumOf(dice, target) {
      return dice.filter(value => value === target).reduce((acc, value) => acc + value, 0);
    }

    function hasOfKind(dice, count) {
      const counts = tally(dice);
      return Object.values(counts).some(value => value >= count);
    }

    function isFullHouse(dice) {
      const counts = Object.values(tally(dice)).sort();
      return counts.length === 2 && counts[0] === 2 && counts[1] === 3;
    }

    function isSmallStraight(dice) {
      const unique = [...new Set(dice)].sort();
      const sequences = [
        [1, 2, 3, 4],
        [2, 3, 4, 5],
        [3, 4, 5, 6]
      ];
      return sequences.some(seq => seq.every(value => unique.includes(value)));
    }

    function isLargeStraight(dice) {
      const unique = [...new Set(dice)].sort().join("");
      return unique === "12345" || unique === "23456";
    }

    function tally(dice) {
      return dice.reduce((acc, value) => {
        acc[value] = (acc[value] || 0) + 1;
        return acc;
      }, {});
    }

    function getUpperSum(playerIndex) {
      return upperCategoryIds.reduce((sum, id) => sum + (state.scores[playerIndex][id] || 0), 0);
    }

    function getBonus(playerIndex) {
      return getUpperSum(playerIndex) >= UPPER_THRESHOLD ? BONUS_VALUE : 0;
    }

    function getLowerSum(playerIndex) {
      const lowerIds = categories.slice(6).map(cat => cat.id);
      return lowerIds.reduce((sum, id) => sum + (state.scores[playerIndex][id] || 0), 0);
    }

    function getGrandTotal(playerIndex) {
      return getUpperSum(playerIndex) + getBonus(playerIndex) + getLowerSum(playerIndex);
    }

    function setSessionStatus(message, isError = false) {
      sessionStatus.textContent = message;
      sessionStatus.className = "session-status" + (isError ? " error" : "");
    }

    function setSessionShare(message) {
      sessionShare.textContent = message;
    }

    function normalizeSessionCode(rawValue) {
      const trimmed = rawValue.trim();
      if (!trimmed) {
        return "";
      }
      const withoutProtocol = trimmed.replace(/^https?:\\/\\//, "");
      if (withoutProtocol.includes("/")) {
        const parts = withoutProtocol.split("/").filter(Boolean);
        return parts[parts.length - 1];
      }
      return withoutProtocol;
    }

    function sessionUrl() {
      return `${sync.baseUrl}/${sync.sessionId}`;
    }

    function exportState() {
      return {
        players: state.players.slice(),
        currentPlayer: state.currentPlayer,
        rollsLeft: state.rollsLeft,
        turn: state.turn,
        dice: state.dice.slice(),
        held: state.held.slice(),
        scores: state.scores.map(score => ({ ...score })),
        started: state.started
      };
    }

    function applyRemoteState(payload) {
      if (!payload || !payload.state) {
        return;
      }
      const remote = payload.state;
      sync.suppressPush = true;
      if (Array.isArray(remote.players)) {
        state.players = remote.players.slice(0, 2);
      }
      if (typeof remote.currentPlayer === "number") {
        state.currentPlayer = remote.currentPlayer;
      }
      if (typeof remote.rollsLeft === "number") {
        state.rollsLeft = remote.rollsLeft;
      }
      if (typeof remote.turn === "number") {
        state.turn = remote.turn;
      }
      if (Array.isArray(remote.dice)) {
        state.dice = remote.dice.slice(0, 5);
      }
      if (Array.isArray(remote.held)) {
        state.held = remote.held.slice(0, 5);
      }
      if (Array.isArray(remote.scores) && remote.scores.length === 2) {
        state.scores = remote.scores.map(score => ({ ...score }));
      }
      state.started = Boolean(remote.started);
      state.updatedAt = payload.updatedAt || Date.now();
      sync.suppressPush = false;
      render();
    }

    function markStateUpdated() {
      state.updatedAt = Date.now();
      if (sync.enabled && !sync.suppressPush) {
        queuePush();
      }
    }

    function queuePush() {
      if (sync.pushTimer) {
        clearTimeout(sync.pushTimer);
      }
      sync.pushTimer = setTimeout(pushState, 300);
    }

    async function pushState() {
      if (!sync.enabled || !sync.sessionId || sync.suppressPush) {
        return;
      }
      try {
        const response = await fetch(sessionUrl(), {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ updatedAt: state.updatedAt, state: exportState() })
        });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        setSessionStatus(sync.isHost ? "Hosting session" : "Session synced");
        setSessionShare(`Session URL: ${sessionUrl()}`);
      } catch (error) {
        setSessionStatus(`Sync failed: ${error.message}`, true);
      }
    }

    async function pollRemote() {
      if (!sync.enabled || !sync.sessionId) {
        return;
      }
      try {
        const response = await fetch(sessionUrl(), { method: "GET", cache: "no-store" });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const text = await response.text();
        if (!text) {
          return;
        }
        const payload = JSON.parse(text);
        if (payload.updatedAt && payload.updatedAt > state.updatedAt) {
          applyRemoteState(payload);
          setSessionStatus("Session updated");
        } else {
          setSessionStatus(sync.isHost ? "Hosting session" : "Session synced");
        }
        setSessionShare(`Session URL: ${sessionUrl()}`);
      } catch (error) {
        setSessionStatus(`Sync failed: ${error.message}`, true);
      }
    }

    function startPolling() {
      if (sync.pollTimer) {
        clearInterval(sync.pollTimer);
      }
      sync.pollTimer = setInterval(pollRemote, sync.pollingMs);
    }

      const generated = `yhatzee-${Math.random().toString(36).slice(2, 8)}`;
>>>>>>> Stashed changes:src/actifix/modules/yahtzee/__init__.py
      const input = normalizeSessionCode(sessionCodeInput.value) || generated;
    function createSession() {
      const generated = `yahtzee-${Math.random().toString(36).slice(2, 8)}`;
      const input = normalizeSessionCode(sessionCodeInput.value) || generated;
=======
      const generated = `yhatzee-${Math.random().toString(36).slice(2, 8)}`;
>>>>>>> Stashed changes:src/actifix/modules/yhatzee/__init__.py
      const input = normalizeSessionCode(sessionCodeInput.value) || generated;
      sync.sessionId = input;
      sync.enabled = true;
      sync.isHost = true;
      sessionCodeInput.value = input;
      setSessionStatus("Creating session...");
      setSessionShare(`Session URL: ${sessionUrl()}`);
      startPolling();
      markStateUpdated();
      pushState();
    }

    function joinSession() {
      const input = normalizeSessionCode(sessionCodeInput.value);
      if (!input) {
        setSessionStatus("Enter a session code to join.", true);
        return;
      }
      sync.sessionId = input;
      sync.enabled = true;
      sync.isHost = false;
      setSessionStatus("Joining session...");
      setSessionShare(`Session URL: ${sessionUrl()}`);
      startPolling();
      pollRemote();
    }

    function rollDice() {
      if (!state.started || state.rollsLeft <= 0) {
        return;
      }
      const rollingIndices = state.held
        .map((held, index) => (held ? null : index))
        .filter(value => value !== null);
      state.dice = state.dice.map((value, index) => state.held[index] ? value : randomDie());
      state.rollsLeft -= 1;
      state.rollingIndices = rollingIndices;
      state.rollAnimationId += 1;
      const animationId = state.rollAnimationId;
      render();
      markStateUpdated();
      setTimeout(() => {
        if (state.rollAnimationId === animationId) {
          state.rollingIndices = [];
          renderDice();
        }
      }, 520);
    }

    function randomDie() {
      return Math.floor(Math.random() * 6) + 1;
    }

    function toggleHold(index) {
      if (!state.started || state.rollsLeft === 3) {
        return;
      }
      state.held[index] = !state.held[index];
      renderDice();
      markStateUpdated();
    }

    function scoreCategory(categoryId) {
      if (!state.started || state.rollsLeft === 3) {
        return;
      }
      const scoreMap = state.scores[state.currentPlayer];
      if (scoreMap[categoryId] !== null) {
        return;
      }
      const category = categories.find(cat => cat.id === categoryId);
      if (!category) {
        return;
      }
      scoreMap[categoryId] = category.score(state.dice);
      nextTurn();
    }

    function nextTurn() {
      state.currentPlayer = state.currentPlayer === 0 ? 1 : 0;
      state.turn += 1;
      state.rollsLeft = 3;
      state.held = [false, false, false, false, false];
      state.dice = [1, 1, 1, 1, 1];
      render();
      markStateUpdated();
    }

    function resetGame() {
      state.players = ["Player 1", "Player 2"];
      state.currentPlayer = 0;
      state.rollsLeft = 3;
      state.turn = 1;
      state.dice = [1, 1, 1, 1, 1];
      state.held = [false, false, false, false, false];
      state.scores = [
        Object.fromEntries(categories.map(cat => [cat.id, null])),
        Object.fromEntries(categories.map(cat => [cat.id, null]))
      ];
      state.started = false;
      playerOneInput.value = "Player 1";
      playerTwoInput.value = "Player 2";
      render();
      markStateUpdated();
    }

    function startGame() {
      state.players = [
        playerOneInput.value.trim() || "Player 1",
        playerTwoInput.value.trim() || "Player 2"
      ];
      state.started = true;
      state.rollsLeft = 3;
      state.turn = 1;
      state.currentPlayer = 0;
      state.held = [false, false, false, false, false];
      state.dice = [1, 1, 1, 1, 1];
      render();
      markStateUpdated();
    }

    function renderDice() {
      diceRow.innerHTML = "";
      const rolling = new Set(state.rollingIndices);
      state.dice.forEach((value, index) => {
        const die = document.createElement("button");
        const classes = ["die"];
        if (state.held[index]) {
          classes.push("held");
        }
        if (rolling.has(index)) {
          classes.push("rolling");
        }
        die.className = classes.join(" ");
        die.type = "button";
        die.textContent = value;
        const label = document.createElement("span");
        label.textContent = state.held[index] ? "Held" : "Hold";
        die.appendChild(label);
        die.addEventListener("click", () => toggleHold(index));
        diceRow.appendChild(die);
      });
    }

    function renderScoreboard() {
      scoreTableBody.innerHTML = "";

      // Upper section header
      let row = document.createElement("tr");
      row.className = "section-header";
      let catCell = document.createElement("td");
      catCell.colSpan = 3;
      catCell.textContent = "UPPER SECTION";
      row.appendChild(catCell);
      scoreTableBody.appendChild(row);

      // Upper categories
      upperCategoryIds.forEach(id => {
        const category = categories.find(c => c.id === id);
        const roww = document.createElement("tr");
        roww.className = "upper-row";
        const nameCell = document.createElement("td");
        nameCell.className = "category";
        nameCell.textContent = category.label;
        roww.appendChild(nameCell);
        state.scores.forEach((scores, playerIndex) => {
          const cell = document.createElement("td");
          const scoreValue = scores[id];
          if (scoreValue !== null) {
            cell.textContent = scoreValue;
          } else {
            const button = document.createElement("button");
            button.className = "score-btn";
            const preview = state.started ? category.score(state.dice) : "-";
            button.textContent = `Score ${preview}`;
            button.disabled = !state.started || playerIndex !== state.currentPlayer;
            button.addEventListener("click", () => scoreCategory(id));
            cell.appendChild(button);
          }
          roww.appendChild(cell);
        });
        scoreTableBody.appendChild(roww);
      });

      // Upper total
      row = document.createElement("tr");
      row.className = "upper-total-row";
      catCell = document.createElement("td");
      catCell.className = "category";
      catCell.textContent = "Upper Total";
      row.appendChild(catCell);
      [0,1].forEach(playerIndex => {
        const cell = document.createElement("td");
        cell.textContent = getUpperSum(playerIndex);
        row.appendChild(cell);
      });
      scoreTableBody.appendChild(row);

      // Line separator
      row = document.createElement("tr");
      row.className = "line-separator";
      const lineCat = document.createElement("td");
      lineCat.textContent = "──────────";
      lineCat.colSpan = 1;
      row.appendChild(lineCat);
      const lineP1 = document.createElement("td");
      row.appendChild(lineP1);
      const lineP2 = document.createElement("td");
      row.appendChild(lineP2);
      scoreTableBody.appendChild(row);

      // Bonus row
      row = document.createElement("tr");
      row.className = "bonus-row";
      catCell = document.createElement("td");
      catCell.className = "category";
      catCell.textContent = "BONUS";
      row.appendChild(catCell);
      [0,1].forEach(playerIndex => {
        const cell = document.createElement("td");
        const bonus = getBonus(playerIndex);
        const upper = getUpperSum(playerIndex);
        if (bonus > 0) {
          cell.innerHTML = '35 <span style="color:green;font-weight:bold;">✓ Achieved</span>';
        } else {
          const needed = UPPER_THRESHOLD - upper;
          cell.innerHTML = `0 <span style="color:orange;">(need ${needed})</span>`;
        }
        row.appendChild(cell);
      });
      scoreTableBody.appendChild(row);

      // Lower section header
      row = document.createElement("tr");
      row.className = "section-header";
      catCell = document.createElement("td");
      catCell.colSpan = 3;
      catCell.textContent = "LOWER SECTION";
      row.appendChild(catCell);
      scoreTableBody.appendChild(row);

      // Lower categories
      categories.slice(6).forEach(category => {
        const roww = document.createElement("tr");
        roww.className = "lower-row";
        const nameCell = document.createElement("td");
        nameCell.className = "category";
        nameCell.textContent = category.label;
        roww.appendChild(nameCell);
        state.scores.forEach((scores, playerIndex) => {
          const cell = document.createElement("td");
          const scoreValue = scores[category.id];
          if (scoreValue !== null) {
            cell.textContent = scoreValue;
          } else {
            const button = document.createElement("button");
            button.className = "score-btn";
            const preview = state.started ? category.score(state.dice) : "-";
            button.textContent = `Score ${preview}`;
            button.disabled = !state.started || playerIndex !== state.currentPlayer;
            button.addEventListener("click", () => scoreCategory(category.id));
            cell.appendChild(button);
          }
          roww.appendChild(cell);
        });
        scoreTableBody.appendChild(roww);
      });
    }

    function updateTotals() {
      const grandTotals = [getGrandTotal(0), getGrandTotal(1)];
      totalOne.textContent = `${state.players[0]} Grand Total: ${grandTotals[0]}`;
      totalTwo.textContent = `${state.players[1]} Grand Total: ${grandTotals[1]}`;
    }

    function renderStatus() {
      currentPlayerEl.textContent = state.started ? `${state.players[state.currentPlayer]}'s turn` : "Waiting to start";
      rollsLeftEl.textContent = state.rollsLeft;
      turnCountEl.textContent = state.turn;
      rollBtn.disabled = !state.started || state.rollsLeft <= 0;
    }

    function renderHeaders() {
      playerOneHeader.textContent = state.players[0];
      playerTwoHeader.textContent = state.players[1];
    }

    function render() {
      renderHeaders();
      renderStatus();
      renderDice();
      renderScoreboard();
      updateTotals();
    }

    rollBtn.addEventListener("click", rollDice);
    startBtn.addEventListener("click", startGame);
    resetBtn.addEventListener("click", resetGame);
    createSessionBtn.addEventListener("click", createSession);
    joinSessionBtn.addEventListener("click", joinSession);

    render();
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    run_gui()
