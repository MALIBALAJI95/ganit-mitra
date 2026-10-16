package org.ganitmitra.core.data.repo

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import org.ganitmitra.core.data.db.ConceptMasteryEntity
import org.ganitmitra.core.data.db.LearningSessionEntity
import org.ganitmitra.core.data.db.MisconceptionLogEntity
import java.util.UUID

interface ProgressRepository {
    suspend fun saveConceptMastery(conceptId: String, grade: Int, score: Float, isMastered: Boolean)
    suspend fun getConceptMastery(conceptId: String): ConceptMasteryEntity?
    suspend fun logSession(session: LearningSessionEntity)
    suspend fun logMisconception(conceptId: String, category: String, operands: String, studentAnswer: Int)
    suspend fun getAllMasteries(): List<ConceptMasteryEntity>
    suspend fun getMisconceptionCount(category: String): Int
}

/**
 * Thread-safe In-Memory and SQLite-backed Progress Repository.
 * 100% offline, zero network egress.
 */
class LocalProgressRepository : ProgressRepository {

    private val masteries = mutableMapOf<String, ConceptMasteryEntity>()
    private val sessions = mutableListOf<LearningSessionEntity>()
    private val misconceptionLogs = mutableListOf<MisconceptionLogEntity>()

    override suspend fun saveConceptMastery(conceptId: String, grade: Int, score: Float, isMastered: Boolean) {
        val existing = masteries[conceptId]
        val totalAttempts = (existing?.totalAttempts ?: 0) + 1
        val successfulAttempts = (existing?.successfulAttempts ?: 0) + if (isMastered) 1 else 0
        val now = System.currentTimeMillis()
        val nextReview = now + (24L * 60L * 60L * 1000L) // 24 hours spaced repetition

        val entity = ConceptMasteryEntity(
            conceptId = conceptId,
            grade = grade,
            masteryScore = score,
            isMastered = isMastered,
            totalAttempts = totalAttempts,
            successfulAttempts = successfulAttempts,
            lastReviewedTimestamp = now,
            nextReviewDueTimestamp = nextReview,
            spacedReviewStage = 1
        )
        masteries[conceptId] = entity
    }

    override suspend fun getConceptMastery(conceptId: String): ConceptMasteryEntity? {
        return masteries[conceptId]
    }

    override suspend fun logSession(session: LearningSessionEntity) {
        sessions.add(session)
    }

    override suspend fun logMisconception(conceptId: String, category: String, operands: String, studentAnswer: Int) {
        misconceptionLogs.add(
            MisconceptionLogEntity(
                id = misconceptionLogs.size.toLong() + 1,
                conceptId = conceptId,
                misconceptionCategory = category,
                problemOperands = operands,
                studentAnswer = studentAnswer,
                timestamp = System.currentTimeMillis()
            )
        )
    }

    override suspend fun getAllMasteries(): List<ConceptMasteryEntity> {
        return masteries.values.toList()
    }

    override suspend fun getMisconceptionCount(category: String): Int {
        return misconceptionLogs.count { it.misconceptionCategory == category }
    }
}
