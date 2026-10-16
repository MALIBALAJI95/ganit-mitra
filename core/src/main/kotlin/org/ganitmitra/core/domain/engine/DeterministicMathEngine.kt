package org.ganitmitra.core.domain.engine

import org.ganitmitra.core.domain.model.AdditionStepBreakdown
import org.ganitmitra.core.domain.model.PlaceValueComponents

/**
 * Deterministic math engine for Ganit Mitra.
 * Implements problem generation, step verification, and misconception classification
 * for Class 3 3-digit addition with carrying.
 */
object DeterministicMathEngine {

    /**
     * Decomposes the addition of two 3-digit numbers into step-by-step place-value columns.
     */
    fun decomposeAddition(op1: Int, op2: Int): AdditionStepBreakdown {
        require(op1 in 100..899 && op2 in 100..899) {
            "Operands must be 3-digit numbers, got op1=$op1, op2=$op2"
        }

        val c1 = PlaceValueComponents.fromInt(op1)
        val c2 = PlaceValueComponents.fromInt(op2)

        // 1. Units column
        val rawUnitsSum = c1.units + c2.units
        val carryToTens = rawUnitsSum / 10
        val unitsResult = rawUnitsSum % 10

        // 2. Tens column
        val rawTensSum = c1.tens + c2.tens + carryToTens
        val carryToHundreds = rawTensSum / 10
        val tensResult = rawTensSum % 10

        // 3. Hundreds column
        val rawHundredsSum = c1.hundreds + c2.hundreds + carryToHundreds
        val finalSum = op1 + op2

        return AdditionStepBreakdown(
            op1 = op1,
            op2 = op2,
            unitsSum = rawUnitsSum,
            unitsResult = unitsResult,
            carryToTens = carryToTens,
            tensSum = rawTensSum,
            tensResult = tensResult,
            carryToHundreds = carryToHundreds,
            hundredsSum = rawHundredsSum,
            finalSum = finalSum
        )
    }

    /**
     * Diagnoses common student misconceptions from an incorrect answer.
     */
    fun diagnoseMisconception(op1: Int, op2: Int, studentAnswer: Int): MisconceptionDiagnosis? {
        val correct = decomposeAddition(op1, op2)
        if (studentAnswer == correct.finalSum) return null

        val c1 = PlaceValueComponents.fromInt(op1)
        val c2 = PlaceValueComponents.fromInt(op2)

        // Case 1: Forgot units-to-tens carry
        if (correct.carryToTens > 0) {
            val tensNoCarry = c1.tens + c2.tens
            val hCarryNoCarry = tensNoCarry / 10
            val tensResNoCarry = tensNoCarry % 10
            val hSumNoCarry = c1.hundreds + c2.hundreds + hCarryNoCarry
            val forgotTensCarry = (hSumNoCarry * 100) + (tensResNoCarry * 10) + correct.unitsResult
            if (studentAnswer == forgotTensCarry) {
                return MisconceptionDiagnosis(
                    category = MisconceptionCategory.FORGOT_CARRY_UNITS_TO_TENS,
                    feedbackMr = "तुम्ही एककातून आलेला हातचा १ दशकात मिळवायला विसरलात का? पुन्हा बेरीज करा: १ + ${c1.tens} + ${c2.tens} = ${correct.tensResult} दशक."
                )
            }
        }

        // Case 2: Reversed carry and result in units (e.g. 7+5=12 -> wrote 1, carried 2)
        if (correct.carryToTens > 0 && correct.unitsSum in 11..19) {
            val reversedUnitsResult = correct.carryToTens
            val reversedCarry = correct.unitsResult
            val reversedTens = c1.tens + c2.tens + reversedCarry
            val reversedAnswer = (correct.hundredsSum * 100) + (reversedTens * 10) + reversedUnitsResult
            if (studentAnswer == reversedAnswer) {
                return MisconceptionDiagnosis(
                    category = MisconceptionCategory.DIGIT_REVERSAL_IN_CARRY,
                    feedbackMr = "१२ मध्ये २ एकक सुटे आहेत आणि १ दशक आहे! म्हणून २ खाली राहील आणि १ हातचा म्हणून दशकाच्या घरात जाईल."
                )
            }
        }

        // Case 3: Alignment error / added hundreds to tens
        return MisconceptionDiagnosis(
            category = MisconceptionCategory.GENERAL_CALCULATION_ERROR,
            feedbackMr = "चला पुन्हा पायरी-पायरीने करूया: आधी एकक, मग दशक आणि शेवटी शतक मोजूया."
        )
    }

    /**
     * Deterministic pseudo-random problem generator with guaranteed carrying.
     * Seeded for reproducibility and regression testing.
     */
    fun generateProblem(requireCarryingInUnits: Boolean = true, seed: Long? = null): Pair<Int, Int> {
        val rng = if (seed != null) java.util.Random(seed) else java.util.Random()
        while (true) {
            val h1 = 1 + rng.nextInt(7)
            val t1 = rng.nextInt(8)
            val u1 = if (requireCarryingInUnits) 5 + rng.nextInt(5) else 1 + rng.nextInt(4)

            val h2 = 1 + rng.nextInt(8 - h1)
            val t2 = rng.nextInt(8)
            val u2 = if (requireCarryingInUnits) (10 - u1) + rng.nextInt(10 - (10 - u1)) else rng.nextInt(9 - u1)

            val op1 = (h1 * 100) + (t1 * 10) + u1
            val op2 = (h2 * 100) + (t2 * 10) + u2

            if (op1 in 100..899 && op2 in 100..899 && (op1 + op2) < 1000) {
                val breakdown = decomposeAddition(op1, op2)
                if (!requireCarryingInUnits || breakdown.carryToTens > 0) {
                    return Pair(op1, op2)
                }
            }
        }
    }
}

enum class MisconceptionCategory {
    FORGOT_CARRY_UNITS_TO_TENS,
    DIGIT_REVERSAL_IN_CARRY,
    FORGOT_CARRY_TENS_TO_HUNDREDS,
    GENERAL_CALCULATION_ERROR
}

data class MisconceptionDiagnosis(
    val category: MisconceptionCategory,
    val feedbackMr: String
)
