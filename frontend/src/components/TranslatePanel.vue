<template>
  <div class="translate-panel">
    <div class="panel-header">
      <h3>中英翻译</h3>
      <div class="actions">
        <button
          class="btn-primary"
          :disabled="loading || !paragraphs.length"
          @click="startTranslate"
        >
          {{ loading ? "翻译中..." : translated.length ? "重新翻译" : "开始翻译" }}
        </button>
        <div class="mode-switch">
          <button
            class="btn-mode"
            :class="{ active: compareMode }"
            @click="compareMode = true"
          >
            原文对照
          </button>
          <button
            class="btn-mode"
            :class="{ active: !compareMode }"
            @click="compareMode = false"
          >
            纯译文
          </button>
        </div>
        <button
          class="btn-secondary"
          :disabled="!translated.length"
          @click="copyTranslation"
        >
          {{ copied ? "已复制" : "复制译文" }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="progress-info">
      <div class="loading-bar">
        <div
          class="loading-bar-inner"
          :style="{ width: progressPercent + '%' }"
        ></div>
      </div>
      <p class="progress-text">
        正在翻译第 {{ currentIndex + 1 }} / {{ paragraphs.length }} 段
      </p>
    </div>

    <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

    <!-- Compare mode: side by side -->
    <div
      v-if="translated.length && compareMode"
      class="compare-view"
    >
      <div class="view-header">
        <span>原文对照</span>
      </div>
      <div
        v-for="(item, idx) in translated"
        :key="idx"
        class="compare-row"
      >
        <div class="compare-col original">
          <span class="col-label">原文</span>
          <p>{{ item.original }}</p>
        </div>
        <div class="compare-col translated">
          <span class="col-label">译文</span>
          <p>{{ item.translated }}{{ idx === currentIndex && loading ? streamingText : "" }}</p>
        </div>
      </div>
      <!-- Currently streaming paragraph -->
      <div v-if="loading && currentIndex >= translated.length" class="compare-row">
        <div class="compare-col original">
          <span class="col-label">原文</span>
          <p>{{ paragraphs[currentIndex] }}</p>
        </div>
        <div class="compare-col translated">
          <span class="col-label">译文</span>
          <p>{{ streamingText }}<span class="cursor-blink">|</span></p>
        </div>
      </div>
    </div>

    <!-- Pure translation mode -->
    <div
      v-if="translated.length && !compareMode"
      class="pure-view"
    >
      <div class="view-header">
        <span>纯译文</span>
      </div>
      <p v-for="(item, idx) in translated" :key="idx" class="translated-para">
        {{ item.translated }}
      </p>
      <p v-if="loading && currentIndex >= translated.length" class="translated-para streaming">
        {{ streamingText }}<span class="cursor-blink">|</span>
      </p>
    </div>

    <div v-if="!translated.length && !loading" class="empty-state">
      <p>点击"开始翻译"按钮，AI 将逐段翻译论文内容</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

const props = defineProps({
  paragraphs: { type: Array, default: () => [] },
});

const translated = ref([]);
const loading = ref(false);
const compareMode = ref(true);
const errorMsg = ref("");
const copied = ref(false);
const currentIndex = ref(0);
const streamingText = ref("");

const progressPercent = ref(0);

async function startTranslate() {
  if (!props.paragraphs.length) return;
  loading.value = true;
  errorMsg.value = "";
  translated.value = [];
  currentIndex.value = 0;
  streamingText.value = "";
  progressPercent.value = 0;

  try {
    const resp = await fetch("/api/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ paragraphs: props.paragraphs }),
    });

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || "请求失败");
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("event: done") || line.trim() === "") continue;
        if (line.startsWith("data: ")) {
          const raw = line.slice(6);
          if (raw === "[DONE]") {
            loading.value = false;
            return;
          }
          try {
            const evt = JSON.parse(raw);
            if (evt.type === "chunk") {
              currentIndex.value = evt.index;
              streamingText.value += evt.content;
            } else if (evt.type === "paragraph_done") {
              translated.value.push({
                original: evt.original,
                translated: evt.translated,
              });
              streamingText.value = "";
              progressPercent.value = Math.round(
                ((evt.index + 1) / props.paragraphs.length) * 100
              );
            } else if (evt.type === "done") {
              loading.value = false;
              return;
            }
          } catch {
            // skip malformed JSON
          }
        }
      }
    }
  } catch (e) {
    errorMsg.value = e.message || "翻译失败";
  } finally {
    loading.value = false;
  }
}

async function copyTranslation() {
  const text = translated.value.map((t) => t.translated).join("\n\n");
  try {
    await navigator.clipboard.writeText(text);
    copied.value = true;
    setTimeout(() => (copied.value = false), 2000);
  } catch {
    errorMsg.value = "复制失败";
  }
}
</script>

<style scoped>
.translate-panel {
  background: var(--color-bg-card);
  border-radius: 12px;
  padding: 24px;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 8px;
}
.panel-header h3 {
  margin: 0;
  font-size: 18px;
  color: var(--color-text);
}
.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.mode-switch {
  display: flex;
  gap: 0;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
}
.btn-mode {
  padding: 8px 18px;
  border: none;
  border-radius: 0;
  background: white;
  color: var(--color-text-secondary);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  font-family: inherit;
}
.btn-mode:hover {
  background: var(--color-bg-muted);
  color: var(--color-text);
}
.btn-mode.active {
  background: var(--color-primary);
  color: white;
  font-weight: 600;
}

.compare-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.view-header {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}
.compare-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 16px;
}
.compare-col {
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.8;
}
.compare-col.original {
  background: var(--color-bg-muted);
}
.compare-col.translated {
  background: var(--color-primary-light);
}
.col-label {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.compare-col p {
  margin: 0;
  color: var(--color-text);
}

.pure-view {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.translated-para {
  font-size: 15px;
  line-height: 1.8;
  color: var(--color-text);
  margin: 0;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-border);
}

.cursor-blink {
  animation: blink 1s step-end infinite;
  color: var(--color-primary);
}
@keyframes blink {
  50% { opacity: 0; }
}

.progress-info {
  margin-bottom: 16px;
}
.loading-bar {
  height: 4px;
  background: var(--color-border);
  border-radius: 2px;
  overflow: hidden;
}
.loading-bar-inner {
  height: 100%;
  background: var(--color-primary);
  border-radius: 2px;
  transition: width 0.3s ease;
}
.progress-text {
  text-align: center;
  color: var(--color-text-muted);
  font-size: 13px;
  margin-top: 8px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--color-text-muted);
}
.error-msg {
  color: var(--color-danger);
  margin-bottom: 12px;
  font-size: 14px;
}
</style>
