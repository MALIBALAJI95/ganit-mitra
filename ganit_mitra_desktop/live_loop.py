import os
import sys
import time
import argparse
from typing import Optional, Dict, Any
import numpy as np
import soundfile as sf
import sounddevice as sd

from ganit_mitra_desktop.audio_gate import AudioGate, AudioGateResult
from ganit_mitra_desktop.asr_engine import ASREngine, ASRResult
from ganit_mitra_desktop.input_classifier import InputClassifier, ClassificationResult
from ganit_mitra_desktop.parser import MarathiSpokenMathParser, MathAST
from ganit_mitra_desktop.math_engine import MathEngine, MathSolution
from ganit_mitra_desktop.audio_bank import NumberAudioBank

class GanitMitraSession:
    def __init__(self,
                 vad_model: str = "models/vad/silero_vad.onnx",
                 asr_model: str = "models/asr/model.int8.onnx",
                 tokens_path: str = "models/asr/tokens.txt"):
        print("\n[Init] Initializing Ganit Mitra Desktop Prototype...")
        t0 = time.time()
        self.audio_gate = AudioGate(vad_model)
        self.asr = ASREngine(asr_model, tokens_path)
        self.classifier = InputClassifier()
        self.parser = MarathiSpokenMathParser()
        self.math_engine = MathEngine()
        self.audio_bank = NumberAudioBank()
        
        # Dialogue State Machine: 'IDLE' | 'AWAITING_CONFIRMATION'
        self.dialogue_state = "IDLE"
        self.pending_ast: Optional[MathAST] = None
        print(f"[Init] Initialized completely in {time.time() - t0:.2f}s!\n")

    def process_turn(self, audio: np.ndarray, source_name: str = "Audio", play_speech: bool = True):
        t_start = time.perf_counter()
        
        # Stage 1: Audio Gate
        t0 = time.perf_counter()
        gate_res = self.audio_gate.analyze(audio)
        t_gate = (time.perf_counter() - t0) * 1000.0

        # Stage 2: ASR
        t0 = time.perf_counter()
        if gate_res.status in ("speech", "noise"):
            asr_res = self.asr.transcribe(audio)
        else:
            asr_res = ASRResult(text="", tokens=[], overall_confidence=0.0, min_confidence=0.0, latency_ms=0.0)
        t_asr = (time.perf_counter() - t0) * 1000.0

        # Stage 3: Input Classifier
        t0 = time.perf_counter()
        cls_res = self.classifier.classify(gate_res, asr_res)
        t_class = (time.perf_counter() - t0) * 1000.0

        # Stage 4: Parser & Dialogue Logic
        t0 = time.perf_counter()
        spoken_reply_text = ""
        speech_audio_to_play = None
        parsed_ast = None
        solution = None

        if cls_res.decision.label == "REPROMPT":
            spoken_reply_text = cls_res.reprompt_prompt
        elif self.dialogue_state == "AWAITING_CONFIRMATION":
            # Expecting confirmation "हो" or "नाही"
            if cls_res.intent.label == "command":
                cmd = cls_res.intent.metadata.get("command")
                if cmd == "yes":
                    # Child confirmed "हो"!
                    if self.pending_ast:
                        if self.pending_ast.op in ("ADD", "SUB", "MUL", "DIV"):
                            l_val = self.pending_ast.left.value
                            r_val = self.pending_ast.right.value
                            solution = self.math_engine.solve(self.pending_ast.op, l_val, r_val)
                            spoken_reply_text = f"बरोबर! उत्तर आहे: {solution.result_str_mr} ({solution.result_int}). {solution.full_speech_mr}"
                            speech_audio_to_play = self.audio_bank.assemble_answer(solution.result_int)
                        elif self.pending_ast.op == "TABLE":
                            l_val = self.pending_ast.left.value if self.pending_ast.left else 5
                            solution = self.math_engine.solve("TABLE", l_val)
                            spoken_reply_text = solution.full_speech_mr
                            speech_audio_to_play = self.audio_bank.synthesize_sentence(solution.full_speech_mr[:180])
                        elif self.pending_ast.op == "SHAPE_SQUARE":
                            l_val = self.pending_ast.left.value if self.pending_ast.left else None
                            solution = self.math_engine.solve("SHAPE_SQUARE", l_val, sub_type=self.pending_ast.unit)
                            spoken_reply_text = f"बरोबर! {solution.full_speech_mr}"
                            speech_audio_to_play = self.audio_bank.synthesize_sentence(spoken_reply_text)
                        elif self.pending_ast.op == "SHAPE_RECTANGLE":
                            l_val = self.pending_ast.left.value if self.pending_ast.left else None
                            r_val = self.pending_ast.right.value if self.pending_ast.right else None
                            solution = self.math_engine.solve("SHAPE_RECTANGLE", l_val, r_val, sub_type=self.pending_ast.unit)
                            spoken_reply_text = f"बरोबर! {solution.full_speech_mr}"
                            speech_audio_to_play = self.audio_bank.synthesize_sentence(spoken_reply_text)
                        elif self.pending_ast.op == "NUMBER_ONLY":
                            l_val = self.pending_ast.left.value if self.pending_ast.left else 0
                            solution = self.math_engine.solve("NUMBER_ONLY", l_val)
                            spoken_reply_text = f"बरोबर! {solution.full_speech_mr}"
                            speech_audio_to_play = self.audio_bank.assemble_answer(int(solution.result_val))
                    self.dialogue_state = "IDLE"
                    self.pending_ast = None
                elif cmd == "no":
                    spoken_reply_text = "काही हरकत नाही, प्रश्न पुन्हा सांगशील का?"
                    self.dialogue_state = "IDLE"
                    self.pending_ast = None
                else:
                    spoken_reply_text = "कृपया 'हो' किंवा 'नाही' सांगा."
            else:
                spoken_reply_text = "कृपया 'हो' किंवा 'नाही' सांगा."
        else:
            # Normal turn: expect math question or number
            parsed_ast = self.parser.parse(asr_res.text)
            if parsed_ast.ambiguity.is_ambiguous:
                spoken_reply_text = parsed_ast.ambiguity.clarification_question
            elif parsed_ast.op in ("ADD", "SUB", "MUL", "DIV"):
                # Mandatory READ-BACK + CONFIRM
                a = int(parsed_ast.left.value)
                b = int(parsed_ast.right.value)
                op_mr = {"ADD": "अधिक", "SUB": "वजा", "MUL": "गुणिले", "DIV": "भागिले"}.get(parsed_ast.op, parsed_ast.op)
                spoken_reply_text = f"तू विचारलंस: {a} {op_mr} {b} किती? बरोबर आहे का? (हो / नाही म्हणा)"
                speech_audio_to_play = self.audio_bank.assemble_readback(parsed_ast.op, a, b)
                self.pending_ast = parsed_ast
                self.dialogue_state = "AWAITING_CONFIRMATION"
            elif parsed_ast.op == "TABLE":
                t_val = int(parsed_ast.left.value) if parsed_ast.left else 5
                spoken_reply_text = f"तू विचारलंस: {t_val} चा पाढा. बरोबर आहे का? (हो / नाही म्हणा)"
                self.pending_ast = parsed_ast
                self.dialogue_state = "AWAITING_CONFIRMATION"
            elif parsed_ast.op == "SHAPE_SQUARE":
                sub_mr = "परिमिती" if parsed_ast.unit == "PERIMETER" else "क्षेत्रफळ"
                s_txt = f"बाजू {int(parsed_ast.left.value)} असलेल्या " if parsed_ast.left else ""
                spoken_reply_text = f"तू विचारलंस: {s_txt}चौरसाचे {sub_mr}. बरोबर आहे का? (हो / नाही म्हणा)"
                self.pending_ast = parsed_ast
                self.dialogue_state = "AWAITING_CONFIRMATION"
            elif parsed_ast.op == "SHAPE_RECTANGLE":
                sub_mr = "परिमिती" if parsed_ast.unit == "PERIMETER" else "क्षेत्रफळ"
                l_txt = f"लांबी {int(parsed_ast.left.value)} व रुंदी {int(parsed_ast.right.value)} असलेल्या " if parsed_ast.left and parsed_ast.right else ""
                spoken_reply_text = f"तू विचारलंस: {l_txt}आयताचे {sub_mr}. बरोबर आहे का? (हो / नाही म्हणा)"
                self.pending_ast = parsed_ast
                self.dialogue_state = "AWAITING_CONFIRMATION"
            elif parsed_ast.op == "NUMBER_ONLY":
                val = int(parsed_ast.left.value)
                spoken_reply_text = f"तू संख्या सांगितलीस: {val}. बरोबर आहे का?"
                self.pending_ast = parsed_ast
                self.dialogue_state = "AWAITING_CONFIRMATION"
            else:
                spoken_reply_text = "गणिताचा प्रश्न पुन्हा सांगशील का?"

        t_logic = (time.perf_counter() - t0) * 1000.0
        t_total = (time.perf_counter() - t_start) * 1000.0

        # Print Debug Panel
        self.print_full_panel(source_name, gate_res, asr_res, cls_res, parsed_ast, solution,
                              spoken_reply_text, t_gate, t_asr, t_class, t_logic, t_total)

        if play_speech and speech_audio_to_play is not None and len(speech_audio_to_play) > 0:
            try:
                sd.play(speech_audio_to_play[:32000], samplerate=16000)
            except Exception:
                pass

        return {
            "transcript": asr_res.text,
            "decision": cls_res.decision.label,
            "spoken_reply": spoken_reply_text,
            "state": self.dialogue_state,
            "latency_ms": t_total,
            "speech_audio": speech_audio_to_play,
            "solution": solution,
            "gate": gate_res,
            "asr": asr_res,
            "classifier": cls_res,
            "ast": parsed_ast
        }

    def print_full_panel(self, source: str, gate: AudioGateResult, asr: ASRResult,
                         cls: ClassificationResult, ast: Optional[MathAST],
                         sol: Optional[MathSolution], reply: str,
                         t_gate: float, t_asr: float, t_class: float, t_logic: float, t_total: float):
        border = "=" * 78
        print("\n" + border)
        print(f"|  गणित मित्र FULL LOOP DEBUG PANEL  |  State: {self.dialogue_state:<12} | {t_total:6.1f} ms  |")
        print(border)
        print(f" 1. AUDIO GATE     : [{gate.status.upper():^10}]  (conf: {gate.confidence:.2f}, {t_gate:.1f}ms)")
        print(f"    - Duration     : {gate.duration:.2f}s (speech: {gate.speech_duration:.2f}s, RMS: {gate.rms_energy:.4f})")
        print("-" * 78)
        print(f" 2. ASR TRANSCRIPT : \"{asr.text}\" (conf: {asr.overall_confidence:.1%}, min: {asr.min_confidence:.1%}, {t_asr:.1f}ms)")
        if asr.tokens:
            tok_s = [f"{t.token}({t.confidence:.2f})" for t in asr.tokens[:7]]
            print(f"    - Tokens       : {' '.join(tok_s)}")
        print("-" * 78)
        print(f" 3. CLASSIFIER     :")
        print(f"    - language_check: [{cls.language_check.label}] ({cls.language_check.confidence:.2f})")
        print(f"    - intent        : [{cls.intent.label}] ({cls.intent.confidence:.2f}, meta: {cls.intent.metadata})")
        print(f"    - decision      : [{cls.decision.label}] (reason: {cls.decision.metadata.get('reason')})")
        print("-" * 78)
        if ast:
            l_val = ast.left.value if ast.left else None
            r_val = ast.right.value if ast.right else None
            print(f" 4. PARSER AST     : OP = {ast.op} | Left = {l_val} | Right = {r_val} | Ambiguous = {ast.ambiguity.is_ambiguous}")
        if sol:
            print(f" 5. MATH SOLUTION  : Ans = {sol.result_int} ({sol.result_str_mr})")
            for s in sol.steps:
                print(f"    - Step {s.step_num}      : {s.explanation_mr}")
        print("-" * 78)
        print(f" 6. SPOKEN REPLY   : \"{reply}\"")
        print("-" * 78)
        print(f" 7. TIMING (ms)    : Gate: {t_gate:.1f} | ASR: {t_asr:.1f} | Classifier: {t_class:.1f} | Logic: {t_logic:.1f} | Sum: {t_total:.1f}")
        print(border + "\n")

def main():
    parser = argparse.ArgumentParser(description="Ganit Mitra Full Loop Prototype")
    parser.add_argument("--wav", type=str, help="Process single WAV file")
    args = parser.parse_args()

    session = GanitMitraSession()
    if args.wav:
        data, sr = sf.read(args.wav)
        if len(data.shape) > 1: data = data[:, 0]
        session.process_turn(data.astype(np.float32), source_name=os.path.basename(args.wav))
    else:
        print("Run with --wav <file>")

if __name__ == '__main__':
    main()
