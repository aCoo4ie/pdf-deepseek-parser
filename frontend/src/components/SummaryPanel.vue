<template>
  <div class="summary-panel">
    <div class="panel-header">
      <h3>摘要总结</h3>
      <div class="actions">
        <button
          class="btn-primary"
          :disabled="loading || !text"
          @click="generateSummary"
        >
          {{ loading ? "生成中..." : summary ? "重新生成" : "生成摘要" }}
        </button>
        <button
          v-if="summary"
          class="btn-secondary"
          @click="copyToClipboard"
        >
          {{ copied ? "已复制" : "复制" }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-bar">
      <div class="loading-bar-inner"></div>
    </div>

    <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

    <div v-if="summary" class="summary-content" v-html="renderedSummary"></div>

    <div v-if="!summary && !loading" class="empty-state">
      <p>点击"生成摘要"按钮，AI 将对论文内容进行结构化总结</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { marked } from "marked";

const props = defineProps({
  text: { type: String, default: "" },
});

const summary = ref("");
const loading = ref(false);
const errorMsg = ref("");
const copied = ref(false);

const renderedSummary = computed(() => {
  return marked.parse(summary.value || "");
});

async function generateSummary() {
  if (!props.text) return;
  loading.value = true;
  errorMsg.value = "";
  summary.value = "";

  try {
    const resp = await fetch("/api/summarize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: props.text }),
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
        if (line.startsWith("event: done")) {
          loading.value = false;
          return;
        }
        if (line.startsWith("event: error")) {
          continue;
        }
        if (line.startsWith("data: ")) {
          const data = line.slice(6);
          if (data === "[DONE]") {
            loading.value = false;
            return;
          }
          summary.value += data;
        }
      }
    }
  } catch (e) {
    errorMsg.value = e.message || "生成摘要失败";
  } finally {
    loading.value = false;
  }
}

async function copyToClipboard() {
  try {
    await navigator.clipboard.writeText(summary.value);
    copied.value = true;
    setTimeout(() => (copied.value = false), 2000);
  } catch {
    errorMsg.value = "复制失败";
  }
}
</script>

<style scoped>
.summary-panel {
  background: var(--color-bg-card);
  border-radius: 12px;
  padding: 24px;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.panel-header h3 {
  margin: 0;
  font-size: 18px;
  color: var(--color-text);
}
.actions {
  display: flex;
  gap: 8px;
}
.summary-content {
  line-height: 1.8;
  color: var(--color-text);
  font-size: 15px;
}
.summary-content :deep(h2) {
  font-size: 17px;
  margin: 20px 0 8px;
  color: var(--color-primary);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 6px;
}
.summary-content :deep(p) {
  margin: 8px 0;
}
.summary-content :deep(ul) {
  padding-left: 20px;
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
.loading-bar {
  height: 3px;
  background: var(--color-border);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 16px;
}
.loading-bar-inner {
  height: 100%;
  width: 30%;
  background: var(--color-primary);
  border-radius: 2px;
  animation: loading-slide 1.2s ease-in-out infinite;
}
@keyframes loading-slide {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(400%); }
}
</style>
