# debate/debate_controller.py
# ──────────────────────────────────────────────────────────────
import time
from agents.conversation_manager import ConversationManager
from debate.context_mode import ContextMode

class DebateController:
    def __init__(self, agents, topic,
                 context_mode: ContextMode = ContextMode.HYBRID,
                 max_rounds: int = 3):
        self.agents     = agents
        self.topic      = topic
        self.max_rounds = max_rounds
        self.cm         = ConversationManager(mode=context_mode)

        # initialise log
        self.cm.start_debate(topic, agents)

    # ──────────────────────────────────────────────────────────
    def run(self):
        self._opening_statements()
        for r in range(2, self.max_rounds):
            self._rebuttal_round(r)
        self._closing_round()
        self._summary()

    # ───────────────────────── rounds ─────────────────────────
    def _opening_statements(self):
        print("\n=== ROUND 1 • Opening Statements ===")
        self.cm.advance_round()

        for ag in self.agents:
            reply = ag.respond(self.topic,
                               context="",
                               round_number=1,
                               stage="opening")     # ← fixed
            self.cm.add_message(ag.name, reply)
            print(f"\n{ag.name}: {reply}")
            time.sleep(0.4)

    def _rebuttal_round(self, num):
        print(f"\n=== ROUND {num} • Rebuttals ===")
        self.cm.advance_round()

        for ag in self.agents:
            ctx   = self.cm.context_for(ag.name)
            reply = ag.respond(self.topic,
                               context=ctx,
                               round_number=num,
                               stage="rebuttal")    # ← fixed
            self.cm.add_message(ag.name, reply)
            print(f"\n{ag.name}: {reply}")
            time.sleep(0.4)

    def _closing_round(self):
        print("\n=== FINAL ROUND • Closing Arguments ===")
        self.cm.advance_round()

        for ag in self.agents:
            ctx   = self.cm.context_for(ag.name)
            reply = ag.respond(self.topic,
                               context=ctx,
                               round_number=self.max_rounds,
                               stage="closing")      # ← fixed
            self.cm.add_message(ag.name, reply)
            print(f"\n{ag.name}: {reply}")
            time.sleep(0.4)

    # ───────────────────────── summary ────────────────────────
    def _summary(self):
        print("\n=== Debate complete ===")
        print(f"Total messages: {len(self.cm.history)}")
        print(f"Context mode  : {self.cm.mode.value}")
