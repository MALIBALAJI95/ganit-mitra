package org.ganitmitra.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.ganitmitra.core.domain.model.NumeralSystem
import org.ganitmitra.ui.theme.RuralCarryRed
import org.ganitmitra.ui.theme.RuralForestEmerald
import org.ganitmitra.ui.theme.TextDark

/**
 * Big, accessible numeric keypad adhering to >= 56dp touch target rules.
 * Supports instant Devanagari (१ २ ३) vs Western (1 2 3) toggle.
 */
@Composable
fun ChildKeypad(
    numeralSystem: NumeralSystem,
    onDigitClick: (Int) -> Unit,
    onClearClick: () -> Unit,
    onSubmitClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val digits = listOf(
        listOf(1, 2, 3),
        listOf(4, 5, 6),
        listOf(7, 8, 9)
    )

    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        digits.forEach { row ->
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                row.forEach { d ->
                    KeypadButton(
                        text = numeralSystem.format(d),
                        onClick = { onDigitClick(d) },
                        modifier = Modifier.weight(1f)
                    )
                }
            }
        }

        // Bottom row: Clear, 0, Submit
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Button(
                onClick = onClearClick,
                colors = ButtonDefaults.buttonColors(
                    containerColor = RuralCarryRed.copy(alpha = 0.12f),
                    contentColor = RuralCarryRed
                ),
                shape = RoundedCornerShape(16.dp),
                modifier = Modifier
                    .weight(1f)
                    .heightIn(min = 56.dp)
            ) {
                Text("हटवा", fontSize = 16.sp, fontWeight = FontWeight.Bold)
            }

            KeypadButton(
                text = numeralSystem.format(0),
                onClick = { onDigitClick(0) },
                modifier = Modifier.weight(1f)
            )

            Button(
                onClick = onSubmitClick,
                colors = ButtonDefaults.buttonColors(containerColor = RuralForestEmerald),
                shape = RoundedCornerShape(16.dp),
                modifier = Modifier
                    .weight(1f)
                    .heightIn(min = 56.dp)
            ) {
                Text("तपासा ✓", fontSize = 15.sp, fontWeight = FontWeight.Bold)
            }
        }
    }
}

@Composable
private fun KeypadButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    ElevatedButton(
        onClick = onClick,
        colors = ButtonDefaults.elevatedButtonColors(
            containerColor = MaterialTheme.colorScheme.surface,
            contentColor = TextDark
        ),
        shape = RoundedCornerShape(16.dp),
        elevation = ButtonDefaults.elevatedButtonElevation(defaultElevation = 2.dp),
        modifier = modifier.heightIn(min = 56.dp)
    ) {
        Text(text = text, fontSize = 24.sp, fontWeight = FontWeight.ExtraBold)
    }
}
