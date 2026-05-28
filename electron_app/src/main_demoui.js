import Vue from 'vue'

// Catch and suppress ResizeObserver loop limit errors to prevent dev overlay/crashes
const ignoreResizeObserverError = (e) => {
  const message = e.message || (e.reason && e.reason.message);
  if (message && (
    message.includes('ResizeObserver loop limit exceeded') || 
    message.includes('ResizeObserver loop completed with undelivered notifications')
  )) {
    e.stopImmediatePropagation();
    e.preventDefault();
  }
};
window.addEventListener('error', ignoreResizeObserverError);
window.addEventListener('unhandledrejection', ignoreResizeObserverError);

Vue.config.productionTip = false

// setup the vue libs 
import {} from "./init_vue_libs.js"

import AppDemoUI from './AppDemoUI.vue'


new Vue({
  render: h => h(AppDemoUI),
}).$mount('#app')
