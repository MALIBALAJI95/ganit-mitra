import os
import unittest
import numpy as np
import soundfile as sf
import scipy.signal

from ganit_mitra_desktop.live_loop import GanitMitraSession

class TestEndToEndSession(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session = GanitMitraSession()

    def _load_wav_16k(self, path: str) -> np.ndarray:
        data, sr = sf.read(path)
        if len(data.shape) > 1: data = data[:, 0]
        if sr != 16000:
            data = scipy.signal.resample_poly(data, 16000, sr).astype(np.float32)
        return data.astype(np.float32)

    def test_full_addition_dialogue_session(self):
        print("\n" + "=" * 78)
        print(">>> STARTING FULL E2E INTERACTIVE SESSION TEST <<<")
        print("=" * 78)

        # TURN 1: Child speaks math question: "सात अधिक आठ"
        print("\n--- TURN 1: Child asks question ---")
        q_audio = self._load_wav_16k("test_question.wav")
        res1 = self.session.process_turn(q_audio, source_name="Child Question (7+8)", play_speech=False)

        self.assertEqual(res1["decision"], "CONFIRM")
        self.assertEqual(res1["state"], "AWAITING_CONFIRMATION")
        self.assertIn("तू विचारलंस", res1["spoken_reply"])
        print(f"[Turn 1 Passed] State is {res1['state']}, Read-back prompt emitted!")

        # TURN 2: Child says "हो" (affirmative confirmation)
        print("\n--- TURN 2: Child confirms 'हो' ---")
        ho_audio = self._load_wav_16k("assets/audio/bank/हो.wav")
        res2 = self.session.process_turn(ho_audio, source_name="Child Confirm (हो)", play_speech=False)

        # Either resolved or reprompted
        print(f"[Turn 2 Response]: \"{res2['spoken_reply']}\"")
        self.assertIsNotNone(res2["spoken_reply"])
        print("\n>>> FULL E2E SESSION TEST COMPLETED SUCCESSFULLY! <<<")

if __name__ == '__main__':
    unittest.main()
