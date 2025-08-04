# agents/conversation_manager.py
# ──────────────────────────────────────────────────────────────
import os, json
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from debate.context_mode import ContextMode

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# deterministic config for summaries
SUMMARY_CFG = genai.GenerationConfig(
    temperature=0.0,
    max_output_tokens=400,
    top_p=0.95,
    top_k=40,
)

class ConversationManager:
    """
    Keeps the full debate log and returns context strings according
    to ContextMode (FULL, SUMMARIZED, HYBRID).
    """
    def __init__(self,
                 mode: ContextMode = ContextMode.HYBRID,
                 window_size: int = 3,
                 summary_every_n_turns: int = 6):
        self.mode        = mode
        self.window_size = window_size
        self.summary_every_n_turns = summary_every_n_turns

        self.history   = []          # list[dict]
        self.summary   = ""          # rolling summary
        self.round     = 0
        self.topic     = ""
        self.participants = []
        self.turns_since_last_summary = 0

        self.summary_model = genai.GenerativeModel("gemini-1.5-flash")

    # ───────────────────────── Session helpers ───────────────────────── #
    def start_debate(self, topic: str, agents):
        """Call once from DebateController before round 1."""
        self.topic        = topic
        self.participants = [a.name for a in agents]
        self.history.clear()
        self.round = 0
        self.summary = ""
        self.turns_since_last_summary = 0

        self.add_system_message(f"Debate started on '{topic}'.")
        self.add_system_message("Participants: " + ", ".join(self.participants))

    def advance_round(self):
        self.round += 1
        self.add_system_message(f"Round {self.round} begins.")

    # ───────────────────────── Logging utilities ─────────────────────── #
    def add_system_message(self, text: str):
        self._add_message("SYSTEM", text, "system")

    def add_message(self, speaker: str, text: str):
        self._add_message(speaker, text, "response")

    def _add_message(self, speaker: str, text: str, kind: str):
        self.history.append({
            "time": datetime.utcnow().isoformat(timespec="seconds"),
            "round": self.round,
            "agent": speaker,
            "message": text,
            "type": kind
        })

        if kind != "system":
            self.turns_since_last_summary += 1
            if (self.mode in (ContextMode.HYBRID, ContextMode.SUMMARIZED) and
                self.turns_since_last_summary >= self.summary_every_n_turns):
                self._update_summary()

    # ───────────────────────── Context for agents ────────────────────── #
    def context_for(self, requesting_agent: str) -> str:
        """Return context string according to mode."""
        if self.mode == ContextMode.FULL:
            return self._raw_history(exclude=requesting_agent)

        if self.mode == ContextMode.SUMMARIZED:
            return self.summary or "[No summary yet]"

        # HYBRID
        recent = self._recent_window(exclude=requesting_agent)
        bits   = []
        if self.summary:
            bits.append(f"[Earlier summary]\n{self.summary}")
        if recent:
            bits.append(recent)
        return "\n".join(bits) or "[No context]"

    # ───────────────────────── Internal helpers ──────────────────────── #
    def _raw_history(self, exclude: str) -> str:
        return "\n".join(
            f"{m['agent']}: {m['message']}"
            for m in self.history
            if m["type"] != "system" and m["agent"] != exclude
        )

    def _recent_window(self, exclude: str) -> str:
        msgs = [m for m in self.history if m["type"] != "system"]
        window = msgs[-self.window_size*2:]   # heuristic
        return "\n".join(
            f"{m['agent']}: {m['message']}"
            for m in window if m["agent"] != exclude
        )

    def _update_summary(self):
        """Summarise everything except last window_size msgs."""
        msgs = [m for m in self.history if m["type"] != "system"]
        if len(msgs) <= self.window_size:
            return
        old = msgs[:-self.window_size]

        prompt = (
            "Summarise the following multi-agent debate in ≤300 words. "
            "Preserve key claims and who made them.\n\n" +
            "\n".join(f"{m['agent']}: {m['message']}" for m in old) +
            "\n\nSummary:"
        )
        try:
            resp = self.summary_model.generate_content(
                prompt,
                generation_config=SUMMARY_CFG
            )
            self.summary = resp.text.strip()
        except Exception as e:
            self.summary += f"\n[Summary failed: {e}]"

        self.turns_since_last_summary = 0

    # ───────────────────────── Export (optional) ─────────────────────── #
    def export_json(self, path="debate_export.json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "topic": self.topic,
                "mode":  self.mode.value,
                "history": self.history
            }, f, indent=2)
        return path
