import { useMemo, useState } from "react";
import {
  ArrowRight,
  BookOpen,
  CircleStop,
  Gift,
  Languages,
  Play,
  Power,
  RotateCcw,
  Skull,
  Users,
} from "lucide-react";
import { createRoot } from "react-dom/client";
import { applyGameAction, createGame } from "./gameLogic";
import "./styles.css";

function diceClass(face) {
  if (face.includes("doll")) return "die doll-die";
  return "die number-die";
}

const TEXT = {
  en: {
    brand: "Cursed Doll",
    table: "Table",
    startCopy:
      "Roll, reserve patterns, move dolls through rooms, and escape the table by starting your turn empty-handed.",
    players: "Players",
    rooms: "Rooms",
    player: "Player",
    room: "Room",
    start: "Start",
    exit: "Exit",
    newGame: "New Game",
    noGame: "No game loaded",
    gameOver: "Game Over",
    turn: "Turn",
    wins: "wins",
    currentRoll: "Current Roll",
    keptDice: "Kept Dice",
    noDice: "No dice",
    noKeptDice: "No dice kept yet",
    total: "Total",
    dolls: "Dolls",
    diceLeft: "dice left",
    nextTurn: "Next Turn",
    turnLog: "Turn Log",
    noTurns: "Completed turns will appear here.",
    placed: "placed",
    back: "back",
    gifted: "gifted",
    roll: "Roll",
    dice: "dice",
    continue: "Continue",
    stop: "Stop",
    stopGiving: "Stop Giving",
    rules: "Rules",
    close: "Close",
    reference: "Reference",
    language: "中文",
    phaseLabels: {
      ready_to_roll: "ready to roll",
      choose_face: "choose face",
      stop_check: "stop check",
      choose_room: "choose room",
      gift: "gift",
      turn_summary: "turn summary",
      game_over: "game over",
    },
    diceFaces: {
      "one doll": "Doll",
      "two dolls": "2 Dolls",
    },
    prompts: {
      ready_to_roll: {
        title: "Roll the dice",
        copy: "Roll the remaining dice, then reserve one available pattern.",
      },
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
        title: "Game over",
        copy: "The winner started a turn with no dolls.",
      },
    },
    rulesText: [
      "Each turn begins by rolling the remaining dice. Choose one face to reserve; all dice showing that face are kept, and that face cannot be chosen again this turn.",
      "Numeric faces add to the kept total. Doll faces add dolls but no number. If the kept total reaches 7 or more, the player may stop; otherwise the turn continues until no dice remain or no new face can be reserved.",
      "Totals 7, 8, 9, and 10 adjust the matching room to the rolled doll count. Totals 11 or more add rolled dolls to room 11. Totals 6 or less take all dolls from one fullest room among 7 through 10.",
      "If a player placed at least one doll and kept any 1s, that player may give one doll per kept 1 to another player. Any player above 10 dolls moves the extra dolls into room 11.",
      "A player wins only when their turn is about to start and they have zero dolls.",
    ],
  },
  zh: {
    brand: "诅咒娃娃",
    table: "牌桌",
    startCopy:
      "掷骰、保留图案、移动娃娃。谁在自己的回合开始时手中没有娃娃，谁就获胜。",
    players: "玩家",
    rooms: "房间",
    player: "玩家",
    room: "房间",
    start: "开始",
    exit: "退出",
    newGame: "新游戏",
    noGame: "没有载入游戏",
    gameOver: "游戏结束",
    turn: "回合",
    wins: "获胜",
    currentRoll: "当前掷骰",
    keptDice: "已保留骰子",
    noDice: "没有骰子",
    noKeptDice: "还没有保留骰子",
    total: "点数",
    dolls: "娃娃",
    diceLeft: "颗骰子剩余",
    nextTurn: "下一回合",
    turnLog: "回合记录",
    noTurns: "完成的回合会显示在这里。",
    placed: "放入",
    back: "取回",
    gifted: "赠送",
    roll: "掷骰",
    dice: "颗骰子",
    continue: "继续",
    stop: "停止",
    stopGiving: "停止赠送",
    rules: "规则",
    close: "关闭",
    reference: "说明",
    language: "EN",
    phaseLabels: {
      ready_to_roll: "准备掷骰",
      choose_face: "选择图案",
      stop_check: "停止检查",
      choose_room: "选择房间",
      gift: "赠送",
      turn_summary: "回合结算",
      game_over: "游戏结束",
    },
    diceFaces: {
      "one doll": "1 娃娃",
      "two dolls": "2 娃娃",
    },
    prompts: {
      ready_to_roll: {
        title: "掷骰",
        copy: "掷出剩余骰子，然后选择一个可保留的图案。",
      },
      choose_face: {
        title: "选择要保留的图案",
        copy: "所有相同图案的骰子都会被保留，剩下的骰子继续游戏。",
      },
      stop_check: {
        title: "停止或继续",
        copy: "已保留点数至少为 7，可以忽略剩余骰子并结束回合。",
      },
      choose_room: {
        title: "选择并列房间",
        copy: "点数为 6 或更少。选择娃娃最多的并列房间之一并取走其中全部娃娃。",
      },
      gift: {
        title: "可选赠送",
        copy: "你放入了娃娃并保留了 1。可以逐个赠送娃娃，也可以停止。",
      },
      turn_summary: {
        title: "回合完成",
        copy: "查看桌面，然后进入下一名玩家的回合。",
      },
      game_over: {
        title: "游戏结束",
        copy: "获胜者在回合开始时没有娃娃。",
      },
    },
    rulesText: [
      "每个回合从掷出剩余骰子开始。玩家选择一个图案保留，所有显示该图案的骰子都会被保留；同一回合内不能再次选择已经保留过的图案。",
      "数字面会加入已保留点数。娃娃面只计算娃娃数量，不增加点数。已保留点数达到 7 或以上时，玩家可以停止；否则继续，直到没有骰子或没有新的图案可保留。",
      "最终点数为 7、8、9、10 时，将对应房间调整为本回合掷出的娃娃数。点数为 11 或以上时，把掷出的娃娃放入 11 号房间。点数为 6 或更少时，从 7 到 10 号房间中选择娃娃最多的房间并取走全部娃娃。",
      "如果玩家至少向房间放入了一个娃娃，并且保留了 1，则每个保留的 1 可以让玩家赠送一个自己的娃娃给其他玩家。任何玩家超过 10 个娃娃时，多出的娃娃进入 11 号房间。",
      "只有当某名玩家的回合即将开始，并且该玩家手中没有娃娃时，该玩家才获胜。",
    ],
  },
};

function diceLabel(face, text) {
  return text.diceFaces[face] || face;
}

function App() {
  const [screen, setScreen] = useState("start");
  const [game, setGame] = useState(null);
  const [playerCount, setPlayerCount] = useState(2);
  const [error, setError] = useState("");
  const [rulesOpen, setRulesOpen] = useState(false);
  const [language, setLanguage] = useState("en");
  const text = TEXT[language];
  const switchLanguage = () =>
    setLanguage((currentLanguage) => (currentLanguage === "en" ? "zh" : "en"));

  function startGame() {
    setError("");
    try {
      setGame(
        createGame({
          playerCount: Number(playerCount),
        }),
      );
      setScreen("game");
    } catch (gameError) {
      setError(gameError.message);
    }
  }

  function exitGame() {
    setError("");
    setGame(null);
    setRulesOpen(false);
    setScreen("start");
  }

  function action(payload) {
    if (rulesOpen) return;
    setError("");
    setGame((currentGame) => {
      if (!currentGame) return currentGame;
      try {
        return applyGameAction(currentGame, payload);
      } catch (gameError) {
        setError(gameError.message);
        return currentGame;
      }
    });
  }

  const prompt = useMemo(() => phasePrompt(game, text), [game, text]);

  if (screen === "start") {
    return (
      <main className="start-screen">
        <section className="start-panel">
          <div>
            <p className="eyebrow">{text.brand}</p>
            <h1>{text.brand}</h1>
            <p className="start-copy">{text.startCopy}</p>
          </div>

          <div className="start-settings">
            <label>
              {text.players}
              <input
                min="1"
                max="6"
                type="number"
                value={playerCount}
                onChange={(event) => setPlayerCount(event.target.value)}
              />
            </label>
          </div>

          {error && <div className="error">{error}</div>}

          <div className="start-actions">
            <button className="primary" onClick={startGame}>
              <Play size={18} />
              {text.start}
            </button>
            <button onClick={exitGame}>
              <Power size={18} />
              {text.exit}
            </button>
          </div>
        </section>
        <div className="floating-controls">
          <LanguageButton text={text} onClick={switchLanguage} />
        </div>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">{text.brand}</p>
          <h1>{text.table}</h1>
        </div>
        <div className="new-game">
          <label>
            {text.players}
            <input
              min="1"
              max="6"
              type="number"
              value={playerCount}
              onChange={(event) => setPlayerCount(event.target.value)}
            />
          </label>
          <button className="primary" onClick={startGame}>
            <RotateCcw size={18} />
            {text.newGame}
          </button>
          <button onClick={exitGame}>
            <Power size={18} />
            {text.exit}
          </button>
        </div>
      </section>

      {error && <div className="error">{error}</div>}

      {!game && !error && (
        <section className="empty-state">
          <strong>{text.noGame}</strong>
        </section>
      )}

      {game && (
        <>
          <section className="game-grid" aria-hidden={rulesOpen}>
            <aside className="side-panel">
              <div className="status-block">
                <span className="status-icon">
                  {game.winner ? <Skull size={20} /> : <Users size={20} />}
                </span>
                <div>
                  <p>
                    {game.winner
                      ? text.gameOver
                      : `${text.turn} ${game.turn_number}`}
                  </p>
                  <strong>
                    {game.winner
                      ? `${text.player} ${game.winner} ${text.wins}`
                      : `${text.player} ${game.current_player}`}
                  </strong>
                </div>
              </div>

              <h2>{text.players}</h2>
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
                    <span>
                      {text.player} {player}
                    </span>
                    <strong>{dolls}</strong>
                  </div>
                ))}
              </div>

              <h2>{text.rooms}</h2>
              <div className="room-list">
                {game.room_numbers.map((room) => (
                  <div className="room" key={room}>
                    <span>
                      {text.room} {room}
                    </span>
                    <strong>{game.rooms[room]}</strong>
                  </div>
                ))}
              </div>
            </aside>

            <section className="table-panel">
              <div className="prompt-row">
                <div>
                  <p className="eyebrow">{text.phaseLabels[game.phase]}</p>
                  <h2>{prompt.title}</h2>
                  <p className="prompt-copy">{prompt.copy}</p>
                </div>
                {game.phase === "turn_summary" && (
                  <button
                    className="primary"
                    onClick={() => action({ action: "next_turn" })}
                  >
                    <ArrowRight size={18} />
                    {text.nextTurn}
                  </button>
                )}
              </div>

              <div className="dice-zone">
                <Panel title={text.currentRoll}>
                  <DiceRow dice={game.roll} text={text} empty={text.noDice} />
                </Panel>
                <Panel title={text.keptDice}>
                  <DiceRow
                    dice={game.kept_dice}
                    empty={text.noKeptDice}
                    text={text}
                  />
                  <div className="kept-stats">
                    <span>
                      {text.total} {game.kept_total}
                    </span>
                    <span>
                      {text.dolls} {game.dolls_rolled}
                    </span>
                    <span>
                      {game.remaining_dice} {text.diceLeft}
                    </span>
                  </div>
                </Panel>
              </div>

              <ActionPanel game={game} action={action} text={text} />
            </section>

            <aside className="log-panel">
              <h2>{text.turnLog}</h2>
              <div className="log-list">
                {game.turn_history.length === 0 && (
                  <p className="muted">{text.noTurns}</p>
                )}
                {[...game.turn_history].reverse().map((turn) => (
                  <div className="log-entry" key={turn.turn_number}>
                    <strong>
                      {text.turn} {turn.turn_number}, {text.player}{" "}
                      {turn.player_index}
                    </strong>
                    <span>
                      {text.total} {turn.turn_result.kept_total},{" "}
                      {text.dolls} {turn.dolls_rolled}, {text.room}{" "}
                      {turn.target_room}
                    </span>
                    <span>
                      {text.placed} {turn.dolls_placed}, {text.back}{" "}
                      {turn.dolls_returned}, {text.gifted} {turn.gifted_dolls}
                    </span>
                  </div>
                ))}
              </div>
            </aside>
          </section>

          <div className="floating-controls">
            <button
              className="rules-button"
              onClick={() => setRulesOpen(true)}
              aria-label={text.rules}
            >
              <BookOpen size={20} />
              {text.rules}
            </button>
            <LanguageButton text={text} onClick={switchLanguage} />
          </div>

          {rulesOpen && (
            <RulesPanel onClose={() => setRulesOpen(false)} text={text} />
          )}
        </>
      )}
    </main>
  );
}

function LanguageButton({ text, onClick }) {
  return (
    <button
      className="language-button"
      onClick={onClick}
      aria-label={text.language}
    >
      <Languages size={20} />
      {text.language}
    </button>
  );
}

function RulesPanel({ onClose, text }) {
  return (
    <div className="rules-overlay" role="dialog" aria-modal="true">
      <section className="rules-panel">
        <div className="rules-header">
          <div>
            <p className="eyebrow">{text.reference}</p>
            <h2>{text.rules}</h2>
          </div>
          <button onClick={onClose}>{text.close}</button>
        </div>

        <div className="rules-content">
          {text.rulesText.map((rule) => (
            <p key={rule}>{rule}</p>
          ))}
        </div>
      </section>
    </div>
  );
}

function phasePrompt(game, text) {
  if (!game) return { title: "", copy: "" };
  if (game.phase === "game_over") {
    return {
      title: `${text.player} ${game.winner} ${text.wins}`,
      copy: text.prompts.game_over.copy,
    };
  }
  return text.prompts[game.phase] || { title: text.continue, copy: "" };
}

function Panel({ title, children }) {
  return (
    <div className="panel">
      <h3>{title}</h3>
      {children}
    </div>
  );
}

function DiceRow({ dice, text, empty }) {
  if (!dice || dice.length === 0) return <p className="muted">{empty}</p>;
  return (
    <div className="dice-row">
      {dice.map((face, index) => (
        <span className={diceClass(face)} key={`${face}-${index}`}>
          {diceLabel(face, text)}
        </span>
      ))}
    </div>
  );
}

function ActionPanel({ game, action, text }) {
  if (game.phase === "ready_to_roll") {
    return (
      <div className="actions two">
        <button className="primary" onClick={() => action({ action: "roll" })}>
          <RotateCcw size={18} />
          {text.roll}
          <small>
            {game.remaining_dice} {text.dice}
          </small>
        </button>
      </div>
    );
  }

  if (game.phase === "choose_face") {
    return (
      <div className="actions">
        {game.choices.map((choice) => (
          <button
            key={choice.face}
            onClick={() =>
              action({ action: "choose_face", face: choice.face })
            }
          >
            <Play size={18} />
            <span>
              {diceLabel(choice.face, text)} x{choice.count}
            </span>
            <small>
              {text.total} {choice.projected_total}
            </small>
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
          {text.continue}
        </button>
        <button onClick={() => action({ action: "stop", stop: true })}>
          <CircleStop size={18} />
          {text.stop}
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
            {text.room} {room}
            <small>
              {game.rooms[room]} {text.dolls}
            </small>
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
            {text.player} {recipient}
            <small>{game.gift_remaining}</small>
          </button>
        ))}
        <button onClick={() => action({ action: "gift", recipient: null })}>
          <CircleStop size={18} />
          {text.stopGiving}
        </button>
      </div>
    );
  }

  if (game.phase === "game_over") {
    return (
      <p className="end-message">
        {text.player} {game.winner} {text.wins}
      </p>
    );
  }

  return null;
}

createRoot(document.getElementById("root")).render(<App />);
