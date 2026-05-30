<template>
  <div
    class="upload-area"
    :class="{ dragging: isDragging, uploaded: hasFile }"
    @dragover.prevent="onDragOver"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="handleDrop"
    @click="triggerInput"
  >
    <input
      ref="fileInput"
      type="file"
      accept=".pdf"
      class="hidden-input"
      @change="handleFileChange"
    />

    <!-- Uploading state -->
    <div v-if="uploading" class="upload-progress">
      <div class="spinner"></div>
      <p>正在解析 PDF...</p>
    </div>

    <!-- Uploaded: compact bar with preview -->
    <div v-else-if="hasFile" class="upload-done">
      <div class="done-info">
        <span class="icon-check">&#10003;</span>
        <div class="file-meta">
          <p class="filename">{{ fileName }}</p>
          <p class="file-details">{{ totalPages }} 页 &middot; {{ fileSizeStr }}</p>
        </div>
        <button class="btn-reupload" @click.stop="reset">重新上传</button>
      </div>
      <div v-if="firstPageImage" class="preview-thumb">
        <img :src="'data:image/png;base64,' + firstPageImage" alt="第 1 页预览" />
      </div>
    </div>

    <!-- Initial empty state -->
    <div v-else class="upload-hint">
      <span class="icon-upload">&#8679;</span>
      <p>拖拽 PDF 文件到此处，或点击选择文件</p>
      <p class="hint-sub">仅支持 PDF 格式，最大 20MB</p>
    </div>

    <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";

const emit = defineEmits(["parsed"]);

const fileInput = ref(null);
const isDragging = ref(false);
const uploading = ref(false);
const hasFile = ref(false);
const fileName = ref("");
const totalPages = ref(0);
const fileSize = ref(0);
const firstPageImage = ref("");
const errorMsg = ref("");

const fileSizeStr = computed(() => {
  const s = fileSize.value;
  if (s < 1024) return s + " B";
  if (s < 1024 * 1024) return (s / 1024).toFixed(1) + " KB";
  return (s / 1024 / 1024).toFixed(2) + " MB";
});

function onDragOver() {
  if (!hasFile.value) isDragging.value = true;
}

function triggerInput() {
  if (!hasFile.value && !uploading.value) {
    fileInput.value?.click();
  }
}

function reset() {
  hasFile.value = false;
  fileName.value = "";
  totalPages.value = 0;
  fileSize.value = 0;
  firstPageImage.value = "";
  errorMsg.value = "";
  if (fileInput.value) fileInput.value.value = "";
  emit("parsed", null);
}

function handleDrop(e) {
  isDragging.value = false;
  const file = e.dataTransfer?.files?.[0];
  if (file) uploadFile(file);
}

function handleFileChange(e) {
  const file = e.target?.files?.[0];
  if (file) uploadFile(file);
}

async function uploadFile(file) {
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    errorMsg.value = "仅支持 PDF 文件";
    return;
  }
  if (file.size > 20 * 1024 * 1024) {
    errorMsg.value = "文件大小不能超过 20MB";
    return;
  }

  errorMsg.value = "";
  uploading.value = true;

  try {
    const formData = new FormData();
    formData.append("file", file);

    const resp = await fetch("/api/upload", {
      method: "POST",
      body: formData,
    });

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || "上传失败");
    }

    const data = await resp.json();
    hasFile.value = true;
    fileName.value = data.filename;
    totalPages.value = data.total_pages;
    fileSize.value = data.file_size;
    firstPageImage.value = data.first_page_image || "";
    emit("parsed", data);
  } catch (e) {
    errorMsg.value = e.message || "上传失败，请重试";
  } finally {
    uploading.value = false;
  }
}
</script>

<style scoped>
.upload-area {
  border: 2px dashed var(--color-border);
  border-radius: 12px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: var(--color-bg-card);
  padding: 40px 20px;
}
.upload-area:hover:not(.uploaded),
.upload-area.dragging {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}
.upload-area.uploaded {
  border-style: solid;
  border-color: var(--color-border);
  cursor: default;
  padding: 16px 20px;
  text-align: left;
}
.hidden-input {
  display: none;
}

/* --- Empty upload hint --- */
.icon-upload {
  font-size: 48px;
  color: var(--color-text-muted);
  display: block;
  margin-bottom: 8px;
}
.upload-hint p {
  margin: 4px 0;
  color: var(--color-text-secondary);
}
.hint-sub {
  font-size: 13px;
  color: var(--color-text-muted);
}

/* --- Uploading spinner --- */
.upload-progress {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.upload-progress p {
  margin-top: 12px;
  color: var(--color-text-secondary);
}
.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* --- Compact uploaded state --- */
.upload-done {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.done-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}
.icon-check {
  font-size: 28px;
  color: var(--color-success);
  flex-shrink: 0;
}
.file-meta {
  min-width: 0;
}
.filename {
  margin: 0;
  font-weight: 600;
  color: var(--color-text);
  font-size: 15px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.file-details {
  margin: 2px 0 0;
  color: var(--color-text-muted);
  font-size: 13px;
}
.btn-reupload {
  padding: 5px 14px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: white;
  color: var(--color-text-secondary);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
  flex-shrink: 0;
}
.btn-reupload:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

/* --- First-page thumbnail --- */
.preview-thumb {
  flex-shrink: 0;
  width: 80px;
  height: 110px;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid var(--color-border);
  background: #f9f9fb;
}
.preview-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: top;
  display: block;
}

.error-msg {
  color: var(--color-danger);
  margin-top: 12px;
  font-size: 14px;
}
</style>
