package org.ganitmitra.ui.components

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.ganitmitra.core.domain.model.NumeralSystem
import org.ganitmitra.core.domain.state.ManipulativeState
import org.ganitmitra.ui.theme.*

/**
 * Visual place-value manipulative for Class 3 addition.
 * Features 3 columns: शतक (₹100), दशक (₹10), एकक (₹1) with animated carrying.
 */
@Composable
fun CurrencyPlaceValueManipulative(
    state: ManipulativeState,
    numeralSystem: NumeralSystem,
    onRegroupClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .background(Color(0xFFF8FAFC), RoundedCornerShape(20.dp))
            .border(1.dp, BorderSubtle, RoundedCornerShape(20.dp))
            .padding(12.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Hundreds Column (शतक)
            PlaceValueColumn(
                title = "शतक (₹१००)",
                count = state.hundreds,
                numeralSystem = numeralSystem,
                accentColor = RuralAmberPrimary,
                modifier = Modifier.weight(1f)
            ) {
                repeat(state.hundreds.coerceAtMost(5)) {
                    NoteBox(label = "१००", color = RuralCoinGold)
                }
            }

            // Tens Column (दशक)
            PlaceValueColumn(
                title = "दशक (₹१०)",
                count = state.tens,
                numeralSystem = numeralSystem,
                accentColor = RuralSkyBlue,
                carryBadge = state.carryBadgeVisible,
                modifier = Modifier.weight(1f)
            ) {
                repeat(state.tens.coerceAtMost(8)) {
                    NoteBox(label = "१०", color = RuralSkyBlue)
                }
            }

            // Units Column (एकक)
            PlaceValueColumn(
                title = "एकक (₹१)",
                count = state.units,
                numeralSystem = numeralSystem,
                accentColor = RuralForestEmerald,
                modifier = Modifier.weight(1f)
            ) {
                repeat(state.units.coerceAtMost(12)) {
                    CoinCircle(label = "१")
                }
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        if (!state.isRegrouped) {
            Button(
                onClick = onRegroupClick,
                colors = ButtonDefaults.buttonColors(containerColor = RuralCoinGold),
                shape = RoundedCornerShape(16.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 56.dp)
            ) {
                Text(
                    text = "✨ १० नाण्यांचा १ दशक हातचा करा",
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF451A03)
                )
            }
        } else {
            Surface(
                color = RuralForestEmerald.copy(alpha = 0.12f),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    text = "✓ १० नाणी एकत्र बांधून १ दशक हातचा नेला! उरले २ एकक.",
                    color = RuralForestEmerald,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.padding(10.dp)
                )
            }
        }
    }
}

@Composable
private fun PlaceValueColumn(
    title: String,
    count: Int,
    numeralSystem: NumeralSystem,
    accentColor: Color,
    carryBadge: Boolean = false,
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.() -> Unit
) {
    Surface(
        color = Color.White,
        shape = RoundedCornerShape(16.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, accentColor.copy(alpha = 0.3f)),
        modifier = modifier
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.padding(8.dp)
        ) {
            Text(title, fontSize = 11.sp, fontWeight = FontWeight.Bold, color = accentColor)
            Text(
                text = numeralSystem.format(count),
                fontSize = 20.sp,
                fontWeight = FontWeight.ExtraBold,
                color = accentColor
            )

            if (carryBadge) {
                Text(
                    text = "हातचा +१",
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White,
                    modifier = Modifier
                        .background(RuralCarryRed, RoundedCornerShape(8.dp))
                        .padding(horizontal = 6.dp, vertical = 2.dp)
                )
            }

            Spacer(modifier = Modifier.height(6.dp))
            Column(
                verticalArrangement = Arrangement.spacedBy(4.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                modifier = Modifier.heightIn(min = 90.dp),
                content = content
            )
        }
    }
}

@Composable
private fun NoteBox(label: String, color: Color) {
    Box(
        contentAlignment = Alignment.Center,
        modifier = Modifier
            .width(44.dp)
            .height(20.dp)
            .background(color, RoundedCornerShape(4.dp))
    ) {
        Text(label, fontSize = 9.sp, fontWeight = FontWeight.ExtraBold, color = Color.White)
    }
}

@Composable
private fun CoinCircle(label: String) {
    Box(
        contentAlignment = Alignment.Center,
        modifier = Modifier
            .size(18.dp)
            .background(RuralForestEmerald, CircleShape)
    ) {
        Text(label, fontSize = 9.sp, fontWeight = FontWeight.ExtraBold, color = Color.White)
    }
}
