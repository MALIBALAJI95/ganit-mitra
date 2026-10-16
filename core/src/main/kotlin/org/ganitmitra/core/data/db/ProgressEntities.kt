package org.ganitmitra.core.data.db

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Local offline mastery progress for each curriculum concept.
 * Zero data leaves the device.
 */
@Entity(tableName = "concept_mastery")
data class ConceptMasteryEntity(
    @PrimaryKey
    val conceptId: String,
    val grade: Int,
    val masteryScore: Float, // 0.0 to 1.0
    val isMastered: Boolean,
    val totalAttempts: Int,
    val successfulAttempts: Int,
    val lastReviewedTimestamp: Long,
    val nextReviewDueTimestamp: Long,
    val spacedReviewStage: Int // 0, 1 (24h), 2 (72h), 3 (7d)
)

/**
 * Local session history for teacher / parent insight.
 */
@Entity(tableName = "learning_sessions")
data class LearningSessionEntity(
    @PrimaryKey
    val sessionId: String,
    val conceptId: String,
    val startTimestamp: Long,
    val durationSeconds: Int,
    val problemsAttempted: Int,
    val problemsCorrectFirstTry: Int,
    val hintsRequested: Int,
    val voiceInteractionsCount: Int,
    val tapInteractionsCount: Int
)

/**
 * Local misconception log to identify recurring child error patterns.
 */
@Entity(tableName = "misconception_logs")
data class MisconceptionLogEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val conceptId: String,
    val misconceptionCategory: String,
    val problemOperands: String,
    val studentAnswer: Int,
    val timestamp: Long
)
