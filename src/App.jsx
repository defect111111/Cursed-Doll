import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  CircleStop,
  Gift,
  Play,
  RotateCcw,
  Skull,
  Users,
} from "lucide-react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

function diceLabel(face) {
  if (face === "one doll") return "Doll";
  if (face === "two dolls") return "2 Dolls";
  return face;
}

function diceClass(face) {
  if (face.includes("doll")) return "die doll-die";
  return "die number-die";
}

function App() {
  const [game, setGame] = useState(null);
  const [playerCount, setPlayerCount] = useState(2);
  const [seed, setSeed] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function request(path, options = {}) {
    setError("");
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}${path}`, {
        headers: { "Content-Type": "application/json" },
        ...options,
      });
      const contentType = response.headers.get("content-type") || "";
      const isJson = contentType.includes("application/json");
      const body = isJson ? await response.json() : await response.text();
      if (!response.ok) {
        const detail = typeof body === "object" ? body.detail : body;
        throw new Error(detail || `Request failed with ${response.status}`);
      }
      if (!isJson) {
        throw new Error("The backend response was not JSON.");
      }
      setGame(body);
      return body;
    } catch (requestError) {
      setError(
        `Cannot reach the game backend. Make sure FastAPI is running and restart Vite if you changed vite.config.js. ${requestError.message}`,
      );
      return null;
    } finally {
      setLoading(false);
    }
  }

  async function startGame() {
    await request("/games", {
      method: "POST",
      body: JSON.stringify({
        player_count: Number(playerCount),
        seed: seed === "" ? null : Number(seed),
      }),
    });
  }

  async function action(payload) {
    if (!game) return;
    await request(`/games/${game.id}/actions`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  useEffect(() => {
    startGame();
  }, []);

  const prompt = useMemo(() => phasePrompt(game), [game]);

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">Cursed Doll</p>
          <h1>Table</h1>
        </div>
        <div className="new-game">
          <label>
            Players
            <input
              min="1"
              max="6"
              type="number"
              value={playerCount}
              onChange={(event) => setPlayerCount(event.target.value)}
            />
          </label>
          <label>
            Seed
            <input
              type="number"
              placeholder="optional"
              value={seed}
              onChange={(event) => setSeed(event.target.value)}
            />
          </label>
          <button className="primary" onClick={startGame} disabled={loading}>
            <RotateCcw size={18} />
            New Game
          </button>
        </div>
      </section>

      {error && <div className="error">{error}</div>}

      {!game && !error && (
        <section className="empty-state">
          <strong>{loading ? "Starting game..." : "No game loaded"}</strong>
        </section>
      )}

      {game && (
        <section className="game-grid">
          <aside className="side-panel">
            <div className="status-block">
              <span className="status-icon">
                {game.winner ? <Skull size={20} /> : <Users size={20} />}
              </span>
              <div>
                <p>{game.winner ? "Game Over" : `Turn ${game.turn_number}`}</p>
                <strong>
                  {game.winner
                    ? `Player ${game.winner} wins`
                    : `Player ${game.current_player}`}
                </strong>
              </div>
            </div>

            <h2>Players</h2>
            <div className="player-list">
              {Object.entries(game.player_dolls).map(([player, dolls]) => (
                <div
                  className={
                    Number(player) === game.current_player
                      ? "player active"
                      : "player"
                  }
                  key={player}
                >
                  <span>Player {player}</span>
                  <strong>{dolls}</strong>
                </div>
              ))}
            </div>

            <h2>Rooms</h2>
            <div className="room-list">
              {game.room_numbers.map((room) => (
                <div className="room" key={room}>
                  <span>Room {room}</span>
                  <strong>{game.rooms[room]}</strong>
                </div>
              ))}
            </div>
          </aside>

          <section className="table-panel">
            <div className="prompt-row">
              <div>
                <p className="eyebrow">{game.phase.replace("_", " ")}</p>
                <h2>{prompt.title}</h2>
                <p className="prompt-copy">{prompt.copy}</p>
              </div>
              {game.phase === "turn_summary" && (
                <button
                  className="primary"
                  onClick={() => action({ action: "next_turn" })}
                  disabled={loading}
                >
                  <ArrowRight size={18} />
                  Next Turn
                </button>
              )}
            </div>

            <div className="dice-zone">
              <Panel title="Current Roll">
                <DiceRow dice={game.roll} />
              </Panel>
              <Panel title="Kept Dice">
                <DiceRow dice={game.kept_dice} empty="No dice kept yet" />
                <div className="kept-stats">
                  <span>Total {game.kept_total}</span>
                  <span>Dolls {game.dolls_rolled}</span>
                  <span>{game.remaining_dice} dice left</span>
                </div>
              </Panel>
            </div>

            <ActionPanel game={game} action={action} loading={loading} />
          </section>

          <aside className="log-panel">
            <h2>Turn Log</h2>
            <div className="log-list">
              {game.turn_history.length === 0 && (
                <p className="muted">Completed turns will appear here.</p>
              )}
              {[...game.turn_history].reverse().map((turn) => (
                <div className="log-entry" key={turn.turn_number}>
                  <strong>
                    Turn {turn.turn_number}, Player {turn.player_index}
                  </strong>
                  <span>
                    total {turn.turn_result.kept_total}, dolls{" "}
                    {turn.dolls_rolled}, room {turn.target_room}
                  </span>
                  <span>
                    placed {turn.dolls_placed}, back {turn.dolls_returned},
                    gifted {turn.gifted_dolls}
                  </span>
                </div>
              ))}
            </div>
          </aside>
        </section>
      )}
    </main>
  );
}

function phasePrompt(game) {
  if (!game) return { title: "Loading", copy: "" };
  const prompts = {
    choose_face: {
      title: "Choose a pattern to keep",
      copy: "All dice with that face will be reserved, then the rest continue.",
    },
    stop_check: {
      title: "Stop or continue",
      copy: "Your kept total is at least 7, so you may ignore the remaining dice.",
    },
    choose_room: {
      title: "Choose a tied room",
      copy: "Your total is 6 or less. Pick one of the fullest tied rooms to empty.",
    },
    gift: {
      title: "Optional gift",
      copy: "You placed dolls and kept some 1s. Give one doll at a time, or stop.",
    },
    turn_summary: {
      title: "Turn complete",
      copy: "Review the table, then pass to the next player.",
    },
    game_over: {
      title: `Player ${game.winner} wins`,
      copy: "That player has no dolls remaining.",
    },
  };
  return prompts[game.phase] || { title: "Continue", copy: "" };
}

function Panel({ title, children }) {
  return (
    <div className="panel">
      <h3>{title}</h3>
      {children}
    </div>
  );
}

function DiceRow({ dice, empty = "No dice" }) {
  if (!dice || dice.length === 0) return <p className="muted">{empty}</p>;
  return (
    <div className="dice-row">
      {dice.map((face, index) => (
        <span className={diceClass(face)} key={`${face}-${index}`}>
          {diceLabel(face)}
        </span>
      ))}
    </div>
  );
}

function ActionPanel({ game, action, loading }) {
  if (game.phase === "choose_face") {
    return (
      <div className="actions">
        {game.choices.map((choice) => (
          <button
            key={choice.face}
            onClick={() =>
              action({ action: "choose_face", face: choice.face })
            }
            disabled={loading}
          >
            <Play size={18} />
            <span>{diceLabel(choice.face)} x{choice.count}</span>
            <small>total {choice.projected_total}</small>
          </button>
        ))}
      </div>
    );
  }

  if (game.phase === "stop_check") {
    return (
      <div className="actions two">
        <button onClick={() => action({ action: "stop", stop: false })}>
          <Play size={18} />
          Continue
        </button>
        <button onClick={() => action({ action: "stop", stop: true })}>
          <CircleStop size={18} />
          Stop
        </button>
      </div>
    );
  }

  if (game.phase === "choose_room") {
    return (
      <div className="actions">
        {game.tied_rooms.map((room) => (
          <button
            key={room}
            onClick={() => action({ action: "choose_room", room })}
          >
            Room {room}
            <small>{game.rooms[room]} dolls</small>
          </button>
        ))}
      </div>
    );
  }

  if (game.phase === "gift") {
    return (
      <div className="actions">
        {game.available_recipients.map((recipient) => (
          <button
            key={recipient}
            onClick={() => action({ action: "gift", recipient })}
          >
            <Gift size={18} />
            Player {recipient}
            <small>{game.gift_remaining} left</small>
          </button>
        ))}
        <button onClick={() => action({ action: "gift", recipient: null })}>
          <CircleStop size={18} />
          Stop Giving
        </button>
      </div>
    );
  }

  if (game.phase === "game_over") {
    return <p className="end-message">Player {game.winner} has escaped the dolls.</p>;
  }

  return null;
}

createRoot(document.getElementById("root")).render(<App />);
