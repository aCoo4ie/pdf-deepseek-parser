<template>
  <div class="loading-spinner">
    <div class="spinner"></div>
    <p v-if="text" class="spinner-text">{{ text }}</p>
  </div>
</template>

<script setup>
defineProps({
  text: { type: String, default: "" },
});
</script>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
}
.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
.spinner-text {
  margin-top: 12px;
  color: var(--color-text-muted);
  font-size: 14px;
}
</style>
