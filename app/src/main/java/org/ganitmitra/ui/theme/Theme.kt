package org.ganitmitra.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val GanitMitraColorScheme = lightColorScheme(
    primary = RuralForestEmerald,
    onPrimary = RuralOnAmber,
    primaryContainer = RuralEmeraldContainer,
    secondary = RuralSkyBlue,
    onSecondary = RuralOnAmber,
    secondaryContainer = RuralSkyBlueContainer,
    tertiary = RuralAmberPrimary,
    background = BackgroundWarm,
    surface = SurfaceWarm,
    onBackground = TextDark,
    onSurface = TextDark
)

@Composable
fun GanitMitraTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = GanitMitraColorScheme,
        content = content
    )
}
