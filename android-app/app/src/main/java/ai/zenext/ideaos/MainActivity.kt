package ai.zenext.ideaos

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val shared = extractSharedText(intent)
        val text = TextView(this).apply {
            textSize = 18f
            setPadding(48, 72, 48, 48)
            text = if (shared != null) "IdeaOS\n\nReady to save:\n$shared" else "IdeaOS\n\nYour Personal Knowledge OS"
        }
        setContentView(text)
    }

    override fun onNewIntent(intent: Intent) { super.onNewIntent(intent); setIntent(intent) }

    private fun extractSharedText(intent: Intent?): String? {
        if (intent?.action != Intent.ACTION_SEND) return null
        return intent.getStringExtra(Intent.EXTRA_TEXT)
            ?: (intent.getParcelableExtra<Uri>(Intent.EXTRA_STREAM)?.toString())
    }
}
