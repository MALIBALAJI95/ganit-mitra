package org.ganitmitra.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.ganitmitra.core.domain.model.NumeralSystem
import org.ganitmitra.core.domain.state.LessonStage
import org.ganitmitra.core.domain.state.LessonStateMachine
import org.ganitmitra.ui.components.ChildKeypad
import org.ganitmitra.ui.components.CurrencyPlaceValueManipulative
import org.ganitmitra.ui.theme.*

@Composable
fun LessonScreen(
    stateMachine: LessonStateMachine = remember { LessonStateMachine() },
    modifier: Modifier = Modifier
) {
    val state by stateMachine.uiState.collectAsState()
    var enteredKeypadString by remember { mutableStateOf("") }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("गणित मित्र", fontSize = 18.sp, fontWeight = FontWeight.Bold)
                        Text(
                            text = state.stage.titleMr,
                            fontSize = 11.sp,
                            color = RuralAmberPrimary,
                            fontWeight = FontWeight.SemiBold
                        )
                    }
                },
                actions = {
                    // Airplane Mode & Zero Network Indicator
                    Surface(
                        color = RuralForestEmerald.copy(alpha = 0.12f),
                        shape = RoundedCornerShape(12.dp),
                        modifier = Modifier.padding(end = 6.dp)
                    ) {
                        Text(
                            text = "✈️ ०% Network",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = RuralForestEmerald,
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                        )
                    }

                    // Numeral System Toggle (१ २ ३ vs 1 2 3)
                    Button(
                        onClick = { stateMachine.toggleNumeralSystem() },
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.secondary),
                        shape = RoundedCornerShape(12.dp),
                        contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp),
                        modifier = Modifier.padding(end = 8.dp)
                    ) {
                        Text(
                            text = if (state.numeralSystem == NumeralSystem.DEVANAGARI) "१ २ ३" else "1 2 3",
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            )
        },
        bottomBar = {
            Surface(
                tonalElevation = 4.dp,
                border = androidx.compose.foundation.BorderStroke(1.dp, BorderSubtle),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    if (state.stage != LessonStage.RURAL_HOOK) {
                        OutlinedButton(
                            onClick = { stateMachine.previousStage() },
                            shape = RoundedCornerShape(16.dp),
                            modifier = Modifier
                                .weight(1f)
                                .heightIn(min = 56.dp)
                        ) {
                            Text("मागे", fontSize = 15.sp, fontWeight = FontWeight.Bold)
                        }
                    }

                    Button(
                        onClick = { stateMachine.advanceStage() },
                        colors = ButtonDefaults.buttonColors(containerColor = RuralForestEmerald),
                        shape = RoundedCornerShape(16.dp),
                        modifier = Modifier
                            .weight(2f)
                            .heightIn(min = 56.dp)
                    ) {
                        Text("पुढे चला ➔", fontSize = 16.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
    ) { padding ->
        Column(
            modifier = modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Mascot Speech Box (चिनू खारूताई)
            MascotSpeechCard(mascotText = state.mascotDialogueMr)

            // Stage-Specific Content
            when (state.stage) {
                LessonStage.RURAL_HOOK -> {
                    RuralHookCard(numeralSystem = state.numeralSystem)
                }
                LessonStage.VISUAL_MANIPULATIVE -> {
                    CurrencyPlaceValueManipulative(
                        state = state.manipulativeState,
                        numeralSystem = state.numeralSystem,
                        onRegroupClick = { stateMachine.triggerRegroupingManipulative() }
                    )
                }
                LessonStage.SPOKEN_EXPLANATION, LessonStage.GUIDED_PRACTICE -> {
                    GuidedPracticeCard(
                        hintLevel = state.currentHintLevel,
                        hintText = state.activeHintTextMr,
                        onRequestHint = { stateMachine.requestNextHint() }
                    )
                }
                LessonStage.INDEPENDENT_PRACTICE -> {
                    IndependentPracticeSection(
                        currentInput = enteredKeypadString,
                        feedback = state.feedbackMessageMr,
                        numeralSystem = state.numeralSystem,
                        onDigit = { d -> enteredKeypadString += state.numeralSystem.format(d) },
                        onClear = { enteredKeypadString = "" },
                        onSubmit = {
                            val parsed = enteredKeypadString.toIntOrNull() ?: 0
                            stateMachine.handleNumericAnswer(parsed)
                        }
                    )
                }
                LessonStage.EXPLAIN_BACK_CHECK -> {
                    ExplainBackCard(
                        onSelectOption = { isCorrect ->
                            stateMachine.handleExplainBackOptionSelected(isCorrect)
                        }
                    )
                }
                LessonStage.MASTERY_REVIEW -> {
                    MasteryCompletedCard()
                }
            }
        }
    }
}

@Composable
private fun MascotSpeechCard(mascotText: String) {
    Surface(
        color = RuralAmberContainer.copy(alpha = 0.5f),
        shape = RoundedCornerShape(20.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, RuralAmberPrimary.copy(alpha = 0.3f)),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.padding(14.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Box(
                contentAlignment = Alignment.Center,
                modifier = Modifier
                    .size(48.dp)
                    .background(RuralAmberPrimary, CircleShape)
            ) {
                Text("🐿️", fontSize = 24.sp)
            }
            Column {
                Text(
                    text = "सखी चिनू खारूताई:",
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    color = RuralAmberPrimary
                )
                Text(
                    text = mascotText,
                    fontSize = 14.sp,
                    lineHeight = 20.sp,
                    color = TextDark,
                    fontWeight = FontWeight.Medium
                )
            }
        }
    }
}

@Composable
private fun RuralHookCard(numeralSystem: NumeralSystem) {
    Surface(
        color = MaterialTheme.colorScheme.surface,
        shape = RoundedCornerShape(20.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, BorderSubtle),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.padding(16.dp)
        ) {
            Text("🥬 🎃 🛒", fontSize = 36.sp)
            Spacer(modifier = Modifier.height(8.dp))
            Text("गावचा आठवडी बाजार", fontSize = 16.sp, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = "${numeralSystem.format(147)} + ${numeralSystem.format(235)} = ?",
                fontSize = 24.sp,
                fontWeight = FontWeight.ExtraBold,
                color = RuralForestEmerald
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "बोला 'पुढे' किंवा खालील हिरव्या बटनावर दाबा!",
                fontSize = 12.sp,
                color = TextMuted
            )
        }
    }
}

@Composable
private fun GuidedPracticeCard(
    hintLevel: Int,
    hintText: String?,
    onRequestHint: () -> Unit
) {
    Surface(
        color = MaterialTheme.colorScheme.surface,
        shape = RoundedCornerShape(20.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, BorderSubtle),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = "पायरी-पायरीने मार्गदर्शन (Scaffolded Hints)",
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(8.dp))
            Surface(
                color = Color(0xFFF3E8FF),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    text = hintText ?: "सुगावा हवा असल्यास खालील 'मदत हवी' बटनावर दाबा.",
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Medium,
                    color = Color(0xFF6B21A8),
                    modifier = Modifier.padding(12.dp)
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
            TextButton(
                onClick = onRequestHint,
                modifier = Modifier.align(Alignment.End)
            ) {
                Text("पुढील हिंट (मदत) ➔", fontWeight = FontWeight.Bold)
            }
        }
    }
}

@Composable
private fun IndependentPracticeSection(
    currentInput: String,
    feedback: String?,
    numeralSystem: NumeralSystem,
    onDigit: (Int) -> Unit,
    onClear: () -> Unit,
    onSubmit: () -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Surface(
            color = Color.White,
            shape = RoundedCornerShape(16.dp),
            border = androidx.compose.foundation.BorderStroke(1.dp, BorderSubtle),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                modifier = Modifier.padding(12.dp)
            ) {
                Text("उत्तर द्या (बोला किंवा टॅप करा):", fontSize = 12.sp, color = TextMuted)
                Text(
                    text = currentInput.ifEmpty { "---" },
                    fontSize = 28.sp,
                    fontWeight = FontWeight.ExtraBold,
                    color = TextDark
                )
                if (feedback != null) {
                    Text(
                        text = feedback,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        color = RuralAmberPrimary,
                        textAlign = TextAlign.Center
                    )
                }
            }
        }

        ChildKeypad(
            numeralSystem = numeralSystem,
            onDigitClick = onDigit,
            onClearClick = onClear,
            onSubmitClick = onSubmit
        )
    }
}

@Composable
private fun ExplainBackCard(onSelectOption: (Boolean) -> Unit) {
    Surface(
        color = MaterialTheme.colorScheme.surface,
        shape = RoundedCornerShape(20.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, BorderSubtle),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text("हातचा १ आपण दशकाच्या घरात का नेला?", fontSize = 15.sp, fontWeight = FontWeight.Bold)

            Button(
                onClick = { onSelectOption(true) },
                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.surface),
                shape = RoundedCornerShape(16.dp),
                border = androidx.compose.foundation.BorderStroke(2.dp, RuralForestEmerald),
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 56.dp)
            ) {
                Text(
                    text = "अ. कारण १० सुटी नाणी मिळून १ दशक (₹१०) बनतो. ✓",
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    color = TextDark
                )
            }

            Button(
                onClick = { onSelectOption(false) },
                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.surface),
                shape = RoundedCornerShape(16.dp),
                border = androidx.compose.foundation.BorderStroke(1.dp, BorderSubtle),
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 56.dp)
            ) {
                Text(
                    text = "ब. कारण १ हा सर्वात लहान अंक आहे म्हणून.",
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Medium,
                    color = TextMuted
                )
            }
        }
    }
}

@Composable
private fun MasteryCompletedCard() {
    Surface(
        color = RuralEmeraldContainer.copy(alpha = 0.5f),
        shape = RoundedCornerShape(20.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, RuralForestEmerald.copy(alpha = 0.3f)),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.padding(20.dp)
        ) {
            Text("🏆", fontSize = 48.sp)
            Spacer(modifier = Modifier.height(8.dp))
            Text("अभिनंदन! संकल्पना पूर्ण झाली!", fontSize = 18.sp, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = "तुमची प्रगती स्थानिक रूम डेटाबेस (Room DB) मध्ये सुरक्षित सेव्ह झाली आहे.",
                fontSize = 12.sp,
                textAlign = TextAlign.Center,
                color = TextDark
            )
        }
    }
}
