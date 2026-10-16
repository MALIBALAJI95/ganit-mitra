package org.ganitmitra.core.domain.model

/**
 * Numeral system representation.
 * Supports Devanagari (१, २, ३...) and Western (1, 2, 3...) with instant conversion.
 */
enum class NumeralSystem {
    DEVANAGARI,
    WESTERN;

    fun format(number: Int): String {
        val westernStr = number.toString()
        if (this == WESTERN) return westernStr
        val devanagariDigits = charArrayOf('०', '१', '२', '३', '४', '५', '६', '७', '८', '९')
        val sb = StringBuilder()
        for (ch in westernStr) {
            if (ch in '0'..'9') {
                sb.append(devanagariDigits[ch - '0'])
            } else {
                sb.append(ch)
            }
        }
        return sb.toString()
    }
}

/**
 * Representation of Place Value components for 3-digit numbers.
 */
data class PlaceValueComponents(
    val hundreds: Int, // शतक (०-९)
    val tens: Int,     // दशक (०-९)
    val units: Int     // एकक (०-९)
) {
    val totalValue: Int get() = (hundreds * 100) + (tens * 10) + units

    companion object {
        fun fromInt(value: Int): PlaceValueComponents {
            require(value in 0..999) { "Value must be in 0..999, got $value" }
            val h = value / 100
            val rem = value % 100
            val t = rem / 10
            val u = rem % 10
            return PlaceValueComponents(hundreds = h, tens = t, units = u)
        }
    }
}

/**
 * Step verification for 3-digit addition with carrying.
 */
data class AdditionStepBreakdown(
    val op1: Int,
    val op2: Int,
    val unitsSum: Int,
    val unitsResult: Int,
    val carryToTens: Int,
    val tensSum: Int,
    val tensResult: Int,
    val carryToHundreds: Int,
    val hundredsSum: Int,
    val finalSum: Int
)

/**
 * Voice commands recognized in Mode A.
 */
enum class VoiceCommand(val marathiSpoken: String) {
    NEXT("पुढे"),
    BACK("मागे"),
    REPEAT("पुन्हा"),
    TELL("सांग"),
    HELP("मदत"),
    YES("हो"),
    NO("नाही"),
    STOP("थांब")
}

/**
 * Speech Recognition Input state.
 */
sealed class SpeechInputResult {
    data class RecognizedCommand(val command: VoiceCommand) : SpeechInputResult()
    data class RecognizedNumber(val number: Int, val rawMarathi: String) : SpeechInputResult()
    data class Unrecognized(val rawSpeech: String, val confidence: Float) : SpeechInputResult()
    data class SilenceOrNoise(val reason: String) : SpeechInputResult()
    data class Error(val throwable: Throwable) : SpeechInputResult()
}
