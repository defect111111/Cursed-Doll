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
    rulesSections: [
      {
        title: "Goal",
        items: [
          "Each player starts the game with 10 dolls in hand. Rooms 7, 8, 9, and 10 each start with 1 doll; room 11 starts empty.",
          "Your aim is to get rid of your dolls. A player wins only if they start their own turn with 0 dolls.",
        ],
      },
      {
        title: "Dice and reserving",
        items: [
          "The six die faces are 1, 2, 3, 4, one doll, and two dolls.",
          "At the start of a turn you roll 6 dice. Later in the same turn, you roll only the dice that were not kept.",
          "After each roll, choose one face to reserve. All dice showing that face are kept together.",
          "Each face can be reserved only once per turn. If no rolled face is available, the turn ends immediately.",
        ],
      },
      {
        title: "Total, dolls, and stopping",
        items: [
          "Number faces add to the kept total. Doll faces do not add to the total; they only count how many dolls were rolled this turn.",
          "If the kept total is below 7, you must continue whenever there are dice left and an available face to reserve.",
          "If the kept total is 7 or higher, you may stop and ignore all unkept dice. If you continue, you roll the remaining dice.",
        ],
      },
      {
        title: "Room effects",
        items: [
          "Final totals 7, 8, 9, and 10 adjust the matching room to exactly the number of dolls you rolled this turn. If the room has fewer dolls, you add dolls from your hand. If it has more, you take the difference back.",
          "A final total of 11 or higher adds the dolls you rolled this turn into room 11. Room 11 is never adjusted downward.",
          "A final total of 6 or lower means you take all dolls from one fullest room among rooms 7 through 10. If several rooms tie for most dolls, you choose which tied room to empty.",
        ],
      },
      {
        title: "Gifts and overflow",
        items: [
          "If you added at least 1 doll to any room this turn and kept any 1s, you may give 1 doll to another player for each kept 1. Giving is optional and happens one doll at a time.",
          "After every turn, any player with more than 10 dolls moves the extra dolls above 10 into room 11.",
        ],
      },
      {
        title: "Winning",
        items: [
          "Running out of dolls during your turn does not win immediately. The win check happens only when a player's turn begins.",
          "If a player's turn begins and that player has 0 dolls, the game ends and that player wins.",
        ],
      },
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
    rulesSections: [
      {
        title: "目标",
        items: [
          "每名玩家开局手中有 10 个娃娃。7、8、9、10 号房间各有 1 个娃娃，11 号房间开局为空。",
          "你的目标是把手中的娃娃清空。只有当某名玩家自己的回合开始时手中有 0 个娃娃，该玩家才获胜。",
        ],
      },
      {
        title: "骰子与保留",
        items: [
          "骰子的六个面分别是 1、2、3、4、一个娃娃、两个娃娃。",
          "回合开始时掷 6 颗骰子。同一回合后续只掷还没有被保留的骰子。",
          "每次掷骰后选择一个面保留。所有显示该面的骰子会一起被保留。",
          "同一个面在一个回合内只能保留一次。如果当前掷出的骰子里没有可保留的新面，回合立刻结束。",
        ],
      },
      {
        title: "点数、娃娃与停止",
        items: [
          "数字面会加入已保留点数。娃娃面不会增加点数，只记录本回合掷出了多少娃娃。",
          "如果已保留点数小于 7，并且还有骰子与可保留的新面，就必须继续。",
          "如果已保留点数达到 7 或更高，可以选择停止并忽略剩余骰子。若选择继续，则掷剩余骰子。",
        ],
      },
      {
        title: "房间结算",
        items: [
          "最终点数为 7、8、9、10 时，把对应房间调整到本回合掷出的娃娃数。房间娃娃较少时，你从手中补入差额；房间娃娃较多时，你取回差额。",
          "最终点数为 11 或更高时，把本回合掷出的娃娃放入 11 号房间。11 号房间不会向下调整。",
          "最终点数为 6 或更低时，从 7 到 10 号房间中选择娃娃最多的房间，并取走该房间全部娃娃。如果多个房间并列最多，由你选择其中一个。",
        ],
      },
      {
        title: "赠送与超额",
        items: [
          "如果你本回合至少向任意房间放入了 1 个娃娃，并且保留过 1，那么每个被保留的 1 都可以让你把 1 个自己的娃娃赠送给另一名玩家。赠送是可选的，并且一次赠送 1 个。",
          "每个回合结束后，所有玩家都要检查手中娃娃数量。任何玩家超过 10 个娃娃时，超过 10 的部分会进入 11 号房间。",
        ],
      },
      {
        title: "获胜",
        items: [
          "在自己的回合中暂时没有娃娃，并不会立刻获胜。获胜检查只发生在某名玩家的回合开始时。",
          "如果某名玩家的回合开始时手中有 0 个娃娃，游戏立刻结束，该玩家获胜。",
        ],
      },
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
          <RulesButton text={text} onClick={() => setRulesOpen(true)} />
          <LanguageButton text={text} onClick={switchLanguage} />
        </div>
        {rulesOpen && (
          <RulesPanel onClose={() => setRulesOpen(false)} text={text} />
        )}
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
            <RulesButton text={text} onClick={() => setRulesOpen(true)} />
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

function RulesButton({ text, onClick }) {
  return (
    <button className="rules-button" onClick={onClick} aria-label={text.rules}>
      <BookOpen size={20} />
      {text.rules}
    </button>
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
          {text.rulesSections.map((section) => (
            <section className="rules-section" key={section.title}>
              <h3>{section.title}</h3>
              <ul>
                {section.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </section>
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
