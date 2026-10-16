package org.ganitmitra.core.domain.speech

import kotlinx.coroutines.flow.StateFlow
import org.ganitmitra.core.domain.model.SpeechInputResult
import org.ganitmitra.core.domain.model.VoiceCommand

/**
 * Speech recognition contract for Ganit Mitra.
 * Supports dual-mode recognition:
 * - Mode A: Constrained control commands (पुढे, मागे, पुन्हा, मदत...)
 * - Mode B: Numeric answers (० ते १०००)
 */
interface SpeechInput {

    /** Current listening and processing state */
    val recognitionState: StateFlow<RecognitionState>

    /**
     * Start listening in Mode A (navigation/control commands).
     */
    fun startListeningForCommands(
        allowedCommands: Set<VoiceCommand> = VoiceCommand.values().toSet(),
        onResult: (SpeechInputResult) -> Unit
    )

    /**
     * Start listening in Mode B (Marathi number words 0 to 1000).
     */
    fun startListeningForNumber(
        validRange: IntRange = 0..1000,
        onResult: (SpeechInputResult) -> Unit
    )

    /**
     * Stop listening and release microphone immediately.
     */
    fun stopListening()

    /**
     * Unload models from memory when navigating away to protect RAM.
     */
    fun release()
}

enum class RecognitionState {
    IDLE,
    PREPARING,
    LISTENING,
    PROCESSING,
    ERROR
}

/**
 * Audio playback contract for pre-rendered Ogg Opus lesson dialogues
 * and dynamic sprite soundboard.
 */
interface AudioPlayer {

    /** Current playback state */
    val isPlaying: StateFlow<Boolean>

    /**
     * Play a pre-rendered Opus audio file from assets.
     */
    fun playAssetAudio(assetPath: String, onCompletion: () -> Unit = {})

    /**
     * Play a spoken Marathi number using the pre-rendered soundboard sprite.
     * Guaranteed zero-latency, authentic pronunciation.
     */
    fun playNumberWord(number: Int, onCompletion: () -> Unit = {})

    /** Pause playback */
    fun pause()

    /** Stop and reset */
    fun stop()

    /** Release ExoPlayer / audio resources */
    fun release()
}
