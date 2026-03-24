export function useDemoMode() {
  const isDemoMode = import.meta.env.VITE_DEMO_MODE === 'true'
  return { isDemoMode }
}
