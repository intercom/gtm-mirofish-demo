import { computed } from 'vue'

const APP_ID = import.meta.env.VITE_INTERCOM_APP_ID || ''

export function useIntercom() {
  const isIntercomEnabled = computed(() => !!APP_ID)

  function install() {
    if (!APP_ID) return
    if (window.Intercom) return

    window.intercomSettings = { app_id: APP_ID }

    const script = document.createElement('script')
    script.async = true
    script.src = `https://widget.intercom.io/widget/${APP_ID}`
    document.head.appendChild(script)

    // Intercom stub so calls before script loads are queued
    window.Intercom = function () {
      window.Intercom.q = window.Intercom.q || []
      window.Intercom.q.push(arguments)
    }
  }

  function boot(attrs = {}) {
    if (!APP_ID) return
    window.Intercom?.('boot', { app_id: APP_ID, ...attrs })
  }

  function update(attrs = {}) {
    if (!APP_ID) return
    window.Intercom?.('update', attrs)
  }

  function show() {
    if (!APP_ID) return
    window.Intercom?.('show')
  }

  function showNewMessage(text = '') {
    if (!APP_ID) return
    window.Intercom?.('showNewMessage', text)
  }

  function shutdown() {
    if (!APP_ID) return
    window.Intercom?.('shutdown')
  }

  return {
    isIntercomEnabled,
    install,
    boot,
    update,
    show,
    showNewMessage,
    shutdown,
  }
}
