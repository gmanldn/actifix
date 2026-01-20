"""Yhatzee module with a localhost GUI for a two-player game."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, TYPE_CHECKING, Union

from actifix.log_utils import log_event
from actifix.raise_af import TicketPriority, record_error
from actifix.state_paths import get_actifix_paths

if TYPE_CHECKING:
    from flask import Blueprint

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8090


def _normalize_project_root(project_root: Optional[Union[str, Path]]) -> Optional[Path]:
    if project_root is None:
        return None
    return Path(project_root)


def _log_gui_init(project_root: Optional[Union[str, Path]], host: str, port: int) -> None:
    paths = get_actifix_paths(project_root=_normalize_project_root(project_root))
    log_event(
        "YHATZEE_GUI_INIT",
        "Yhatzee GUI configured",
        extra={
            "host": host,
            "port": port,
            "state_dir": str(paths.state_dir),
            "module": "modules.yhatzee",
        },
        source="modules.yhatzee.create_blueprint",
    )


def create_blueprint(
    project_root: Optional[Union[str, Path]] = None,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    url_prefix: Optional[str] = "/modules/yhatzee",
) -> Blueprint:
    """Create the Flask blueprint that serves the Yhatzee GUI."""
    try:
        from flask import Blueprint, Response  # Local import keeps Flask optional

        blueprint = Blueprint("yhatzee", __name__, url_prefix=url_prefix)

        @blueprint.route("/")
        def index():
            return Response(_HTML_PAGE, mimetype="text/html")

        @blueprint.route("/health")
        def health():
            return {"status": "ok"}

        _log_gui_init(project_root, host, port)
        return blueprint
    except Exception as exc:
        record_error(
            message=f"Failed to create Yhatzee blueprint: {exc}",
            source="modules/yhatzee/__init__.py:create_blueprint",
            run_label="yhatzee-gui",
            error_type=type(exc).__name__,
            priority=TicketPriority.P2,
        )
        raise


def create_app(
    project_root: Optional[Union[str, Path]] = None,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> "Flask":
    """Create the Flask app that serves the Yhatzee GUI."""
    try:
        from flask import Flask  # Local import to keep optional dependency optional

        app = Flask(__name__)
        blueprint = create_blueprint(project_root=project_root, host=host, port=port, url_prefix=None)
        app.register_blueprint(blueprint)
        return app
    except Exception as exc:
        record_error(
            message=f"Failed to create Yhatzee GUI app: {exc}",
            source="modules/yhatzee/__init__.py:create_app",
            run_label="yhatzee-gui",
            error_type=type(exc).__name__,
            priority=TicketPriority.P2,
        )
        raise


def run_gui(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    project_root: Optional[Union[str, Path]] = None,
    debug: bool = False,
) -> None:
    """Run the Yhatzee GUI on localhost."""
    try:
        app = create_app(project_root=project_root, host=host, port=port)
        log_event(
            "YHATZEE_GUI_START",
            f"Yhatzee GUI running at http://{host}:{port}",
            extra={"host": host, "port": port, "module": "modules.yhatzee"},
            source="modules.yhatzee.run_gui",
        )
        app.run(host=host, port=port, debug=debug)
    except Exception as exc:
        record_error(
            message=f"Failed to start Yhatzee GUI: {exc}",
            source="modules/yhatzee/__init__.py:run_gui",
            run_label="yhatzee-gui",
            error_type=type(exc).__name__,
            priority=TicketPriority.P1,
        )
        raise


_HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Yhatzee Module</title>
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
    .die span {
      position: absolute;
      bottom: 6px;
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--muted);
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
  </style>
</head>
<body>
  <div class="app">
    <header>
      <div>
        <div class="subtitle">Actifix Module</div>
        <h1>Yhatzee</h1>
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
    </div>

    <section class="card" style="margin-top: 18px;">
      <h2>Score Sheet</h2>
      <div class="note">Select a category for the current player to lock in a score.</div>
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
      { id: "yhatzee", label: "Yhatzee", score: dice => hasOfKind(dice, 5) ? 50 : 0 },
      { id: "chance", label: "Chance", score: dice => sum(dice) }
    ];

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
      started: false
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

    function rollDice() {
      if (!state.started || state.rollsLeft <= 0) {
        return;
      }
      state.dice = state.dice.map((value, index) => state.held[index] ? value : randomDie());
      state.rollsLeft -= 1;
      render();
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
    }

    function renderDice() {
      diceRow.innerHTML = "";
      state.dice.forEach((value, index) => {
        const die = document.createElement("button");
        die.className = "die" + (state.held[index] ? " held" : "");
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
      categories.forEach(category => {
        const row = document.createElement("tr");
        const nameCell = document.createElement("td");
        nameCell.className = "category";
        nameCell.textContent = category.label;
        row.appendChild(nameCell);

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
          row.appendChild(cell);
        });
        scoreTableBody.appendChild(row);
      });
    }

    function updateTotals() {
      const totalScores = state.scores.map(scoreMap => {
        return Object.values(scoreMap).reduce((acc, value) => acc + (value || 0), 0);
      });
      totalOne.textContent = `${state.players[0]} Total: ${totalScores[0]}`;
      totalTwo.textContent = `${state.players[1]} Total: ${totalScores[1]}`;
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

    render();
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    run_gui()
