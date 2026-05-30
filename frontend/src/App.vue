<template>
  <div class="app">
    <header class="app-header">
      <div class="header-inner">
        <h1 class="app-title">
          <span class="title-icon">&#128196;</span>
          PDF 论文解析器
        </h1>
        <p class="app-subtitle">上传论文，智能翻译与摘要</p>
      </div>
    </header>

    <main class="app-main">
      <section class="upload-section">
        <FileUpload @parsed="onParsed" />
      </section>

      <section v-if="docData" class="content-section">
        <div class="tabs">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            class="tab-btn"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>

        <div class="tab-content">
          <!-- Original text -->
          <div v-show="activeTab === 'original'" class="original-panel">
            <div class="panel-header">
              <h3>原文内容</h3>
              <span class="page-badge">{{ docData.total_pages }} 页</span>
            </div>
            <div class="original-content">
              <div
                v-for="page in docData.pages"
                :key="page.page"
                class="page-block"
              >
                <div class="page-label">第 {{ page.page }} 页</div>
                <p
                  v-for="(para, idx) in page.paragraphs"
                  :key="idx"
                  class="original-para"
                >
                  {{ para }}
                </p>
              </div>
            </div>
          </div>

          <!-- Summary -->
          <SummaryPanel
            v-show="activeTab === 'summary'"
            :text="docData.full_text"
          />

          <!-- Translate -->
          <TranslatePanel
            v-show="activeTab === 'translate'"
            :paragraphs="docData.paragraphs"
          />
        </div>
      </section>
    </main>

    <footer class="app-footer">
      <p>PDF 论文解析器 &mdash; 本地运行，数据安全</p>
    </footer>
  </div>
</template>

<script setup>
import { ref } from "vue";
import FileUpload from "./components/FileUpload.vue";
import SummaryPanel from "./components/SummaryPanel.vue";
import TranslatePanel from "./components/TranslatePanel.vue";

const docData = ref(null);
const activeTab = ref("original");

const tabs = [
  { key: "original", label: "原文" },
  { key: "summary", label: "摘要总结" },
  { key: "translate", label: "中英翻译" },
];

function onParsed(data) {
  docData.value = data;
  if (data) {
    activeTab.value = "original";
  }
}
</script>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
  color: white;
  padding: 32px 20px;
  text-align: center;
}
.header-inner {
  max-width: 800px;
  margin: 0 auto;
}
.app-title {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
}
.title-icon {
  margin-right: 8px;
}
.app-subtitle {
  margin: 8px 0 0;
  font-size: 15px;
  opacity: 0.85;
}

.app-main {
  flex: 1;
  max-width: 960px;
  width: 100%;
  margin: 0 auto;
  padding: 24px 16px;
}

.upload-section {
  margin-bottom: 24px;
}

.content-section {
  animation: fadeIn 0.3s ease;
}

.tabs {
  display: flex;
  gap: 4px;
  border-bottom: 2px solid var(--color-border);
  margin-bottom: 20px;
}
.tab-btn {
  padding: 10px 20px;
  border: none;
  background: none;
  font-size: 15px;
  color: var(--color-text-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s;
  font-weight: 500;
}
.tab-btn:hover {
  color: var(--color-primary);
}
.tab-btn.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

.original-panel {
  background: var(--color-bg-card);
  border-radius: 12px;
  padding: 24px;
}
.original-panel .panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.original-panel .panel-header h3 {
  margin: 0;
  font-size: 18px;
}
.page-badge {
  background: var(--color-primary-light);
  color: var(--color-primary);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}
.page-block {
  margin-bottom: 24px;
}
.page-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-muted);
  margin-bottom: 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--color-border);
}
.original-para {
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-text);
  margin: 8px 0;
}
.original-content {
  max-height: 600px;
  overflow-y: auto;
}

.app-footer {
  text-align: center;
  padding: 20px;
  color: var(--color-text-muted);
  font-size: 13px;
  border-top: 1px solid var(--color-border);
  margin-top: 40px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
