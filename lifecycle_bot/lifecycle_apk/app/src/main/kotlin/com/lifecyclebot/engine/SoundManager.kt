package com.lifecyclebot.engine

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioManager
import android.media.MediaPlayer
import android.media.SoundPool
import android.media.ToneGenerator
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.os.Build
import com.lifecyclebot.R

/**
 * SoundManager v2
 *
 * Plays custom sound files for trading events using MediaPlayer.
 * Falls back to ToneGenerator if custom sounds are unavailable.
 *
 * CUSTOM SOUNDS (from res/raw/):
 *   - woohoo.mp3    → BUY events (Homer "Woohoo!")
 *   - awesome.mp3   → BLOCK/SAFETY events (Peter Griffin "Awesome")
 *
 * FALLBACK (ToneGenerator):
 *   - PROFIT SELL   → Ascending ding sequence
 *   - LOSS/STOP     → Descending wail
 *   - MILESTONE     → Escalating tones
 *   - NEW TOKEN     → Short alert ping
 *
 * All sounds respect the device's volume and Do Not Disturb settings.
 */
class SoundManager(private val ctx: Context) {

    private val mainHandler = Handler(Looper.getMainLooper())
    private var enabled = true

    // Audio attributes for media playback
    private val audioAttrs = AudioAttributes.Builder()
        .setUsage(AudioAttributes.USAGE_NOTIFICATION_EVENT)
        .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
        .build()

    // ToneGenerator for simple synthesised tones (fallback)
    private fun makeTone(): ToneGenerator? = try {
        ToneGenerator(AudioManager.STREAM_NOTIFICATION, 85)
    } catch (_: Exception) { null }

    // Vibrator for haptic feedback
    private val vibrator: Vibrator? = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
        (ctx.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager)
            ?.defaultVibrator
    } else {
        @Suppress("DEPRECATION")
        ctx.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
    }

    fun setEnabled(v: Boolean) { enabled = v }

    // ── Custom Sound Playback ─────────────────────────────────────────

    /**
     * Play a custom sound from res/raw/ using MediaPlayer.
     * Falls back to ToneGenerator if the resource doesn't exist.
     */
    private fun playCustomSound(resId: Int, fallbackTone: Int = ToneGenerator.TONE_PROP_ACK) {
        if (!enabled) return
        mainHandler.post {
            try {
                val mp = MediaPlayer.create(ctx, resId)
                if (mp != null) {
                    mp.setAudioAttributes(audioAttrs)
                    mp.setOnCompletionListener { it.release() }
                    mp.setOnErrorListener { player, _, _ -> 
                        player.release()
                        // Fallback to tone on error
                        makeTone()?.startTone(fallbackTone, 200)
                        true 
                    }
                    mp.start()
                } else {
                    // Resource not found — use fallback tone
                    makeTone()?.startTone(fallbackTone, 200)
                }
            } catch (e: Exception) {
                // Any error — use fallback tone
                makeTone()?.startTone(fallbackTone, 200)
            }
        }
    }

    // ── BUY sound (Homer "Woohoo!") ───────────────────────────────────
    fun playBuySound() {
        if (!enabled) return
        try {
            playCustomSound(R.raw.woohoo, ToneGenerator.TONE_PROP_ACK)
        } catch (_: Exception) {
            // R.raw.woohoo not available — use tone fallback
            mainHandler.post {
                makeTone()?.startTone(ToneGenerator.TONE_PROP_ACK, 200)
            }
        }
        vibratePattern(longArrayOf(0, 100, 50, 100))
    }

    // ── BLOCK sound (Peter Griffin "Awesome") ─────────────────────────
    fun playBlockSound() {
        if (!enabled) return
        try {
            playCustomSound(R.raw.awesome, ToneGenerator.TONE_PROP_NACK)
        } catch (_: Exception) {
            // R.raw.awesome not available — use tone fallback
            mainHandler.post {
                makeTone()?.startTone(ToneGenerator.TONE_PROP_NACK, 200)
            }
        }
        vibratePattern(longArrayOf(0, 80, 40, 80))
    }

    // ── Cash register (profitable sell) ──────────────────────────────
    // Classic "cha-ching" — ascending notes then a long ring
    fun playCashRegister() {
        if (!enabled) return
        mainHandler.post {
            playSequence(listOf(
                Pair(ToneGenerator.TONE_PROP_BEEP,  80),
                Pair(ToneGenerator.TONE_PROP_BEEP2, 80),
                Pair(ToneGenerator.TONE_PROP_ACK,   150),
            ), delayMs = 60)
            vibratePattern(longArrayOf(0, 50, 30, 80, 30, 120))
        }
    }

    // Big win bonus sounds — escalating with profit size
    fun playMilestone(gainPct: Double) {
        if (!enabled) return
        mainHandler.post {
            when {
                gainPct >= 200 -> {
                    // 200%+ — triple ding sequence
                    playSequence(listOf(
                        Pair(ToneGenerator.TONE_PROP_BEEP,  100),
                        Pair(ToneGenerator.TONE_PROP_BEEP2, 100),
                        Pair(ToneGenerator.TONE_PROP_ACK,   100),
                        Pair(ToneGenerator.TONE_PROP_BEEP,  200),
                    ), delayMs = 80)
                    vibratePattern(longArrayOf(0, 80, 40, 80, 40, 200))
                }
                gainPct >= 100 -> {
                    // 100%+ — double ding
                    playSequence(listOf(
                        Pair(ToneGenerator.TONE_PROP_BEEP2, 120),
                        Pair(ToneGenerator.TONE_PROP_ACK,   180),
                    ), delayMs = 80)
                    vibratePattern(longArrayOf(0, 60, 40, 120))
                }
                gainPct >= 50 -> {
                    // 50%+ — single high ding
                    makeTone()?.startTone(ToneGenerator.TONE_PROP_ACK, 150)
                    vibratePattern(longArrayOf(0, 80))
                }
            }
        }
    }

    // ── Warning siren (loss / stop loss triggered) ────────────────────
    // Descending wail — two falling notes
    fun playWarningSiren() {
        if (!enabled) return
        mainHandler.post {
            playSequence(listOf(
                Pair(ToneGenerator.TONE_SUP_ERROR,      200),
                Pair(ToneGenerator.TONE_PROP_NACK,      200),
                Pair(ToneGenerator.TONE_SUP_ERROR,      300),
            ), delayMs = 150)
            vibratePattern(longArrayOf(0, 100, 50, 100, 50, 200))
        }
    }

    // ── New token alert (Pump.fun launch detected) ────────────────────
    fun playNewToken() {
        if (!enabled) return
        mainHandler.post {
            makeTone()?.startTone(ToneGenerator.TONE_PROP_BEEP, 120)
            vibratePattern(longArrayOf(0, 40, 20, 40))
        }
    }

    // ── Safety block alert ────────────────────────────────────────────
    fun playSafetyBlock() {
        if (!enabled) return
        // Use custom "awesome" sound for blocks
        playBlockSound()
    }

    // ── Circuit breaker triggered ─────────────────────────────────────
    fun playCircuitBreaker() {
        if (!enabled) return
        mainHandler.post {
            playSequence(listOf(
                Pair(ToneGenerator.TONE_SUP_ERROR,  300),
                Pair(ToneGenerator.TONE_PROP_NACK,  300),
            ), delayMs = 200)
            vibratePattern(longArrayOf(0, 200, 100, 200))
        }
    }

    // ── Helpers ───────────────────────────────────────────────────────

    private fun playSequence(tones: List<Pair<Int, Int>>, delayMs: Long) {
        var offset = 0L
        tones.forEach { (tone, duration) ->
            mainHandler.postDelayed({
                makeTone()?.startTone(tone, duration)
            }, offset)
            offset += duration + delayMs
        }
    }

    private fun vibratePattern(pattern: LongArray) {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator?.vibrate(VibrationEffect.createWaveform(pattern, -1))
            } else {
                @Suppress("DEPRECATION")
                vibrator?.vibrate(pattern, -1)
            }
        } catch (_: Exception) {}
    }
}
