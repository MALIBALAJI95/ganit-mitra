package org.ganitmitra.core.domain.state

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import org.ganitmitra.core.domain.engine.DeterministicMathEngine
import org.ganitmitra.core.domain.engine.MisconceptionCategory
import org.ganitmitra.core.domain.engine.MisconceptionDiagnosis
import org.ganitmitra.core.domain.model.AdditionStepBreakdown
import org.ganitmitra.core.domain.model.NumeralSystem
import org.ganitmitra.core.domain.model.PlaceValueComponents
import org.ganitmitra.core.domain.model.VoiceCommand

/**
 * The 7 Pedagogical Stages for Ganit Mitra.
 */
enum class LessonStage(val stageNumber: Int, val titleMr: String) {
    RURAL_HOOK(1, "गावचा आठवडी बाजार (हूक)"),
    VISUAL_MANIPULATIVE(2, "स्थानमूल्य नाणी-नोटा (मॅनिप्युलेटिव्ह)"),
    SPOKEN_EXPLANATION(3, "चिनूची सोपी समजूत (स्पष्टीकरण)"),
    GUIDED_PRACTICE(4, "मार्गदर्शित सराव व हिंट्स (सराव)"),
    INDEPENDENT_PRACTICE(5, "स्वाध्याय (आत्मविश्वासाने सोडवणे)"),
    EXPLAIN_BACK_CHECK(6, "कारण सांगा (Explain-Back)"),
    MASTERY_REVIEW(7, "प्रावीण्य व उजळणी (प्रगती नोंद)")
}

data class ManipulativeState(
    val hundreds: Int = 3,
    val tens: Int = 7,
    val units: Int = 12,
    val isRegrouped: Boolean = false,
    val carryBadgeVisible: Boolean = false
)

data class LessonUiState(
    val stage: LessonStage = LessonStage.RURAL_HOOK,
    val numeralSystem: NumeralSystem = NumeralSystem.DEVANAGARI,
    val mascotDialogueMr: String = "",
    val currentAudioFile: String = "",
    val manipulativeState: ManipulativeState = ManipulativeState(),
    val currentHintLevel: Int = 0, // 0 = none, 1 = nudge, 2 = visual, 3 = walkthrough
    val activeHintTextMr: String? = null,
    val independentStreak: Int = 0,
    val targetStreak: Int = 3,
    val currentProblem: Pair<Int, Int> = Pair(147, 235),
    val studentInputText: String = "",
    val feedbackMessageMr: String? = null,
    val isAnswerCorrect: Boolean? = null,
    val isListening: Boolean = false,
    val voicePromptHelp: String = "बोला किंवा टॅप करा",
    val sessionMistakeCount: Int = 0,
    val sessionDurationSeconds: Int = 0,
    val isLessonCompleted: Boolean = false
)

/**
 * State machine managing the 7-step pedagogical cycle for Class 3 MVP.
 * Pure Kotlin, zero Android UI coupling, 100% testable.
 */
class LessonStateMachine(
    private val onProgressSaved: (conceptId: String, score: Float, mistakes: Int) -> Unit = { _, _, _ -> }
) {
    private val _uiState = MutableStateFlow(
        LessonUiState(
            mascotDialogueMr = "आज आठवडी बाजारात गण्याने भोपळे विकून ₹१४७ मिळवले आणि वांग्यांचे ₹२३५ मिळवले. गण्याकडे एकूण किती रुपये जमले? चला हिशोब करूया!",
            currentAudioFile = "audio/std3/add_03/hook_bajar_hisob.opus"
        )
    )
    val uiState: StateFlow<LessonUiState> = _uiState.asStateFlow()

    fun toggleNumeralSystem() {
        val next = if (_uiState.value.numeralSystem == NumeralSystem.DEVANAGARI) {
            NumeralSystem.WESTERN
        } else {
            NumeralSystem.DEVANAGARI
        }
        _uiState.value = _uiState.value.copy(numeralSystem = next)
    }

    fun handleVoiceCommand(command: VoiceCommand) {
        when (command) {
            VoiceCommand.NEXT -> advanceStage()
            VoiceCommand.BACK -> previousStage()
            VoiceCommand.REPEAT -> repeatCurrentAudio()
            VoiceCommand.HELP -> requestNextHint()
            VoiceCommand.TELL -> provideAutoExplanation()
            VoiceCommand.YES -> handleAffirmation(true)
            VoiceCommand.NO -> handleAffirmation(false)
            VoiceCommand.STOP -> { /* pause */ }
        }
    }

    fun handleNumericAnswer(answer: Int) {
        val s = _uiState.value
        val (op1, op2) = s.currentProblem
        val breakdown = DeterministicMathEngine.decomposeAddition(op1, op2)

        if (answer == breakdown.finalSum) {
            val nextStreak = s.independentStreak + 1
            _uiState.value = s.copy(
                isAnswerCorrect = true,
                studentInputText = answer.toString(),
                feedbackMessageMr = "शाब्बास! अतिशय अचूक उत्तर: $answer रुपये!",
                independentStreak = nextStreak,
                currentAudioFile = "audio/common/correct_cheer.opus"
            )
            if (nextStreak >= s.targetStreak && s.stage == LessonStage.INDEPENDENT_PRACTICE) {
                advanceStage()
            } else if (s.stage == LessonStage.INDEPENDENT_PRACTICE) {
                loadNextIndependentProblem()
            }
        } else {
            // Misconception diagnosis
            val diagnosis = DeterministicMathEngine.diagnoseMisconception(op1, op2, answer)
            _uiState.value = s.copy(
                isAnswerCorrect = false,
                studentInputText = answer.toString(),
                sessionMistakeCount = s.sessionMistakeCount + 1,
                feedbackMessageMr = diagnosis?.feedbackMr ?: "पुन्हा विचार करा! चला एकत्र पायरी तपासूया.",
                currentAudioFile = "audio/std3/add_03/err_forgot_carry.opus"
            )
            // Auto-trigger level 1 hint if child errs
            if (_uiState.value.currentHintLevel == 0) {
                requestNextHint()
            }
        }
    }

    fun triggerRegroupingManipulative() {
        val m = _uiState.value.manipulativeState
        if (!m.isRegrouped) {
            _uiState.value = _uiState.value.copy(
                manipulativeState = m.copy(
                    hundreds = 3,
                    tens = 8,
                    units = 2,
                    isRegrouped = true,
                    carryBadgeVisible = true
                ),
                mascotDialogueMr = "छान! १० सुटी नाणी एकत्र येऊन त्यांचा १ निळा ₹१० चा गट्टा बनला आणि तो दशकाच्या घरात गेला. एककात २ नाणी उरली!",
                currentAudioFile = "audio/std3/add_03/step_2_carry.opus"
            )
        }
    }

    fun requestNextHint() {
        val currentLevel = _uiState.value.currentHintLevel
        val nextLevel = (currentLevel + 1).coerceAtMost(3)
        val hintText = when (nextLevel) {
            1 -> "स्तर १ (सुगावा): एककाच्या घरात ७ + ५ = १२ झाले. १२ मधला १ दशक कुठे जाईल बरं?"
            2 -> "स्तर २ (दृश्य मदत): बघा, १० सुटी नाणी एकत्र येऊन १ नवीन ₹१० चा गट्टा बनला आहे!"
            3 -> "स्तर ३ (उकल): एककाच्या घरात २ लिहा आणि दशकाच्या डोक्यावर १ हातचा ठेवा. मग १ + ४ + ३ = ८ लिहा!"
            else -> null
        }
        _uiState.value = _uiState.value.copy(
            currentHintLevel = nextLevel,
            activeHintTextMr = hintText,
            currentAudioFile = "audio/std3/add_03/hint_l${nextLevel}.opus"
        )
    }

    fun handleExplainBackOptionSelected(isCorrect: Boolean) {
        if (isCorrect) {
            _uiState.value = _uiState.value.copy(
                feedbackMessageMr = "अगदी बरोबर! १० सुटी नाणी मिळूनच १ दशक (₹१०) बनतो म्हणूनच तो दशकाच्या घरात जातो.",
                currentAudioFile = "audio/std3/add_03/explain_correct.opus"
            )
            advanceStage()
        } else {
            _uiState.value = _uiState.value.copy(
                feedbackMessageMr = "विचार करा: १ नाणे लहान असले तरी त्याचे मूल्य आणि घराचा नियम काय आहे?",
                currentAudioFile = "audio/std3/add_03/explain_retry.opus"
            )
        }
    }

    fun advanceStage() {
        val current = _uiState.value.stage
        val nextStage = when (current) {
            LessonStage.RURAL_HOOK -> LessonStage.VISUAL_MANIPULATIVE
            LessonStage.VISUAL_MANIPULATIVE -> LessonStage.SPOKEN_EXPLANATION
            LessonStage.SPOKEN_EXPLANATION -> LessonStage.GUIDED_PRACTICE
            LessonStage.GUIDED_PRACTICE -> LessonStage.INDEPENDENT_PRACTICE
            LessonStage.INDEPENDENT_PRACTICE -> LessonStage.EXPLAIN_BACK_CHECK
            LessonStage.EXPLAIN_BACK_CHECK -> LessonStage.MASTERY_REVIEW
            LessonStage.MASTERY_REVIEW -> LessonStage.MASTERY_REVIEW
        }

        if (nextStage == LessonStage.MASTERY_REVIEW && current != LessonStage.MASTERY_REVIEW) {
            // Save progress locally
            val mistakes = _uiState.value.sessionMistakeCount
            val score = if (mistakes == 0) 1.0f else (1.0f / (1.0f + (mistakes * 0.15f))).coerceIn(0.5f, 0.95f)
            onProgressSaved("STD3_MATH_ADD_03", score, mistakes)
            _uiState.value = _uiState.value.copy(
                stage = nextStage,
                isLessonCompleted = true,
                mascotDialogueMr = "अभिनंदन! तुम्ही ३-अंकी संख्यांची हातच्याची बेरीज यशस्वीपणे शिकलात. तुमचे प्रावीण्य नोंदवले गेले आहे!",
                currentAudioFile = "audio/std3/add_03/mastery_cheer.opus"
            )
            return
        }

        _uiState.value = _uiState.value.copy(
            stage = nextStage,
            currentHintLevel = 0,
            activeHintTextMr = null,
            feedbackMessageMr = null,
            isAnswerCorrect = null
        )
    }

    fun previousStage() {
        val current = _uiState.value.stage
        val prev = when (current) {
            LessonStage.RURAL_HOOK -> LessonStage.RURAL_HOOK
            LessonStage.VISUAL_MANIPULATIVE -> LessonStage.RURAL_HOOK
            LessonStage.SPOKEN_EXPLANATION -> LessonStage.VISUAL_MANIPULATIVE
            LessonStage.GUIDED_PRACTICE -> LessonStage.SPOKEN_EXPLANATION
            LessonStage.INDEPENDENT_PRACTICE -> LessonStage.GUIDED_PRACTICE
            LessonStage.EXPLAIN_BACK_CHECK -> LessonStage.INDEPENDENT_PRACTICE
            LessonStage.MASTERY_REVIEW -> LessonStage.EXPLAIN_BACK_CHECK
        }
        _uiState.value = _uiState.value.copy(stage = prev)
    }

    private fun loadNextIndependentProblem() {
        val (op1, op2) = DeterministicMathEngine.generateProblem(requireCarryingInUnits = true)
        _uiState.value = _uiState.value.copy(
            currentProblem = Pair(op1, op2),
            studentInputText = "",
            feedbackMessageMr = null,
            isAnswerCorrect = null
        )
    }

    private fun repeatCurrentAudio() { /* replay current audio file */ }
    private fun provideAutoExplanation() { requestNextHint() }
    private fun handleAffirmation(isYes: Boolean) {
        if (isYes && _uiState.value.stage == LessonStage.RURAL_HOOK) advanceStage()
    }
}
